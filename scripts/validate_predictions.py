#!/usr/bin/env python3
"""Reject malformed prediction feeds before publication."""
import json, math, sys
from datetime import datetime
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else "data/predictions.json")
data=json.loads(p.read_text(encoding="utf-8"))
if not isinstance(data,dict) or not isinstance(data.get("predictions"),list):
    raise SystemExit("Feed requires a predictions array")
ids=set()
for i,x in enumerate(data["predictions"]):
    if not isinstance(x,dict): raise SystemExit(f"Row {i} must be an object")
    mid=str(x.get("id") or "")
    if not mid or mid in ids: raise SystemExit(f"Missing/duplicate market id: {mid}")
    ids.add(mid)
    if not isinstance(x.get("question"),str) or not x["question"].strip(): raise SystemExit(f"{mid}: missing question")
    if str(x.get("pick","")).upper() not in ("YES","NO"): raise SystemExit(f"{mid}: invalid pick")
    if str(x.get("status","")).lower() not in ("open","won","lost","resolved","void"): raise SystemExit(f"{mid}: invalid status")
    for key in ("confidence","market_probability_at_pick","market_probability_current"):
        v=x.get(key)
        if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=100): raise SystemExit(f"{mid}: invalid {key}")
    for key in ("locked_at","resolved_at","market_end_date"):
        if x.get(key):
            try: datetime.fromisoformat(str(x[key]).replace("Z","+00:00"))
            except ValueError: raise SystemExit(f"{mid}: invalid {key}")
print(f"Validated {len(ids)} prediction records")
