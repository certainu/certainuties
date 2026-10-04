#!/usr/bin/env python3
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"index.html"
s=P.read_text(encoding="utf-8")

controls='''
    <div class="prediction-time-filters reveal" id="predictionTimeFilters" aria-label="Filter predictions by resolution time">
      <button type="button" class="prediction-time-filter active" data-filter="all">ALL <span id="count-all">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="quick">⚡ QUICK ≤24H <span id="count-quick">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="short">🔥 SHORT 1–3D <span id="count-short">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="week">🎯 THIS WEEK <span id="count-week">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="long">🔮 LONG TERM <span id="count-long">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="resolved">✅ RESOLVED <span id="count-resolved">0</span></button>
    </div>
'''
needle='    <div class="prediction-list" id="predictionList">'
if 'id="predictionTimeFilters"' not in s:
    s=s.replace(needle,controls+'\n'+needle,1)
elif 'data-filter="resolved"' not in s:
    long_btn='      <button type="button" class="prediction-time-filter" data-filter="long">🔮 LONG TERM <span id="count-long">0</span></button>'
    s=s.replace(long_btn,long_btn+'\n      <button type="button" class="prediction-time-filter" data-filter="resolved">✅ RESOLVED <span id="count-resolved">0</span></button>',1)

css='''
<style>
/* CERTAINUTIES resolution-time filters — prediction cards intentionally unchanged */
.prediction-time-filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}
.prediction-time-filter{border:1px solid rgba(255,255,255,.18);background:rgba(7,24,79,.24);color:rgba(255,255,255,.78);border-radius:999px;padding:10px 13px;font-size:9px;font-weight:900;letter-spacing:.06em;cursor:pointer;transition:.18s ease}
.prediction-time-filter:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-1px)}
.prediction-time-filter.active{background:#fff;color:#1747df;border-color:#fff;box-shadow:0 8px 20px rgba(4,18,76,.16)}
.prediction-time-filter span{opacity:.7;margin-left:4px}
@media(max-width:600px){.prediction-time-filters{gap:6px}.prediction-time-filter{padding:9px 10px;font-size:8px}}
</style>
'''
if 'CERTAINUTIES resolution-time filters' not in s:
    s=s.replace('</head>',css+'\n</head>',1)

old="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||''};"
new="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||'',\n    market_end_date:p.market_end_date||p.end_date||p.endDate||p.resolution_date||''};"
if old in s:s=s.replace(old,new,1)

oldblock="""  predictionList.innerHTML=
    predictions.map(renderPrediction).join('') ||
    '<article class="prediction-card"><h3>No official calls yet.</h3></article>';

  // Show the three most recent calls by default. The arrow reveals/collapses the archive.
  predictionList.classList.toggle('prediction-list-collapsed',predictions.length>3);
  if(expandBtn){"""
newblock="""  function resolutionBucket(raw){
    const p=normalizePrediction(raw);
    if(['won','lost','void','resolved'].includes(p.status) || p.resolved_at) return 'resolved';
    const end=Date.parse(p.market_end_date||'');
    if(!end) return 'long';
    const hours=(end-Date.now())/3600000;
    if(hours<=24) return 'quick';
    if(hours<=72) return 'short';
    if(hours<=168) return 'week';
    return 'long';
  }
  const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0,resolved:0};
  predictions.forEach(p=>bucketCounts[resolutionBucket(p)]++);
  predictionList.innerHTML=
    predictions.map(p=>renderPrediction(p).replace('<article class="prediction-card','<article data-resolution-bucket="'+resolutionBucket(p)+'" class="prediction-card')).join('') ||
    '<article class="prediction-card"><h3>No official calls yet.</h3></article>';

  Object.entries(bucketCounts).forEach(([key,value])=>{
    const el=document.getElementById('count-'+key); if(el) el.textContent=value;
  });
  const filterBar=document.getElementById('predictionTimeFilters');
  if(filterBar){
    filterBar.onclick=(event)=>{
      const btn=event.target.closest('.prediction-time-filter'); if(!btn)return;
      const filter=btn.dataset.filter;
      filterBar.querySelectorAll('.prediction-time-filter').forEach(b=>b.classList.toggle('active',b===btn));
      predictionList.querySelectorAll('.prediction-card').forEach(card=>{
        card.style.display=(filter==='all'||card.dataset.resolutionBucket===filter)?'':'none';
      });
      // Preserve the archive arrow for every category instead of hiding it.
      const visibleCards=[...predictionList.querySelectorAll('.prediction-card')].filter(card=>card.style.display!=='none');
      const shouldCollapse=visibleCards.length>3;
      predictionList.classList.toggle('prediction-list-collapsed',shouldCollapse);
      if(expandBtn){
        expandBtn.hidden=!shouldCollapse;
        expandBtn.setAttribute('aria-expanded',shouldCollapse?'false':'true');
      }
      const label=document.getElementById('predictionExpandLabel');
      if(label){ label.hidden=!shouldCollapse; label.textContent='SHOW MORE'; }
    };
  }

  // Keep the existing three-card expander on the default ALL view.
  predictionList.classList.toggle('prediction-list-collapsed',predictions.length>3);
  if(expandBtn){"""
if oldblock in s:s=s.replace(oldblock,newblock,1)
else:
    s=s.replace("if(['won','lost','void'].includes(p.status)) return 'long';","if(['won','lost','void','resolved'].includes(p.status) || p.resolved_at) return 'resolved';")
    s=s.replace("const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0};","const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0,resolved:0};")
    # Repair the prior category patch that hid the expander after a filter click.
    s=s.replace("predictionList.classList.remove('prediction-list-collapsed');\n      if(expandBtn) expandBtn.hidden=true;\n      const label=document.getElementById('predictionExpandLabel'); if(label) label.hidden=true;",
'''const visibleCards=[...predictionList.querySelectorAll('.prediction-card')].filter(card=>card.style.display!=='none');
      const shouldCollapse=visibleCards.length>3;
      predictionList.classList.toggle('prediction-list-collapsed',shouldCollapse);
      if(expandBtn){ expandBtn.hidden=!shouldCollapse; expandBtn.setAttribute('aria-expanded',shouldCollapse?'false':'true'); }
      const label=document.getElementById('predictionExpandLabel');
      if(label){ label.hidden=!shouldCollapse; label.textContent='SHOW MORE'; }''')

P.write_text(s,encoding="utf-8")
print('CERTAINUTIES category UI + collapse arrow patched')
