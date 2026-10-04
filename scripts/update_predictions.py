#!/usr/bin/env python3
"""CERTAINU updater with short-term preference, long-term cap, and moderate crypto tilt."""
import json, math, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]/"data"/"predictions.json";GAMMA="https://gamma-api.polymarket.com/markets"
MIN_VOLUME=float(os.getenv("CERTAINU_MIN_VOLUME","5000"));MIN_EDGE=float(os.getenv("CERTAINU_MIN_EDGE","0"));MAX_OPEN=int(os.getenv("CERTAINU_MAX_OPEN","100"));MAX_RESOLVED=int(os.getenv("CERTAINU_MAX_RESOLVED","1000"));MAX_NEW=int(os.getenv("CERTAINU_MAX_NEW_PER_RUN","1"));MAX_LONG_OPEN=int(os.getenv("CERTAINU_MAX_LONG_OPEN","6"));MAX_CRYPTO_OPEN=int(os.getenv("CERTAINU_MAX_CRYPTO_OPEN","24"));CRYPTO_BONUS=float(os.getenv("CERTAINU_CRYPTO_BONUS","6"));DEMO_REMOVAL_REAL_RESOLVED=int(os.getenv("CERTAINU_DEMO_REMOVAL_REAL_RESOLVED","10"));MODEL_VERSION="rules-v2.6-open-resolved-caps"
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def get_json(url):return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CERTAINU/2.0','Accept':'application/json'}),timeout=30))
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
 e=parse_end(m);return (e-datetime.now(timezone.utc)).total_seconds()/3600 if e else None
def bucket_hours(h):
 if h is None:return 'long'
 if h<=0:return 'expired'
 if h<=24:return 'quick'
 if h<=72:return 'short'
 if h<=168:return 'week'
 return 'long'
def bucket_pred(p):
 raw=p.get('market_end_date') or p.get('end_date') or p.get('endDate')
 if not raw:return 'long'
 try:return bucket_hours((datetime.fromisoformat(str(raw).replace('Z','+00:00')).astimezone(timezone.utc)-datetime.now(timezone.utc)).total_seconds()/3600)
 except:return 'long'
def speed_score(h):
 if h is None:return -20
 if h<=0:return -100
 if h<=24:return 30
 if h<=72:return 24
 if h<=168:return 15
 if h<=336:return 2
 if h<=720:return -8
 return -18
def crypto_market(x):
 text=' '.join(str(x.get(k) or '') for k in ('question','slug','eventSlug','description')).lower();ev=x.get('events') or []
 if isinstance(ev,list):text+=' '+' '.join(str((e or {}).get(k) or '') for e in ev for k in ('title','slug','description'))
 return any(t in text for t in ('bitcoin',' btc','btc ','ethereum',' eth','eth ','solana',' sol','sol ','crypto','cryptocurrency','dogecoin',' doge','xrp','ripple','cardano',' ada','chainlink','link price','bnb','avalanche','avax','sui','memecoin','meme coin'))
def crypto_pred(p):return crypto_market({'question':p.get('question'),'slug':p.get('slug'),'eventSlug':p.get('eventSlug'),'description':p.get('description')})
def market_url(m):
 ev=m.get('events') or [];es=str((ev[0] or {}).get('slug') or '') if isinstance(ev,list) and ev else '';slug=es or str(m.get('eventSlug') or m.get('slug') or '');return f'https://polymarket.com/event/{slug}' if slug else 'https://polymarket.com/'
def model(m):
 p=yes_prob(m);v=volume(m);l=liquidity(m);vq=min(1,math.log10(max(v,10))/7);lq=min(1,math.log10(max(l,10))/6) if l else vq*.75;q=max(.2,min(1,.65*vq+.35*lq));ext=(-7*q if p>=80 else 7*q if p<=20 else -3.5*q if p>=68 else 3.5*q if p<=32 else 0);center=abs(p-50)/50;conv=(5.2+2.8*q)*(.55+.45*center);est=max(5,min(95,p+ext+(1 if p>=50 else -1)*conv));pick='YES' if est>=50 else 'NO';conf=round(est if pick=='YES' else 100-est);side=p if pick=='YES' else 100-p;return pick,conf,conf-side,f'Rules-v2: market {p:.1f}% YES; volume ${v:,.0f}; liquidity ${l:,.0f}; quality {q:.2f}; model {est:.1f}% YES.',p,v,l
def status(p):
 s=str(p.get('status','')).lower()
 if s=='resolved':
  r=str(p.get('result','')).upper();return 'won' if r=='WIN' else 'lost' if r=='LOSS' else s
 return s
def demo(p):return bool(p.get('seeded_demo',False))
def main():
 state=json.loads(DATA.read_text()) if DATA.exists() else {'predictions':[]};preds=state.setdefault('predictions',[]);retired={str(x) for x in state.setdefault('retired_market_ids',[])};real=[p for p in preds if not demo(p)];byid={str(p.get('id')):p for p in real if p.get('id') is not None};active=[];seen=set()
 for offset in range(0,1000,100):
  try:page=get_json(GAMMA+'?'+urllib.parse.urlencode({'active':'true','closed':'false','limit':'100','offset':offset}))
  except Exception as e:print(f'[scan] stopped at offset {offset}: {e}');break
  if not page:break
  for m in page:
   mid=str(m.get('id') or '')
   if mid and mid not in seen:seen.add(mid);active.append(m)
  if len(page)<100:break
 active_by={str(m.get('id')):m for m in active};resolved=0
 for p in real:
  if status(p)!='open':continue
  m=active_by.get(str(p.get('id')))
  if not m:
   try:x=get_json(GAMMA+'?'+urllib.parse.urlencode({'id':str(p.get('id'))}));m=x[0] if x else None
   except:m=None
  if not m:continue
  cur=yes_prob(m);p['market_probability_current']=round(cur,2);p['volume']=volume(m);p['updated_at']=now()
  if m.get('closed') or cur>=99 or cur<=1:
   outcome='YES' if cur>=99 else 'NO' if cur<=1 else None
   if outcome:p['result']=outcome;p['status']='won' if outcome==str(p.get('pick','')).upper() else 'lost';p['resolved_at']=now();resolved+=1
 real_resolved=sum(status(p) in('won','lost') for p in real)
 if real_resolved>=DEMO_REMOVAL_REAL_RESOLVED:preds[:]=[p for p in preds if not demo(p)]
 real=[p for p in preds if not demo(p)];byid={str(p.get('id')):p for p in real if p.get('id') is not None};open_preds=[p for p in real if status(p)=='open'];open_count=len(open_preds);long_open=sum(bucket_pred(p)=='long' for p in open_preds);crypto_open=sum(crypto_pred(p) for p in open_preds);candidates=[];bucket_counts={'quick':0,'short':0,'week':0,'long':0};crypto_qualifying=0
 if open_count<MAX_OPEN:
  for m in active:
   mid=str(m.get('id') or '');v=volume(m);l=liquidity(m)
   if not mid or mid in byid or mid in retired or not(v>=MIN_VOLUME or(v==0 and l>=MIN_VOLUME)):continue
   p0=yes_prob(m)
   if p0<=3 or p0>=97:continue
   h=hours_left(m);b=bucket_hours(h)
   if b=='expired' or(b=='long' and long_open>=MAX_LONG_OPEN):continue
   iscrypto=crypto_market(m)
   if iscrypto and crypto_open>=MAX_CRYPTO_OPEN:continue
   pick,conf,edge,reason,yesp,v,l=model(m)
   if edge<MIN_EDGE:continue
   uncertainty=2 if 10<=p0<=90 else -2;quality=min(2,math.log10(max(v,1))/4)+min(1.5,math.log10(max(l,1))/4 if l else 0);score=edge+speed_score(h)+uncertainty+quality+(CRYPTO_BONUS if iscrypto else 0);candidates.append((score,edge,v,m,pick,conf,reason,yesp,l,h,b,iscrypto));bucket_counts[b]+=1;crypto_qualifying+=int(iscrypto)
 candidates.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True);slots=max(0,min(MAX_NEW,MAX_OPEN-open_count));created=0
 for score,edge,v,m,pick,conf,reason,yesp,l,h,b,iscrypto in candidates:
  if created>=slots:break
  if b=='long' and long_open>=MAX_LONG_OPEN:continue
  if iscrypto and crypto_open>=MAX_CRYPTO_OPEN:continue
  side=yesp if pick=='YES' else 100-yesp;e=parse_end(m);preds.append({'id':str(m['id']),'slug':m.get('slug'),'question':m.get('question','Untitled market'),'pick':pick,'confidence':conf,'market_probability_at_pick':round(yesp,2),'market_probability_current':round(yesp,2),'edge_at_pick':round(conf-side,2),'selection_score':round(score,2),'hours_to_resolution_at_pick':round(h,1) if h is not None else None,'market_end_date':e.isoformat().replace('+00:00','Z') if e else None,'volume':v,'liquidity':l,'locked_at':now(),'updated_at':now(),'status':'open','result':None,'resolved_at':None,'market_url':market_url(m),'reason':reason,'model_version':MODEL_VERSION,'category':'crypto' if iscrypto else 'general','seeded_demo':False});created+=1;long_open+=int(b=='long');crypto_open+=int(iscrypto)
 # Independent retention limits: keep up to 100 open and 1000 resolved predictions.
 open_items=[p for p in preds if status(p)=='open'];resolved_items=[p for p in preds if status(p) in ('won','lost','resolved','void')];other_items=[p for p in preds if p not in open_items and p not in resolved_items]
 def newest(items,limit):return sorted(items,key=lambda p:str(p.get('resolved_at') or p.get('locked_at') or ''),reverse=True)[:limit]
 kept_open=newest(open_items,MAX_OPEN);kept_resolved=newest(resolved_items,MAX_RESOLVED);kept_ids={id(p) for p in kept_open+kept_resolved+other_items}
 for p in preds:
  if id(p) not in kept_ids and not demo(p) and p.get('id') is not None:retired.add(str(p['id']))
 preds[:]=kept_open+kept_resolved+other_items
 state['retired_market_ids']=sorted(retired);real=[p for p in preds if not demo(p)];wins=sum(status(p)=='won' for p in real);losses=sum(status(p)=='lost' for p in real);ropen=sum(status(p)=='open' for p in real);state['updated_at']=now();state['model_version']=MODEL_VERSION;state['stats']={'real_wins':wins,'real_losses':losses,'real_resolved':wins+losses,'real_open':ropen,'real_accuracy':round(wins/(wins+losses)*100,1) if wins+losses else None,'seeded_demo_count':sum(demo(p) for p in preds),'visible_predictions':len(preds),'max_open':MAX_OPEN,'max_resolved':MAX_RESOLVED,'crypto_open':sum(crypto_pred(p) for p in real if status(p)=='open')};DATA.write_text(json.dumps(state,indent=2)+'\n');print(f'[scan] qualifying={bucket_counts}; crypto_qualifying={crypto_qualifying}; crypto_open={crypto_open}/{MAX_CRYPTO_OPEN}; long_open={long_open}/{MAX_LONG_OPEN}');print(f'[run] candidates={len(candidates)}, created={created}, resolved={resolved}, open={ropen}/{MAX_OPEN}, resolved_kept={wins+losses}/{MAX_RESOLVED}, visible={len(preds)}')
if __name__=='__main__':main()
