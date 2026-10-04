#!/usr/bin/env python3
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"index.html"
s=P.read_text(encoding="utf-8")

controls='''\n    <div class="prediction-time-filters reveal" id="predictionTimeFilters" aria-label="Filter predictions by resolution time">\n      <button type="button" class="prediction-time-filter active" data-filter="all">ALL <span id="count-all">0</span></button>\n      <button type="button" class="prediction-time-filter" data-filter="quick">⚡ QUICK ≤24H <span id="count-quick">0</span></button>\n      <button type="button" class="prediction-time-filter" data-filter="short">🔥 SHORT 1–3D <span id="count-short">0</span></button>\n      <button type="button" class="prediction-time-filter" data-filter="week">🎯 THIS WEEK <span id="count-week">0</span></button>\n      <button type="button" class="prediction-time-filter" data-filter="long">🔮 LONG TERM <span id="count-long">0</span></button>\n    </div>\n'''
needle='    <div class="prediction-list" id="predictionList">'
if 'id="predictionTimeFilters"' not in s:
    s=s.replace(needle,controls+'\n'+needle,1)

css='''\n<style>\n/* CERTAINUTIES resolution-time filters — prediction cards intentionally unchanged */\n.prediction-time-filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}\n.prediction-time-filter{border:1px solid rgba(255,255,255,.18);background:rgba(7,24,79,.24);color:rgba(255,255,255,.78);border-radius:999px;padding:10px 13px;font-size:9px;font-weight:900;letter-spacing:.06em;cursor:pointer;transition:.18s ease}\n.prediction-time-filter:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-1px)}\n.prediction-time-filter.active{background:#fff;color:#1747df;border-color:#fff;box-shadow:0 8px 20px rgba(4,18,76,.16)}\n.prediction-time-filter span{opacity:.7;margin-left:4px}\n@media(max-width:600px){.prediction-time-filters{gap:6px}.prediction-time-filter{padding:9px 10px;font-size:8px}}\n</style>\n'''
if 'CERTAINUTIES resolution-time filters' not in s:
    s=s.replace('</head>',css+'\n</head>',1)

old="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||''};"
new="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||'',\n    market_end_date:p.market_end_date||p.end_date||p.endDate||p.resolution_date||''};"
if old in s:s=s.replace(old,new,1)

oldblock="""  predictionList.innerHTML=\n    predictions.map(renderPrediction).join('') ||\n    '<article class="prediction-card"><h3>No official calls yet.</h3></article>';\n\n  // Show the three most recent calls by default. The arrow reveals/collapses the archive.\n  predictionList.classList.toggle('prediction-list-collapsed',predictions.length>3);\n  if(expandBtn){"""
newblock="""  function resolutionBucket(raw){\n    const p=normalizePrediction(raw);\n    if(['won','lost','void'].includes(p.status)) return 'long';\n    const end=Date.parse(p.market_end_date||'');\n    if(!end) return 'long';\n    const hours=(end-Date.now())/3600000;\n    if(hours<=24) return 'quick';\n    if(hours<=72) return 'short';\n    if(hours<=168) return 'week';\n    return 'long';\n  }\n  const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0};\n  predictions.forEach(p=>bucketCounts[resolutionBucket(p)]++);\n  predictionList.innerHTML=\n    predictions.map(p=>renderPrediction(p).replace('<article class="prediction-card','<article data-resolution-bucket="'+resolutionBucket(p)+'" class="prediction-card')).join('') ||\n    '<article class="prediction-card"><h3>No official calls yet.</h3></article>';\n\n  Object.entries(bucketCounts).forEach(([key,value])=>{\n    const el=document.getElementById('count-'+key); if(el) el.textContent=value;\n  });\n  const filterBar=document.getElementById('predictionTimeFilters');\n  if(filterBar){\n    filterBar.onclick=(event)=>{\n      const btn=event.target.closest('.prediction-time-filter'); if(!btn)return;\n      const filter=btn.dataset.filter;\n      filterBar.querySelectorAll('.prediction-time-filter').forEach(b=>b.classList.toggle('active',b===btn));\n      predictionList.querySelectorAll('.prediction-card').forEach(card=>{\n        card.style.display=(filter==='all'||card.dataset.resolutionBucket===filter)?'':'none';\n      });\n      predictionList.classList.remove('prediction-list-collapsed');\n      if(expandBtn) expandBtn.hidden=true;\n      const label=document.getElementById('predictionExpandLabel'); if(label) label.hidden=true;\n    };\n  }\n\n  // Keep the existing three-card expander on the default ALL view.\n  predictionList.classList.toggle('prediction-list-collapsed',predictions.length>3);\n  if(expandBtn){"""
if oldblock in s:s=s.replace(oldblock,newblock,1)

P.write_text(s,encoding="utf-8")
print('CERTAINUTIES category UI patched')
