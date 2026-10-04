#!/usr/bin/env python3
"""CERTAINU rules-v2 updater with resolution-speed ranking."""
import json, math, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "predictions.json"
GAMMA = "https://gamma-api.polymarket.com/markets"
MIN_VOLUME = float(os.getenv("CERTAINU_MIN_VOLUME", "25000"))
MIN_EDGE = float(os.getenv("CERTAINU_MIN_EDGE", "5"))
MAX_OPEN = int(os.getenv("CERTAINU_MAX_OPEN", "5"))
MAX_NEW = int(os.getenv("CERTAINU_MAX_NEW_PER_RUN", "1"))
MAX_VISIBLE = int(os.getenv("CERTAINU_MAX_VISIBLE", "24"))
DEMO_REMOVAL_REAL_RESOLVED = int(os.getenv("CERTAINU_DEMO_REMOVAL_REAL_RESOLVED", "10"))
MODEL_VERSION = "rules-v2.3-speed"

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CERTAINU/2.0"})
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
    outcomes,prices=arr(m.get("outcomes")),arr(m.get("outcomePrices"))
    for i,o in enumerate(outcomes):
        if str(o).upper()=="YES" and i<len(prices):return f(prices[i])*100
    return f(m.get("bestAsk") or m.get("lastTradePrice"))*100
def _first_numeric(m,keys):
    for key in keys:
        v=m.get(key)
        if v is None or v=="":continue
        if isinstance(v,str):v=v.replace(",","").replace("$","").strip()
        try:return float(v)
        except (TypeError,ValueError):continue
    return 0.0
def market_volume(m):return max(0.0,_first_numeric(m,("volumeNum","volume","volumeClob","volume24hr","volume1wk","volume1mo","volume1yr")))
def market_liquidity(m):return max(0.0,_first_numeric(m,("liquidityNum","liquidity","liquidityClob")))
def market_url(m):
    events=m.get("events") or []; event_slug=""
    if isinstance(events,list) and events:event_slug=str((events[0] or {}).get("slug") or "")
    slug=event_slug or str(m.get("eventSlug") or m.get("slug") or "")
    return f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com/"
def parse_end(m):
    raw=m.get("endDate") or m.get("end_date") or m.get("endDateIso") or m.get("endDateISO")
    if not raw:return None
    try:return datetime.fromisoformat(str(raw).replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:return None
def resolution_speed(m):
    end=parse_end(m)
    if not end:return 0.0,None
    hours=(end-datetime.now(timezone.utc)).total_seconds()/3600
    if hours<=0:return -20.0,hours
    if hours<=24:return 8.0,hours
    if hours<=72:return 7.0,hours
    if hours<=168:return 5.0,hours
    if hours<=336:return 3.0,hours
    if hours<=720:return 0.0,hours
    if hours<=2160:return -3.0,hours
    return -6.0,hours
def rules_v2(m,previous_prob=None):
    p=yes_prob(m);vol=market_volume(m);liq=market_liquidity(m)
    momentum=0.0 if previous_prob is None else max(-10.0,min(10.0,p-previous_prob))
    vq=min(1.0,math.log10(max(vol,10.0))/7.0);lq=min(1.0,math.log10(max(liq,10.0))/6.0) if liq else vq*.75
    quality=max(.20,min(1.0,.65*vq+.35*lq));extreme=0.0
    if p>=80:extreme=-7.0*quality
    elif p<=20:extreme=7.0*quality
    elif p>=68:extreme=-3.5*quality
    elif p<=32:extreme=3.5*quality
    momentum_adj=momentum*.45*quality;center=abs(p-50.0)/50.0;conviction=(5.2+2.8*quality)*(.55+.45*center);direction=1 if p>=50 else -1
    estimate=max(5.0,min(95.0,p+extreme+momentum_adj+direction*conviction));pick="YES" if estimate>=50 else "NO";confidence=round(estimate if pick=="YES" else 100-estimate);market_side=p if pick=="YES" else 100-p;edge=confidence-market_side
    reason=f"Rules-v2: market {p:.1f}% YES; volume ${vol:,.0f}; liquidity ${liq:,.0f}; quality {quality:.2f}; model {estimate:.1f}% YES."
    return pick,confidence,edge,reason,p,vol,liq
def normalize_status(p):
    s=str(p.get("status","")).lower()
    if s=="resolved":
        r=str(p.get("result","")).upper()
        if r=="WIN":return "won"
        if r=="LOSS":return "lost"
    return s
def is_demo(p):return bool(p.get("seeded_demo",False))
def main():
    state=json.loads(DATA.read_text()) if DATA.exists() else {"predictions":[]};preds=state.setdefault("predictions",[]);retired_ids=set(str(x) for x in state.setdefault("retired_market_ids",[]));real_preds=[p for p in preds if not is_demo(p)];byid={str(p.get("id")):p for p in real_preds if p.get("id") is not None}
    PAGE_SIZE=100;MAX_MARKETS=1000;active=[];seen_ids=set()
    for offset in range(0,MAX_MARKETS,PAGE_SIZE):
        qs=urllib.parse.urlencode({"active":"true","closed":"false","limit":str(PAGE_SIZE),"offset":str(offset)});page=get_json(GAMMA+"?"+qs)
        if not page:break
        for m in page:
            mid=str(m.get("id") or "")
            if mid and mid not in seen_ids:seen_ids.add(mid);active.append(m)
        if len(page)<PAGE_SIZE:break
    active_by_id={str(m.get("id")):m for m in active};refreshed=resolved=0
    for p in real_preds:
        if normalize_status(p)!="open":continue
        mid=str(p.get("id"));m=active_by_id.get(mid)
        if m is None:
            try:
                exact=get_json(GAMMA+"?"+urllib.parse.urlencode({"id":mid}));m=exact[0] if exact else None
            except Exception:m=None
        if not m:continue
        cur=yes_prob(m);p["market_probability_current"]=round(cur,2);p["volume"]=market_volume(m);p["updated_at"]=now();refreshed+=1
        if m.get("closed") or cur>=99 or cur<=1:
            outcome="YES" if cur>=99 else "NO" if cur<=1 else None
            if outcome:p["result"]=outcome;p["status"]="won" if outcome==str(p.get("pick","")).upper() else "lost";p["resolved_at"]=now();resolved+=1
    real_resolved=sum(normalize_status(p) in ("won","lost") for p in real_preds);demos_before=sum(is_demo(p) for p in preds)
    if real_resolved>=DEMO_REMOVAL_REAL_RESOLVED and demos_before:preds[:]=[p for p in preds if not is_demo(p)]
    real_preds=[p for p in preds if not is_demo(p)];byid={str(p.get("id")):p for p in real_preds if p.get("id") is not None};open_count=sum(normalize_status(p)=="open" for p in real_preds);candidates=[]
    if open_count<MAX_OPEN:
        for m in active:
            mid=str(m.get("id") or "");vol=market_volume(m);liqf=market_liquidity(m)
            if not mid or mid in byid or mid in retired_ids:continue
            if not (vol>=MIN_VOLUME or (vol==0 and liqf>=MIN_VOLUME)):continue
            p0=yes_prob(m)
            # Prefer meaningful uncertainty; still allow 3-10/90-97 markets, but penalize them.
            if p0<=3 or p0>=97:continue
            pick,conf,edge,reason,yesp,vol,liq=rules_v2(m)
            if edge<MIN_EDGE:continue
            speed,hours=resolution_speed(m);uncertainty_bonus=2.0 if 10<=p0<=90 else -2.0
            quality_bonus=min(2.0,math.log10(max(vol,1))/4.0)+min(1.5,math.log10(max(liq,1))/4.0 if liq else 0.0)
            score=edge+speed+uncertainty_bonus+quality_bonus
            candidates.append((score,edge,vol,m,pick,conf,reason,yesp,liq,hours))
    candidates.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True);slots=max(0,min(MAX_NEW,MAX_OPEN-open_count));created=0
    for score,edge,vol,m,pick,conf,reason,yesp,liq,hours in candidates[:slots]:
        market_side=yesp if pick=="YES" else 100-yesp
        preds.append({"id":str(m["id"]),"slug":m.get("slug"),"question":m.get("question","Untitled market"),"pick":pick,"confidence":conf,"market_probability_at_pick":round(yesp,2),"market_probability_current":round(yesp,2),"edge_at_pick":round(conf-market_side,2),"selection_score":round(score,2),"hours_to_resolution_at_pick":round(hours,1) if hours is not None else None,"market_end_date":parse_end(m).isoformat().replace("+00:00","Z") if parse_end(m) else None,"volume":vol,"liquidity":liq,"locked_at":now(),"updated_at":now(),"status":"open","result":None,"resolved_at":None,"market_url":market_url(m),"reason":reason,"model_version":MODEL_VERSION,"seeded_demo":False});created+=1
        print(f"[new] {pick} {conf}% | score {score:.1f} | resolves in {hours:.1f}h" if hours is not None else f"[new] {pick} {conf}% | score {score:.1f}")
    removed=0
    while len(preds)>MAX_VISIBLE:
        oi=min(range(len(preds)),key=lambda i:str(preds[i].get("locked_at") or ""));old=preds.pop(oi)
        if not is_demo(old) and old.get("id") is not None:retired_ids.add(str(old["id"]))
        removed+=1
    state["retired_market_ids"]=sorted(retired_ids);real_preds=[p for p in preds if not is_demo(p)];wins=sum(normalize_status(p)=="won" for p in real_preds);losses=sum(normalize_status(p)=="lost" for p in real_preds);ropen=sum(normalize_status(p)=="open" for p in real_preds);state["updated_at"]=now();state["model_version"]=MODEL_VERSION;state["stats"]={"real_wins":wins,"real_losses":losses,"real_resolved":wins+losses,"real_open":ropen,"real_accuracy":round(wins/(wins+losses)*100,1) if wins+losses else None,"seeded_demo_count":sum(is_demo(p) for p in preds),"visible_predictions":len(preds)};DATA.write_text(json.dumps(state,indent=2,sort_keys=False)+"\n");print(f"[run] candidates={len(candidates)}, created={created}, retired={removed}, visible={len(preds)}")
if __name__=="__main__":main()
