#!/usr/bin/env python3
"""One-time helper: append exactly 3 real Polymarket calls resolving within 24h.

Broader search than the normal updater. It scans active markets in several sort orders,
then progressively relaxes only the one-time liquidity/probability/edge filters until
3 legitimate <=24h markets are found. It does NOT modify the hourly updater.
"""
import json, math, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'predictions.json'
GAMMA='https://gamma-api.polymarket.com/markets'
MARKER='manual_three_quick_predictions_2026_10_05'
COUNT=3

def now_dt(): return datetime.now(timezone.utc)
def now(): return now_dt().isoformat().replace('+00:00','Z')
def get_json(url):
 req=urllib.request.Request(url,headers={'User-Agent':'CERTAINU/2.1','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def arr(v):
 if isinstance(v,list):return v
 if isinstance(v,str):
  try:return json.loads(v)
  except:return []
 return []
def f(v,d=0.0):
 try:return float(v)
 except:return d
def yes_prob(m):
 o,p=arr(m.get('outcomes')),arr(m.get('outcomePrices'))
 for i,x in enumerate(o):
  if str(x).upper()=='YES' and i<len(p):return f(p[i])*100
 return f(m.get('bestAsk') or m.get('lastTradePrice'))*100
def num(m,keys):
 for k in keys:
  v=m.get(k)
  if v in(None,''):continue
  try:return float(str(v).replace(',','').replace('$','').strip())
  except:pass
 return 0.0
def volume(m):return max(0,num(m,('volumeNum','volume','volumeClob','volume24hr','volume1wk','volume1mo','volume1yr')))
def liquidity(m):return max(0,num(m,('liquidityNum','liquidity','liquidityClob')))
def parse_end(m):
 raw=m.get('endDate') or m.get('end_date') or m.get('endDateIso') or m.get('endDateISO')
 if not raw:return None
 try:return datetime.fromisoformat(str(raw).replace('Z','+00:00')).astimezone(timezone.utc)
 except:return None
def hours_left(m):
 e=parse_end(m);return (e-now_dt()).total_seconds()/3600 if e else None
def crypto_market(x):
 text=' '.join(str(x.get(k) or '') for k in ('question','slug','eventSlug','description')).lower();ev=x.get('events') or []
 if isinstance(ev,list):text+=' '+' '.join(str((e or {}).get(k) or '') for e in ev for k in ('title','slug','description'))
 return any(t in text for t in ('bitcoin',' btc','btc ','ethereum',' eth','eth ','solana',' sol','sol ','crypto','cryptocurrency','dogecoin',' doge','xrp','ripple','cardano',' ada','chainlink','bnb','avalanche','avax','sui','memecoin','meme coin'))
def topic(m):
 text=' '.join(str(m.get(k) or '') for k in ('question','slug','eventSlug','description')).lower()
 if crypto_market(m):return 'crypto'
 if any(x in text for x in ('nba','nfl','mlb','nhl','soccer','football','basketball','baseball','tennis','ufc','game','match','championship','world cup')):return 'sports'
 if any(x in text for x in ('trump','democrat','republican','election','president','senate','congress','prime minister','government','strike','war','israel','ukraine','russia','china')):return 'politics'
 return 'other'
def market_url(m):
 ev=m.get('events') or [];es=str((ev[0] or {}).get('slug') or '') if isinstance(ev,list) and ev else '';slug=es or str(m.get('eventSlug') or m.get('slug') or '')
 return f'https://polymarket.com/event/{slug}' if slug else 'https://polymarket.com/'
def model(m):
 p=yes_prob(m);v=volume(m);l=liquidity(m);vq=min(1,math.log10(max(v,10))/7);lq=min(1,math.log10(max(l,10))/6) if l else vq*.75;q=max(.2,min(1,.65*vq+.35*lq));ext=(-7*q if p>=80 else 7*q if p<=20 else -3.5*q if p>=68 else 3.5*q if p<=32 else 0);center=abs(p-50)/50;conv=(5.2+2.8*q)*(.55+.45*center);est=max(5,min(95,p+ext+(1 if p>=50 else -1)*conv));pick='YES' if est>=50 else 'NO';conf=round(est if pick=='YES' else 100-est);side=p if pick=='YES' else 100-p;edge=conf-side;reason=f'Rules-v2: market {p:.1f}% YES; volume ${v:,.0f}; liquidity ${l:,.0f}; quality {q:.2f}; model {est:.1f}% YES.';return pick,conf,edge,reason,p,v,l

def scan_active():
 # Scan substantially deeper than the regular updater. Multiple query orders reduce
 # the chance that short-duration markets are buried behind long-term markets.
 found={}
 variants=[{}, {'order':'endDate','ascending':'true'}, {'order':'volume24hr','ascending':'false'}, {'order':'liquidity','ascending':'false'}]
 for extra in variants:
  for offset in range(0,5000,100):
   qs={'active':'true','closed':'false','limit':'100','offset':offset};qs.update(extra)
   try:page=get_json(GAMMA+'?'+urllib.parse.urlencode(qs))
   except Exception as e:
    print(f'[scan] query {extra or "default"} stopped at {offset}: {e}');break
   if not page:break
   for m in page:
    mid=str(m.get('id') or '')
    if mid:found[mid]=m
   if len(page)<100:break
 return list(found.values())

def build_candidates(active,existing,retired,min_activity,prob_floor,require_edge):
 out=[]
 for m in active:
  mid=str(m.get('id') or '')
  if not mid or mid in existing or mid in retired:continue
  h=hours_left(m)
  if h is None or h<=0 or h>24:continue
  v,l=volume(m),liquidity(m)
  if max(v,l)<min_activity:continue
  p=yes_prob(m)
  if p<=prob_floor or p>=100-prob_floor:continue
  pick,conf,edge,reason,yesp,v,l=model(m)
  if require_edge and edge<0:continue
  quality=min(2,math.log10(max(v,1))/4)+min(1.5,math.log10(max(l,1))/4 if l else 0)
  score=edge+30+(2 if 10<=p<=90 else -2)+quality+(6 if crypto_market(m) else 0)
  out.append((score,v,h,m,pick,conf,edge,reason,yesp,l,topic(m)))
 return sorted(out,key=lambda x:(x[0],x[1]),reverse=True)

def choose(candidates):
 chosen=[];used_topics=set()
 for c in candidates:
  if c[-1] not in used_topics:
   chosen.append(c);used_topics.add(c[-1])
   if len(chosen)==COUNT:return chosen
 ids={str(c[3].get('id')) for c in chosen}
 for c in candidates:
  if str(c[3].get('id')) in ids:continue
  chosen.append(c)
  if len(chosen)==COUNT:break
 return chosen

def main():
 state=json.loads(DATA.read_text(encoding='utf-8'))
 if state.get(MARKER):raise SystemExit('Already completed: this one-time script will not add another 3 predictions.')
 preds=state.setdefault('predictions',[]);existing={str(p.get('id')) for p in preds if p.get('id') is not None};retired={str(x) for x in state.get('retired_market_ids',[])};open_count=sum(str(p.get('status','')).lower()=='open' for p in preds if not p.get('seeded_demo',False))
 if open_count+COUNT>100:raise SystemExit(f'Refusing to exceed 100 live calls: currently {open_count} open.')
 active=scan_active();quick=[m for m in active if (hours_left(m) is not None and 0<hours_left(m)<=24)]
 print(f'[scan] unique active={len(active)}; <=24h={len(quick)}')
 # Progressive one-time fallback. We still require real active <=24h markets and
 # nonzero market probability, but widen activity and probability requirements.
 tiers=[(5000,3,True),(1000,2,True),(250,1,True),(50,0.5,False),(0,0.1,False)]
 chosen=[];used_tier=None
 for min_activity,prob_floor,require_edge in tiers:
  candidates=build_candidates(active,existing,retired,min_activity,prob_floor,require_edge)
  print(f'[tier] activity>={min_activity:g}, probability={prob_floor:g}-{100-prob_floor:g}, edge_required={require_edge}: {len(candidates)} candidates')
  if len(candidates)>=COUNT:
   chosen=choose(candidates);used_tier=(min_activity,prob_floor,require_edge);break
 if len(chosen)<COUNT:raise SystemExit(f'Found only {len(chosen)} usable <=24h markets even after broad fallback; nothing was changed.')
 stamp=now()
 for score,v,h,m,pick,conf,edge,reason,yesp,l,cat in chosen:
  e=parse_end(m);preds.append({'id':str(m['id']),'slug':m.get('slug'),'question':m.get('question','Untitled market'),'pick':pick,'confidence':conf,'market_probability_at_pick':round(yesp,2),'market_probability_current':round(yesp,2),'edge_at_pick':round(edge,2),'selection_score':round(score,2),'hours_to_resolution_at_pick':round(h,1),'market_end_date':e.isoformat().replace('+00:00','Z'),'volume':v,'liquidity':l,'locked_at':stamp,'updated_at':stamp,'status':'open','result':None,'resolved_at':None,'market_url':market_url(m),'reason':reason,'model_version':'rules-v2-one-time-quick-broad','category':cat,'seeded_demo':False})
 state[MARKER]={'completed_at':stamp,'count':COUNT,'market_ids':[str(c[3]['id']) for c in chosen],'selection_tier':{'min_activity':used_tier[0],'probability_floor':used_tier[1],'edge_required':used_tier[2]}};state['updated_at']=stamp;DATA.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
 print('Added exactly 3 one-time <=24h CERTAINU predictions:')
 for c in chosen:print(f" - [{c[-1]}] {c[3].get('question')} ({c[2]:.1f}h left; volume ${c[1]:,.0f}; liquidity ${c[9]:,.0f})")
 print('Done. This script is now locked against running again on this predictions file.')
if __name__=='__main__':main()
