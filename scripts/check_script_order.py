#!/usr/bin/env python3
"""Smoke-check the script layout and prediction UI wiring."""
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/"index.html").read_text(encoding="utf-8")
scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html)
expected=["js/main-1.js","js/certainuties.js","js/ui-enhancements.js"]
if scripts!=expected:
    raise SystemExit(f"Unexpected script order: {scripts!r}; expected {expected!r}")
for key in ("predictionList","predictionExpandBtn","receiptsLedger","predictionTimeFilters","predictionTopicFilters"):
    if f'id="{key}"' not in html and f"id='{key}'" not in html:
        raise SystemExit(f"Missing required prediction UI element: {key}")
js=(root/"js/certainuties.js").read_text(encoding="utf-8")
for term in ("loadPredictions()","renderResolvedArchive(data)","applyPredictionFilters()"):
    if term not in js: raise SystemExit(f"Missing prediction hook: {term}")
print("Prediction UI script wiring valid")
