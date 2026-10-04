#!/usr/bin/env python3
"""One-time CERTAINU batch filler: add up to 30 new calls with a varied resolution mix."""
import json, math, os, random, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"/"predictions.json"
GAMMA="https://gamma-api.polymarket.com/markets"
ADD_LIMIT=int(os.getenv("CERTAINU_BATCH_ADD","30"))
MAX_VISIBLE=int(os.getenv("CERTAINU_MAX_VISIBLE","50"))
MIN_VOLUME=float(os.getenv("CERTAINU_MIN_VOLUME","5000"))
MIN_EDGE=float(os.getenv("CERTAINU_MIN_EDGE","0"))
MODEL_VERSION="rules-v2.3-speed"

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':'CERTAINU/2.0'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def arr(v):
    if isinstance(v,list):return v
    if isinstance(v,str):
        try:return json.loads(v)
        except Exception:return []
    return []
def f(v,d=0.0):
    try:return float(v)
    except Exception:return d
def yes_prob(m):
    outcomes,prices=arr(m.get('outcomes')),arr(m.get('outcomePrices'))
    for i,o in enumerate(outcomes):
        if str(o).upper()=='YES' and i<len(prices):return f(prices[i])*100
    return f(m.get('bestAsk') or m.get('lastTradePrice'))*100
def num(m,keys):
    for k in keys:
        v=m.get(k)
        if v in (None,''):continue
        try:return float(str(v).replace(',','').replace('$','').strip())
        except Exception:pass
    return 0.0
def volume(m):return max(0,num(m,('volumeNum','volume','volumeClob','volume24hr','volume1wk','volume1mo','volume1yr')))
def liquidity(m):return max(0,num(m,('liquidityNum','liquidity','liquidityClob')))
def parse_end(m):
    raw=m.get('endDate') or m.get('end_date') or m.get('endDateIso') or m.get('endDateISO')
    if not raw:return None
    try:return datetime.fromisoformat(str(raw).replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception:return None
def bucket(m):
    e=parse_end(m)
    if not e:return 'long',None
    h=(e-datetime.now(timezone.utc)).total_seconds()/3600
    if h<=0:return None,h
    if h<=24:return 'quick',h
    if h<=72:return 'short',h
    if h<=168:return 'week',h
    return 'long',h
def market_url(m):
    events=m.get('events') or []
    es=str((events[0] or {}).get('slug') or '') if isinstance(events,list) and events else ''
    slug=es or str(m.get('eventSlug') or m.get('slug') or '')
    return f'https://polymarket.com/event/{slug}' if slug else 'https://polymarket.com/'
def model(m):
    p=yes_prob(m);v=volume(m);l=liquidity(m)
    vq=min(1,math.log10(max(v,10))/7);lq=min(1,math.log10(max(l,10))/6) if l else vq*.75
    q=max(.2,min(1,.65*vq+.35*lq));ext=0
    if p>=80:ext=-7*q
    elif p<=20:ext=7*q
    elif p>=68:ext=-3.5*q
    elif p<=32:ext=3.5*q
    center=abs(p-50)/50;conv=(5.2+2.8*q)*(.55+.45*center);direction=1 if p>=50 else -1
    est=max(5,min(95,p+ext+direction*conv));pick='YES' if est>=50 else 'NO';conf=round(est if pick=='YES' else 100-est);side=p if pick=='YES' else 100-p;edge=conf-side
    reason=f'Rules-v2: market {p:.1f}% YES; volume ${v:,.0f}; liquidity ${l:,.0f}; quality {q:.2f}; model {est:.1f}% YES.'
    return pick,conf,edge,reason,p,v,l

def main():
    state=json.loads(DATA.read_text()) if DATA.exists() else {'predictions':[]};preds=state.setdefault('predictions',[])
    existing={str(p.get('id')) for p in preds if p.get('id') is not None};retired={str(x) for x in state.setdefault('retired_market_ids',[])}
    room=max(0,MAX_VISIBLE-len(preds));to_add=min(ADD_LIMIT,room)
    if to_add<=0:
        print(f'[batch] no room: visible={len(preds)} cap={MAX_VISIBLE}');return
    active=[];seen=set()
    for offset in range(0,3000,100):
        qs=urllib.parse.urlencode({'active':'true','closed':'false','limit':'100','offset':str(offset)});page=get_json(GAMMA+'?'+qs)
        if not page:break
        for m in page:
            mid=str(m.get('id') or '')
            if mid and mid not in seen:seen.add(mid);active.append(m)
        if len(page)<100:break
    pools={k:[] for k in ('quick','short','week','long')}
    for m in active:
        mid=str(m.get('id') or '');v=volume(m);l=liquidity(m);p=yes_prob(m);b,h=bucket(m)
        if not mid or mid in existing or mid in retired or not b:continue
        if not (v>=MIN_VOLUME or (v==0 and l>=MIN_VOLUME)):continue
        if p<=3 or p>=97:continue
        pick,conf,edge,reason,yesp,v,l=model(m)
        if edge<MIN_EDGE:continue
        uncertainty=2 if 10<=p<=90 else -2;quality=min(2,math.log10(max(v,1))/4)+min(1.5,math.log10(max(l,1))/4 if l else 0)
        pools[b].append((edge+uncertainty+quality,edge,v,m,pick,conf,reason,yesp,l,h))
    for p in pools.values():p.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    # Randomized weights create a balanced-but-not-identical split each one-time run.
    weights={'quick':random.uniform(.25,.35),'short':random.uniform(.25,.35),'week':random.uniform(.20,.30),'long':random.uniform(.10,.20)}
    chosen=[];counts={k:0 for k in pools}
    while len(chosen)<to_add:
        available=[k for k in pools if pools[k]]
        if not available:break
        # Prefer categories below their randomized share, but never force a category with no good candidates.
        totalw=sum(weights[k] for k in available);progress=max(1,len(chosen)+1)
        def need(k):return (weights[k]/totalw)*progress-counts[k]
        b=max(available,key=lambda k:(need(k),pools[k][0][0]+random.random()*.35))
        item=pools[b].pop(0);chosen.append((b,item));counts[b]+=1
    for b,item in chosen:
        score,edge,v,m,pick,conf,reason,yesp,l,h=item;side=yesp if pick=='YES' else 100-yesp;e=parse_end(m)
        preds.append({'id':str(m['id']),'slug':m.get('slug'),'question':m.get('question','Untitled market'),'pick':pick,'confidence':conf,'market_probability_at_pick':round(yesp,2),'market_probability_current':round(yesp,2),'edge_at_pick':round(conf-side,2),'selection_score':round(score,2),'hours_to_resolution_at_pick':round(h,1) if h is not None else None,'market_end_date':e.isoformat().replace('+00:00','Z') if e else None,'volume':v,'liquidity':l,'locked_at':now(),'updated_at':now(),'status':'open','result':None,'resolved_at':None,'market_url':market_url(m),'reason':reason,'model_version':MODEL_VERSION,'seeded_demo':False})
    state['updated_at']=now();state['model_version']=MODEL_VERSION
    DATA.write_text(json.dumps(state,indent=2)+'\n')
    print(f'[batch] requested={ADD_LIMIT} room={room} created={len(chosen)} mix={counts} visible={len(preds)}')

if __name__=='__main__':main()
