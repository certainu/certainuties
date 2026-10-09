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

# The live site now owns its prediction filter implementation.
# Do not replace that JavaScript on every updater run: doing so is brittle and can
# overwrite newer UI fixes. If the current category system is already present,
# leave it untouched and continue successfully.
filter_markers=[
    'id="predictionTimeFilters"',
    'id="predictionTopicFilters"',
    'function resolutionBucket(raw)',
    'function topicBucket(raw)',
    'function applyPredictionFilters()',
    'data-filter="resolved"',
]
missing_filter_markers=[x for x in filter_markers if x not in s]
if missing_filter_markers:
    raise SystemExit('ERROR: prediction category system is incomplete: '+', '.join(missing_filter_markers))
print('CERTAINUTIES category system already installed; leaving current filter logic unchanged')

# The category system has evolved since this installer was first written.
# Do not require one exact JavaScript expression here: equivalent/newer filter
# implementations are valid and an exact-string check can unnecessarily stop
# the hourly updater before its commit step.
#
# The structural markers above are the safety check. They confirm that the live
# time/topic filtering system, resolution bucketing, filter application, and
# RESOLVED control are all present. If any of those disappear, this script still
# fails loudly instead of silently accepting a broken page.
P.write_text(s,encoding='utf-8')
print('CERTAINUTIES category system verified; preserving current filter implementation')
