#!/usr/bin/env python3
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"index.html"
s=P.read_text(encoding="utf-8")

# Keep the public status banner synchronized with the hourly GitHub updater.
s=s.replace('AUTO-REFRESH ≈ EVERY 2 HOURS','AUTO-REFRESH ≈ EVERY HOUR')
s=s.replace('AUTO-REFRESH ≈ EVERY 30 MINUTES','AUTO-REFRESH ≈ EVERY HOUR')

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

/* Make the four CERTAINU confidence-scale pills much easier to notice. */
.certainu-confidence-pill,
.confidence-pill,
.confidence-scale span,
.confidence-legend span,
.certainty-scale span,
.certainty-legend span{
  display:inline-flex!important;
  align-items:center;
  justify-content:center;
  min-height:42px;
  padding:11px 18px!important;
  border:2px solid rgba(255,255,255,.42)!important;
  border-radius:999px!important;
  background:rgba(13,54,178,.52)!important;
  color:#fff!important;
  font-size:12px!important;
  font-weight:900!important;
  line-height:1.1!important;
  letter-spacing:.035em!important;
  box-shadow:0 5px 14px rgba(5,24,100,.18), inset 0 1px 0 rgba(255,255,255,.08)!important;
}
.confidence-scale,.confidence-legend,.certainty-scale,.certainty-legend{gap:12px!important;align-items:center!important;flex-wrap:wrap!important}

@media(max-width:600px){
  .prediction-time-filters{gap:6px}.prediction-time-filter{padding:9px 10px;font-size:8px}
  .certainu-confidence-pill,.confidence-pill,.confidence-scale span,.confidence-legend span,.certainty-scale span,.certainty-legend span{min-height:38px;padding:9px 13px!important;font-size:10px!important}
  .confidence-scale,.confidence-legend,.certainty-scale,.certainty-legend{gap:8px!important}
}
</style>
'''
if 'CERTAINUTIES resolution-time filters' not in s:
    s=s.replace('</head>',css+'\n</head>',1)
elif 'Make the four CERTAINU confidence-scale pills' not in s:
    # Existing patch style is already present; inject the confidence enhancement separately.
    confidence_css='''\n<style>\n/* Make the four CERTAINU confidence-scale pills much easier to notice. */\n.certainu-confidence-pill,.confidence-pill,.confidence-scale span,.confidence-legend span,.certainty-scale span,.certainty-legend span{display:inline-flex!important;align-items:center;justify-content:center;min-height:42px;padding:11px 18px!important;border:2px solid rgba(255,255,255,.42)!important;border-radius:999px!important;background:rgba(13,54,178,.52)!important;color:#fff!important;font-size:12px!important;font-weight:900!important;line-height:1.1!important;letter-spacing:.035em!important;box-shadow:0 5px 14px rgba(5,24,100,.18),inset 0 1px 0 rgba(255,255,255,.08)!important}.confidence-scale,.confidence-legend,.certainty-scale,.certainty-legend{gap:12px!important;align-items:center!important;flex-wrap:wrap!important}@media(max-width:600px){.certainu-confidence-pill,.confidence-pill,.confidence-scale span,.confidence-legend span,.certainty-scale span,.certainty-legend span{min-height:38px;padding:9px 13px!important;font-size:10px!important}.confidence-scale,.confidence-legend,.certainty-scale,.certainty-legend{gap:8px!important}}\n</style>\n'''
    s=s.replace('</head>',confidence_css+'\n</head>',1)

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
      const visibleCards=[...predictionList.querySelectorAll('.prediction-card')].filter(card=>card.style.display!=='none');
      const shouldCollapse=visibleCards.length>3;
      predictionList.classList.toggle('prediction-list-collapsed',shouldCollapse);
      if(expandBtn){expandBtn.hidden=!shouldCollapse;expandBtn.setAttribute('aria-expanded',shouldCollapse?'false':'true');}
      const label=document.getElementById('predictionExpandLabel');
      if(label){label.hidden=!shouldCollapse;label.textContent='SHOW MORE';}
    };
  }

  predictionList.classList.toggle('prediction-list-collapsed',predictions.length>3);
  if(expandBtn){"""
if oldblock in s:s=s.replace(oldblock,newblock,1)
else:
    s=s.replace("if(['won','lost','void'].includes(p.status)) return 'long';","if(['won','lost','void','resolved'].includes(p.status) || p.resolved_at) return 'resolved';")
    s=s.replace("const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0};","const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0,resolved:0};")

P.write_text(s,encoding="utf-8")
print('CERTAINUTIES categories + collapse arrow + hourly refresh banner + larger confidence bubbles patched')
