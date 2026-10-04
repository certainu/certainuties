#!/usr/bin/env python3
from pathlib import Path
import re

P=Path(__file__).resolve().parents[1]/"index.html"
s=P.read_text(encoding="utf-8")
s=s.replace('AUTO-REFRESH ≈ EVERY 2 HOURS','AUTO-REFRESH ≈ EVERY HOUR').replace('AUTO-REFRESH ≈ EVERY 30 MINUTES','AUTO-REFRESH ≈ EVERY HOUR')

needle='<div class="prediction-list" id="predictionList">'
time='''<div class="prediction-time-filters reveal" id="predictionTimeFilters" aria-label="Filter predictions by resolution time">
<button type="button" class="prediction-time-filter active" data-filter="all">ALL</button>
<button type="button" class="prediction-time-filter" data-filter="quick">⚡ QUICK ≤24H</button>
<button type="button" class="prediction-time-filter" data-filter="short">🔥 SHORT 1–3D</button>
<button type="button" class="prediction-time-filter" data-filter="week">🎯 THIS WEEK</button>
<button type="button" class="prediction-time-filter" data-filter="long">⌛ LONG TERM</button>
<button type="button" class="prediction-time-filter" data-filter="resolved">✅ RESOLVED</button>
</div>'''
topic='''<div class="prediction-topic-filters reveal" id="predictionTopicFilters" aria-label="Filter predictions by topic">
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

s=re.sub(r'<div class="prediction-time-filters[^>]*id="predictionTimeFilters"[\s\S]*?</div>','',s,count=1)
s=re.sub(r'<div class="prediction-topic-filters[^>]*id="predictionTopicFilters"[\s\S]*?</div>','',s,count=1)
if needle not in s: raise SystemExit('ERROR: predictionList anchor not found')
s=s.replace(needle,time+'\n'+topic+'\n'+needle,1)

style='''<style id="certainu-filter-enhancements">
.prediction-time-filters,.prediction-topic-filters{display:flex!important;gap:11px;flex-wrap:wrap;align-items:center;visibility:visible!important;opacity:1!important}.prediction-time-filters{margin:0 0 14px}.prediction-topic-filters{margin:0 0 26px;padding-top:3px}.prediction-time-filter,.prediction-topic-filter{border:1.5px solid rgba(255,255,255,.26);background:rgba(7,24,79,.25);color:rgba(255,255,255,.88);border-radius:999px;padding:14px 18px;font-size:13px;font-weight:900;letter-spacing:.06em;cursor:pointer;transition:.18s ease;min-height:46px}.prediction-topic-filter{padding:11px 17px;font-size:11px;min-height:42px;background:rgba(7,24,79,.16)}.prediction-time-filter:hover,.prediction-topic-filter:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-1px)}.prediction-time-filter.active,.prediction-topic-filter.active{background:#fff;color:#1747df;border-color:#fff;box-shadow:0 9px 24px rgba(4,18,76,.2)}.prediction-filter-label{font-size:11px;font-weight:900;letter-spacing:.16em;color:rgba(255,255,255,.68);margin-right:3px}@media(max-width:600px){.prediction-time-filters,.prediction-topic-filters{gap:8px}.prediction-time-filter{padding:11px 14px;font-size:10px;min-height:40px}.prediction-topic-filter{padding:9px 12px;font-size:9px;min-height:36px}.prediction-filter-label{font-size:9px}}
</style>'''
s=re.sub(r'<style id="certainu-filter-enhancements">[\s\S]*?</style>',style,s,count=1)
if 'id="certainu-filter-enhancements"' not in s:
 if '</head>' not in s: raise SystemExit('ERROR: </head> not found')
 s=s.replace('</head>',style+'\n</head>',1)

old="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||''};"
new="    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||'', market_end_date:p.market_end_date||p.end_date||p.endDate||p.resolution_date||'', category:p.category||''};"
s=s.replace(old,new,1)

# Deterministically replace the prediction render/filter section on EVERY run.
# This prevents stale ALL-filter logic from surviving older patches.
start=s.find('  function resolutionBucket(raw){')
end=s.find("\n  predictionList.classList.toggle('prediction-list-collapsed'",start) if start!=-1 else -1
if start==-1 or end==-1:
 raise SystemExit('ERROR: could not locate existing prediction filter block')
block='''  function resolutionBucket(raw){const p=normalizePrediction(raw);const st=String(p.status||'').toLowerCase();if(['won','lost','void','resolved'].includes(st)||p.resolved_at)return 'resolved';const end=Date.parse(p.market_end_date||'');if(!end)return 'long';const h=(end-Date.now())/3600000;if(h<=24)return 'quick';if(h<=72)return 'short';if(h<=168)return 'week';return 'long';}
  function topicBucket(raw){const p=normalizePrediction(raw),saved=String(p.category||'').toLowerCase();if(['crypto','politics','geopolitics','sports','economy','culture','other'].includes(saved))return saved;const t=((p.question||'')+' '+(p.slug||'')).toLowerCase();if(/bitcoin|\\bbtc\\b|ethereum|\\beth\\b|solana|\\bsol\\b|crypto|dogecoin|\\bdoge\\b|xrp|ripple|cardano|chainlink|bnb|avalanche|sui|memecoin/.test(t))return 'crypto';if(/war|strike|attack|iran|israel|russia|ukraine|china|taiwan|nato|military|ceasefire|invasion|country|countries/.test(t))return 'geopolitics';if(/president|election|congress|senate|house|governor|democrat|republican|trump|vance|cabinet|primary|nominee|vote/.test(t))return 'politics';if(/nfl|nba|mlb|nhl|soccer|football|basketball|baseball|hockey|tennis|ufc|f1|formula 1|super bowl|world cup|championship|playoffs/.test(t))return 'sports';if(/fed|interest rate|inflation|gdp|recession|unemployment|jobs report|cpi|economy|tariff|stock market|s&p|nasdaq/.test(t))return 'economy';if(/movie|film|oscar|grammy|album|song|celebrity|box office|tv|television|streaming|award/.test(t))return 'culture';return 'other';}
  predictionList.innerHTML=predictions.map(p=>renderPrediction(p).replace('<article class="prediction-card','<article data-resolution-bucket="'+resolutionBucket(p)+'" data-topic-bucket="'+topicBucket(p)+'" class="prediction-card')).join('')||'<article class="prediction-card"><h3>No official calls yet.</h3></article>';
  let activeTime='all',activeTopic='all';
  function applyPredictionFilters(){predictionList.querySelectorAll('.prediction-card').forEach(card=>{const bucket=card.dataset.resolutionBucket;const timeMatch=activeTime==='all' ? bucket!=='resolved' : bucket===activeTime;const topicMatch=activeTopic==='all'||card.dataset.topicBucket===activeTopic;card.style.display=(timeMatch&&topicMatch)?'':'none';});const visible=[...predictionList.querySelectorAll('.prediction-card')].filter(c=>c.style.display!=='none');const collapse=visible.length>3;predictionList.classList.toggle('prediction-list-collapsed',collapse);if(expandBtn){expandBtn.hidden=!collapse;expandBtn.setAttribute('aria-expanded',collapse?'false':'true');}const label=document.getElementById('predictionExpandLabel');if(label){label.hidden=!collapse;label.textContent='SHOW MORE';}}
  const timeBar=document.getElementById('predictionTimeFilters');if(timeBar)timeBar.onclick=e=>{const b=e.target.closest('.prediction-time-filter');if(!b)return;activeTime=b.dataset.filter;timeBar.querySelectorAll('.prediction-time-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
  const topicBar=document.getElementById('predictionTopicFilters');if(topicBar)topicBar.onclick=e=>{const b=e.target.closest('.prediction-topic-filter');if(!b)return;activeTopic=b.dataset.topic;topicBar.querySelectorAll('.prediction-topic-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
  applyPredictionFilters();
'''
s=s[:start]+block+s[end:]

# Verify the production behavior is present before writing.
required=["activeTime==='all' ? bucket!=='resolved' : bucket===activeTime",'applyPredictionFilters();','data-filter="resolved"']
missing=[x for x in required if x not in s]
if missing: raise SystemExit('ERROR: deterministic filter verification failed: '+', '.join(missing))
P.write_text(s,encoding='utf-8')
print('CERTAINUTIES deterministic filtering patched: ALL=open only; RESOLVED=resolved only')
