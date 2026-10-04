#!/usr/bin/env python3
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"index.html";s=P.read_text(encoding="utf-8")
s=s.replace('AUTO-REFRESH ≈ EVERY 2 HOURS','AUTO-REFRESH ≈ EVERY HOUR').replace('AUTO-REFRESH ≈ EVERY 30 MINUTES','AUTO-REFRESH ≈ EVERY HOUR')
needle='    <div class="prediction-list" id="predictionList">'
time='''    <div class="prediction-time-filters reveal" id="predictionTimeFilters" aria-label="Filter predictions by resolution time">
      <button type="button" class="prediction-time-filter active" data-filter="all">ALL <span id="count-all">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="quick">⚡ QUICK ≤24H <span id="count-quick">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="short">🔥 SHORT 1–3D <span id="count-short">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="week">🎯 THIS WEEK <span id="count-week">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="long">🔮 LONG TERM <span id="count-long">0</span></button>
      <button type="button" class="prediction-time-filter" data-filter="resolved">✅ RESOLVED <span id="count-resolved">0</span></button>
    </div>'''
topic='''    <div class="prediction-topic-filters reveal" id="predictionTopicFilters" aria-label="Filter predictions by topic">
      <span class="prediction-filter-label">TOPIC</span>
      <button type="button" class="prediction-topic-filter active" data-topic="all">ALL TOPICS</button>
      <button type="button" class="prediction-topic-filter" data-topic="crypto">🪙 CRYPTO</button>
      <button type="button" class="prediction-topic-filter" data-topic="politics">🏛️ POLITICS</button>
      <button type="button" class="prediction-topic-filter" data-topic="geopolitics">🌎 GEOPOLITICS</button>
      <button type="button" class="prediction-topic-filter" data-topic="sports">🏈 SPORTS</button>
      <button type="button" class="prediction-topic-filter" data-topic="economy">💰 ECONOMY</button>
      <button type="button" class="prediction-topic-filter" data-topic="culture">🎭 CULTURE</button>
      <button type="button" class="prediction-topic-filter" data-topic="other">• OTHER</button>
    </div>'''
if 'id="predictionTimeFilters"' not in s:s=s.replace(needle,time+'\n'+topic+'\n'+needle,1)
elif 'id="predictionTopicFilters"' not in s:s=s.replace('</div>\n    <div class="prediction-list" id="predictionList">','</div>\n'+topic+'\n    <div class="prediction-list" id="predictionList">',1)
if 'data-filter="resolved"' not in s:
 longbtn='      <button type="button" class="prediction-time-filter" data-filter="long">🔮 LONG TERM <span id="count-long">0</span></button>';s=s.replace(longbtn,longbtn+'\n      <button type="button" class="prediction-time-filter" data-filter="resolved">✅ RESOLVED <span id="count-resolved">0</span></button>',1)
style='''<style id="certainu-filter-enhancements">
.prediction-time-filters,.prediction-topic-filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.prediction-time-filters{margin:0 0 10px}.prediction-topic-filters{margin:0 0 20px;padding-top:2px}.prediction-time-filter,.prediction-topic-filter{border:1px solid rgba(255,255,255,.22);background:rgba(7,24,79,.25);color:rgba(255,255,255,.82);border-radius:999px;padding:10px 13px;font-size:9px;font-weight:900;letter-spacing:.06em;cursor:pointer;transition:.18s ease}.prediction-topic-filter{padding:8px 12px;font-size:8px;background:rgba(7,24,79,.16)}.prediction-time-filter:hover,.prediction-topic-filter:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-1px)}.prediction-time-filter.active,.prediction-topic-filter.active{background:#fff;color:#1747df;border-color:#fff;box-shadow:0 8px 20px rgba(4,18,76,.16)}.prediction-time-filter span{opacity:.7;margin-left:4px}.prediction-filter-label{font-size:8px;font-weight:900;letter-spacing:.16em;color:rgba(255,255,255,.55);margin-right:2px}
.certainu-confidence-pill,.confidence-pill,.confidence-scale span,.confidence-legend span,.certainty-scale span,.certainty-legend span{display:inline-flex!important;align-items:center;justify-content:center;min-height:42px;padding:11px 18px!important;border:2px solid rgba(255,255,255,.42)!important;border-radius:999px!important;background:rgba(13,54,178,.52)!important;color:#fff!important;font-size:12px!important;font-weight:900!important;line-height:1.1!important;letter-spacing:.035em!important;box-shadow:0 5px 14px rgba(5,24,100,.18),inset 0 1px 0 rgba(255,255,255,.08)!important}.confidence-scale,.confidence-legend,.certainty-scale,.certainty-legend{gap:12px!important;align-items:center!important;flex-wrap:wrap!important}@media(max-width:600px){.prediction-time-filters,.prediction-topic-filters{gap:6px}.prediction-time-filter{padding:9px 10px;font-size:8px}.prediction-topic-filter{padding:7px 9px;font-size:7px}.certainu-confidence-pill,.confidence-pill,.confidence-scale span,.confidence-legend span,.certainty-scale span,.certainty-legend span{min-height:38px;padding:9px 13px!important;font-size:10px!important}}
</style>'''
if 'id="certainu-filter-enhancements"' not in s:s=s.replace('</head>',style+'\n</head>',1)
old="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||''};";new="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||'', market_end_date:p.market_end_date||p.end_date||p.endDate||p.resolution_date||'', category:p.category||''};";s=s.replace(old,new,1)
# Replace the earlier category renderer/filter block if present; otherwise replace original list render.
start=s.find('  function resolutionBucket(raw){')
end=s.find('\n  predictionList.classList.toggle(\'prediction-list-collapsed\'',start) if start!=-1 else -1
block='''  function resolutionBucket(raw){const p=normalizePrediction(raw);if(['won','lost','void','resolved'].includes(p.status)||p.resolved_at)return 'resolved';const end=Date.parse(p.market_end_date||'');if(!end)return 'long';const h=(end-Date.now())/3600000;if(h<=24)return 'quick';if(h<=72)return 'short';if(h<=168)return 'week';return 'long';}
  function topicBucket(raw){const p=normalizePrediction(raw),saved=String(p.category||'').toLowerCase();if(['crypto','politics','geopolitics','sports','economy','culture','other'].includes(saved))return saved;const t=((p.question||'')+' '+(p.slug||'')).toLowerCase();if(/bitcoin|\bbtc\b|ethereum|\beth\b|solana|\bsol\b|crypto|dogecoin|\bdoge\b|xrp|ripple|cardano|chainlink|bnb|avalanche|sui|memecoin/.test(t))return 'crypto';if(/war|strike|attack|iran|israel|russia|ukraine|china|taiwan|nato|military|ceasefire|invasion|country|countries/.test(t))return 'geopolitics';if(/president|election|congress|senate|house|governor|democrat|republican|trump|vance|cabinet|primary|nominee|vote/.test(t))return 'politics';if(/nfl|nba|mlb|nhl|soccer|football|basketball|baseball|hockey|tennis|ufc|f1|formula 1|super bowl|world cup|championship|playoffs/.test(t))return 'sports';if(/fed|interest rate|inflation|gdp|recession|unemployment|jobs report|cpi|economy|tariff|stock market|s&p|nasdaq/.test(t))return 'economy';if(/movie|film|oscar|grammy|album|song|celebrity|box office|tv|television|streaming|award/.test(t))return 'culture';return 'other';}
  const bucketCounts={all:predictions.length,quick:0,short:0,week:0,long:0,resolved:0};predictions.forEach(p=>bucketCounts[resolutionBucket(p)]++);
  predictionList.innerHTML=predictions.map(p=>renderPrediction(p).replace('<article class="prediction-card','<article data-resolution-bucket="'+resolutionBucket(p)+'" data-topic-bucket="'+topicBucket(p)+'" class="prediction-card')).join('')||'<article class="prediction-card"><h3>No official calls yet.</h3></article>';
  Object.entries(bucketCounts).forEach(([k,v])=>{const el=document.getElementById('count-'+k);if(el)el.textContent=v;});
  let activeTime='all',activeTopic='all';
  function applyPredictionFilters(){predictionList.querySelectorAll('.prediction-card').forEach(card=>{card.style.display=((activeTime==='all'||card.dataset.resolutionBucket===activeTime)&&(activeTopic==='all'||card.dataset.topicBucket===activeTopic))?'':'none';});const visible=[...predictionList.querySelectorAll('.prediction-card')].filter(c=>c.style.display!=='none');const collapse=visible.length>3;predictionList.classList.toggle('prediction-list-collapsed',collapse);if(expandBtn){expandBtn.hidden=!collapse;expandBtn.setAttribute('aria-expanded',collapse?'false':'true');}const label=document.getElementById('predictionExpandLabel');if(label){label.hidden=!collapse;label.textContent='SHOW MORE';}}
  const timeBar=document.getElementById('predictionTimeFilters');if(timeBar)timeBar.onclick=e=>{const b=e.target.closest('.prediction-time-filter');if(!b)return;activeTime=b.dataset.filter;timeBar.querySelectorAll('.prediction-time-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
  const topicBar=document.getElementById('predictionTopicFilters');if(topicBar)topicBar.onclick=e=>{const b=e.target.closest('.prediction-topic-filter');if(!b)return;activeTopic=b.dataset.topic;topicBar.querySelectorAll('.prediction-topic-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
'''
if start!=-1 and end!=-1:s=s[:start]+block+s[end:]
else:
 oldrender="  predictionList.innerHTML=\n    predictions.map(renderPrediction).join('') ||\n    '<article class=\"prediction-card\"><h3>No official calls yet.</h3></article>';\n"
 if oldrender in s:s=s.replace(oldrender,block,1)
P.write_text(s,encoding='utf-8');print('CERTAINUTIES time + topic filters, collapse behavior, hourly banner, confidence styling patched')
