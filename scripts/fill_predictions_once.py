#!/usr/bin/env python3
"""One-time CERTAINU batch filler: add up to 30 new calls with a varied resolution mix."""
import json, math, os, random, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"/"predictions.json"
GAMMA="https://gamma-api.polymarket.com/markets"
ADD_LIMIT=int(os.getenv("CERTAINU_BATCH_ADD","30"));MAX_VISIBLE=int(os.getenv("CERTAINU_MAX_VISIBLE","50"));MIN_VOLUME=float(os.getenv("CERTAINU_MIN_VOLUME","5000"));MIN_EDGE=float(os.getenv("CERTAINU_MIN_EDGE","0"));MODEL_VERSION="rules-v2.3-speed"
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def get_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CERTAINU/2.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def arr(v):
 if isinstance(v,list):return v
 if isinstance(v,str):
  try:return json.loads(v)
  except:return []
 return []
def f(v,d=0):
 try:return float(v)
 except:return d
def yes_prob(m):
 o,p=arr(m.get('outcomes')),arr(m.get('outcomePrices'))
 for i,x in enumerate(o):
  if str(x).upper()=='YES' and i<len(p):return f(p[i])*100
 return f(m.get('bestAsk') or m.get('lastTradePrice'))*100
def num(m,keys):
 for k in keys:
  try:
   if m.get(k) not in (None,''):return float(str(m[k]).replace(',','').replace('$','').strip())
  except:pass
 return 0
def volume(m):return max(0,num(m,('volumeNum','volume','volumeClob','volume24hr','volume1wk','volume1mo','volume1yr')))
def liquidity(m):return max(0,num(m,('liquidityNum','liquidity','liquidityClob')))
def parse_end(m):
 raw=m.get('endDate') or m.get('end_date') or m.get('endDateIso') or m.get('endDateISO')
 if not raw:return None
 try:return datetime.fromisoformat(str(raw).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return None
def bucket(m):
 e=parse_end(m)
 if not e:return 'long',None
 h=(e-datetime.now(timezone.utc)).total_seconds()/3600
 if h<=0:return None,h
 return ('quick' if h<=24 else 'short' if h<=72 else 'week' if h<=168 else 'long'),h
def market_url(m):
 ev=m.get('events') or [];es=str((ev[0] or {}).get('slug') or '') if isinstance(ev,list) and ev else '';slug=es or str(m.get('eventSlug') or m.get('slug') or '')
 return f'https://polymarket.com/event/{slug}' if slug else 'https://polymarket.com/'
def model(m):
 p=yes_prob(m);v=volume(m);l=liquidity(m);vq=min(1,math.log10(max(v,10))/7);lq=min(1,math.log10(max(l,10))/6) if l else vq*.75;q=max(.2,min(1,.65*vq+.35*lq));ext=(-7*q if p>=80 else 7*q if p<=20 else -3.5*q if p>=68 else 3.5*q if p<=32 else 0);center=abs(p-50)/50;conv=(5.2+2.8*q)*(.55+.45*center);est=max(5,min(95,p+ext+(1 if p>=50 else -1)*conv));pick='YES' if est>=50 else 'NO';conf=round(est if pick=='YES' else 100-est);side=p if pick=='YES' else 100-p;edge=conf-side;reason=f'Rules-v2: market {p:.1f}% YES; volume ${v:,.0f}; liquidity ${l:,.0f}; quality {q:.2f}; model {est:.1f}% YES.';return pick,conf,edge,reason,p,v,l
def main():
 state=json.loads(DATA.read_text()) if DATA.exists() else {'predictions':[]};preds=state.setdefault('predictions',[]);existing={str(p.get('id')) for p in preds if p.get('id') is not None};retired={str(x) for x in state.setdefault('retired_market_ids',[])};room=max(0,MAX_VISIBLE-len(preds));to_add=min(ADD_LIMIT,room)
 if to_add<=0:print(f'[batch] no room: visible={len(preds)} cap={MAX_VISIBLE}');return
 # Gamma rejects very large offsets with 422. Pull the current active universe in supported pages only.
 active=[];seen=set()
 for offset in range(0,1000,100):
  qs=urllib.parse.urlencode({'active':'true','closed':'false','limit':'100','offset':offset})
  try:page=get_json(GAMMA+'?'+qs)
  except Exception as e:
   print(f'[batch] stopping pagination at offset={offset}: {e}');break
  if not page:break
  for m in page:
   mid=str(m.get('id') or '')
   if mid and mid not in seen:seen.add(mid);active.append(m)
  if len(page)<100:break
 pools={k:[] for k in ('quick','short','week','long')}
 for m in active:
  mid=str(m.get('id') or '');v=volume(m);l=liquidity(m);p=yes_prob(m);b,h=bucket(m)
  if not mid or mid in existing or mid in retired or not b or not(v>=MIN_VOLUME or(v==0 and l>=MIN_VOLUME)) or p<=3 or p>=97:continue
  pick,conf,edge,reason,yesp,v,l=model(m)
  if edge<MIN_EDGE:continue
  quality=min(2,math.log10(max(v,1))/4)+min(1.5,math.log10(max(l,1))/4 if l else 0);uncertainty=2 if 10<=p<=90 else -2;pools[b].append((edge+uncertainty+quality,edge,v,m,pick,conf,reason,yesp,l,h))
 for x in pools.values():x.sort(key=lambda z:(z[0],z[1],z[2]),reverse=True)
 weights={'quick':random.uniform(.25,.35),'short':random.uniform(.25,.35),'week':random.uniform(.20,.30),'long':random.uniform(.10,.20)};chosen=[];counts={k:0 for k in pools}
 while len(chosen)<to_add:
  available=[k for k in pools if pools[k]]
  if not available:break
  tw=sum(weights[k] for k in available);progress=max(1,len(chosen)+1);b=max(available,key=lambda k:((weights[k]/tw)*progress-counts[k],pools[k][0][0]+random.random()*.35));chosen.append((b,pools[b].pop(0)));counts[b]+=1
 for b,item in chosen:
  score,edge,v,m,pick,conf,reason,yesp,l,h=item;side=yesp if pick=='YES' else 100-yesp;e=parse_end(m);preds.append({'id':str(m['id']),'slug':m.get('slug'),'question':m.get('question','Untitled market'),'pick':pick,'confidence':conf,'market_probability_at_pick':round(yesp,2),'market_probability_current':round(yesp,2),'edge_at_pick':round(conf-side,2),'selection_score':round(score,2),'hours_to_resolution_at_pick':round(h,1) if h is not None else None,'market_end_date':e.isoformat().replace('+00:00','Z') if e else None,'volume':v,'liquidity':l,'locked_at':now(),'updated_at':now(),'status':'open','result':None,'resolved_at':None,'market_url':market_url(m),'reason':reason,'model_version':MODEL_VERSION,'seeded_demo':False})
 state['updated_at']=now();state['model_version']=MODEL_VERSION;DATA.write_text(json.dumps(state,indent=2)+'\n');print(f'[batch] markets_scanned={len(active)} requested={ADD_LIMIT} room={room} created={len(chosen)} mix={counts} visible={len(preds)}')
if __name__=='__main__':main()
