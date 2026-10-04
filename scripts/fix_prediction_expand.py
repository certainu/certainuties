#!/usr/bin/env python3
from pathlib import Path
import re

P=Path(__file__).resolve().parents[1]/'index.html'
s=P.read_text(encoding='utf-8')

# Remove any previous copy so this patch is safe to run every hour.
s=re.sub(r'<style id="certainu-prediction-expand-fix">[\s\S]*?</style>','',s)
s=re.sub(r'<script id="certainu-prediction-expand-fix-js">[\s\S]*?</script>','',s)

style='''<style id="certainu-prediction-expand-fix">
#certainuPredictionExpandWrap{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;margin:18px auto 8px;position:relative;z-index:5}
#certainuPredictionExpandWrap[hidden]{display:none!important}
#certainuPredictionExpandWrap .prediction-expand-label{position:static!important;margin:0!important;transform:none!important}
#certainuPredictionExpandWrap button{position:static!important;margin:0!important;transform:none!important}
</style>'''

js='''<script id="certainu-prediction-expand-fix-js">
(function(){
  function initCertainuPredictionExpand(){
    const list=document.getElementById('predictionList');
    if(!list)return;

    let label=document.getElementById('predictionExpandLabel');
    let btn=document.querySelector('[aria-controls="predictionList"]') || document.getElementById('predictionExpandBtn') || document.querySelector('.prediction-expand-btn');
    if(!btn && label){
      const candidates=[label.previousElementSibling,label.nextElementSibling,label.parentElement&&label.parentElement.querySelector('button')];
      btn=candidates.find(x=>x&&x.tagName==='BUTTON')||null;
    }

    let wrap=document.getElementById('certainuPredictionExpandWrap');
    if(!wrap){wrap=document.createElement('div');wrap.id='certainuPredictionExpandWrap';list.insertAdjacentElement('afterend',wrap);}
    else if(wrap.previousElementSibling!==list){list.insertAdjacentElement('afterend',wrap);}

    if(label){label.classList.add('prediction-expand-label');wrap.appendChild(label);}
    if(btn)wrap.appendChild(btn);

    let expanded=false;
    function matches(card){
      const time=document.querySelector('#predictionTimeFilters .prediction-time-filter.active')?.dataset.filter||'all';
      const topic=document.querySelector('#predictionTopicFilters .prediction-topic-filter.active')?.dataset.topic||'all';
      return (time==='all'||card.dataset.resolutionBucket===time)&&(topic==='all'||card.dataset.topicBucket===topic);
    }
    function refresh(){
      const cards=[...list.querySelectorAll('.prediction-card')];
      const matched=cards.filter(matches);
      cards.forEach(c=>c.style.display='none');
      matched.forEach((c,i)=>{c.style.display=(expanded||i<3)?'':'none';});
      list.classList.remove('prediction-list-collapsed');
      const needs=matched.length>3;
      wrap.hidden=!needs;
      if(label){label.hidden=!needs;label.textContent=expanded?'SHOW LESS':'SHOW MORE';}
      if(btn){btn.hidden=!needs;btn.setAttribute('aria-expanded',expanded?'true':'false');}
    }

    if(btn){
      btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();expanded=!expanded;refresh();},{capture:true});
    }
    if(label){
      label.style.cursor='pointer';
      label.addEventListener('click',function(e){e.preventDefault();expanded=!expanded;refresh();});
    }
    document.getElementById('predictionTimeFilters')?.addEventListener('click',()=>{expanded=false;setTimeout(refresh,0);});
    document.getElementById('predictionTopicFilters')?.addEventListener('click',()=>{expanded=false;setTimeout(refresh,0);});
    new MutationObserver(()=>setTimeout(refresh,0)).observe(list,{childList:true});
    refresh();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initCertainuPredictionExpand);else initCertainuPredictionExpand();
})();
</script>'''

if '</head>' in s:s=s.replace('</head>',style+'\n</head>',1)
else:raise SystemExit('ERROR: </head> not found')
if '</body>' in s:s=s.replace('</body>',js+'\n</body>',1)
else:raise SystemExit('ERROR: </body> not found')
P.write_text(s,encoding='utf-8')
print('Prediction list fixed: max 3 cards collapsed; Show More anchored directly below list.')
