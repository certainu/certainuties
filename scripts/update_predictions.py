#!/usr/bin/env python3
"""CERTAINU updater: refreshes Polymarket prices, resolves old calls, and locks selective new calls."""
import json, math, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"/"predictions.json"
GAMMA="https://gamma-api.polymarket.com/markets"
MIN_VOLUME=float(os.getenv("CERTAINU_MIN_VOLUME","25000"))
MIN_EDGE=float(os.getenv("CERTAINU_MIN_EDGE","10"))
MAX_OPEN=int(os.getenv("CERTAINU_MAX_OPEN","5"))
MAX_NEW=int(os.getenv("CERTAINU_MAX_NEW_PER_RUN","1"))
MODEL_VERSION="rules-v1"

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CERTAINU/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)
def arr(v):
    if isinstance(v,list): return v
    if isinstance(v,str):
        try: return json.loads(v)
        except: return []
    return []
def f(v,d=0):
    try:return float(v)
    except:return d

def market_prob(m):
    outcomes=arr(m.get('outcomes')); prices=arr(m.get('outcomePrices'))
    for i,o in enumerate(outcomes):
        if str(o).upper()=='YES' and i<len(prices): return f(prices[i])*100
    return f(m.get('bestAsk') or m.get('lastTradePrice'))*100

def url_for(m):
    slug=m.get('slug') or ''
    return 'https://polymarket.com/event/'+slug if slug else 'https://polymarket.com/'

def model(m, previous_prob=None):
    """Transparent meme-forecast model. It is intentionally conservative and deterministic.
    Uses market baseline + mild momentum + liquidity confidence + mean-reversion at extremes.
    This is not a claim of superior forecasting ability.
    """
    p=market_prob(m); vol=max(0,f(m.get('volume') or m.get('volumeNum')))
    momentum=0 if previous_prob is None else max(-8,min(8,p-previous_prob))
    liquidity=min(1, math.log10(max(vol,10))/6)
    # Small contrarian adjustment at extremes, small momentum adjustment otherwise.
    adjustment=(-6 if p>82 else 6 if p<18 else momentum*0.8)
    # Deterministic question-based tilt prevents exact mirroring while remaining bounded.
    q=str(m.get('question','')); tilt=((sum(map(ord,q))%9)-4)*0.7
    estimate=max(5,min(95,p+adjustment+tilt))
    pick='YES' if estimate>=50 else 'NO'
    confidence=round(estimate if pick=='YES' else 100-estimate)
    market_side=p if pick=='YES' else 100-p
    edge=confidence-market_side
    reason=f"Rules-v1: market baseline {p:.0f}% YES; volume ${vol:,.0f}; momentum {momentum:+.1f} pts; bounded adjustment produced {estimate:.0f}% YES."
    return pick,confidence,edge,reason,p,vol

def main():
    state=json.loads(DATA.read_text()) if DATA.exists() else {"predictions":[]}
    preds=state.setdefault('predictions',[]); byid={str(p['id']):p for p in preds}
    qs=urllib.parse.urlencode({'active':'true','closed':'false','limit':'100','order':'volume','ascending':'false'})
    active=get_json(GAMMA+'?'+qs)
    active_by_id={str(m.get('id')):m for m in active}
    # Refresh open calls.
    for p in preds:
        if p.get('status')!='open': continue
        m=active_by_id.get(str(p['id']))
        if m:
            p['market_probability_current']=round(market_prob(m),2); p['updated_at']=now(); p['volume']=f(m.get('volume') or m.get('volumeNum'))
        else:
            # Fetch exact market; closed markets often disappear from active list.
            try:
                exact=get_json(GAMMA+'?'+urllib.parse.urlencode({'id':p['id']})); m=exact[0] if exact else None
            except Exception: m=None
            if m:
                cur=market_prob(m); p['market_probability_current']=round(cur,2); p['updated_at']=now()
                if m.get('closed') or cur>=99 or cur<=1:
                    result='YES' if cur>=99 else 'NO' if cur<=1 else None
                    if result:
                        p['result']=result; p['status']='won' if result==p['pick'] else 'lost'; p['resolved_at']=now()
    # Select at most MAX_NEW selective calls.
    open_count=sum(p.get('status')=='open' for p in preds); candidates=[]
    if open_count<MAX_OPEN:
        for m in active:
            mid=str(m.get('id')); vol=f(m.get('volume') or m.get('volumeNum'))
            if not mid or mid in byid or vol<MIN_VOLUME: continue
            p0=market_prob(m)
            if p0<=3 or p0>=97: continue
            pick,conf,edge,reason,yesp,vol=model(m)
            if edge>=MIN_EDGE: candidates.append((edge,vol,m,pick,conf,reason,yesp))
        candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
        for edge,vol,m,pick,conf,reason,yesp in candidates[:min(MAX_NEW,MAX_OPEN-open_count)]:
            market_side=yesp if pick=='YES' else 100-yesp
            preds.append({'id':str(m['id']),'slug':m.get('slug'),'question':m.get('question','Untitled market'),'pick':pick,'confidence':conf,'market_probability_at_pick':round(yesp,2),'market_probability_current':round(yesp,2),'edge_at_pick':round(conf-market_side,2),'volume':vol,'locked_at':now(),'updated_at':now(),'status':'open','result':None,'resolved_at':None,'market_url':url_for(m),'reason':reason,'model_version':MODEL_VERSION})
    state['updated_at']=now(); state['model_version']=MODEL_VERSION
    DATA.write_text(json.dumps(state,indent=2,sort_keys=False)+"\n")
    print(f"Updated {len(preds)} predictions; {sum(p.get('status')=='open' for p in preds)} open.")
if __name__=='__main__': main()
