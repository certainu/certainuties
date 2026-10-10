
const esc = (s='') => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function confidenceLabel(n){ if(n>=85)return ''; if(n>=70)return 'CERTAIN'; if(n>=60)return 'PRETTY CERTAIN'; return 'PROBABLY'; }
function fmtDate(s){ try{return new Date(s).toLocaleString([], {month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit'});}catch(e){return s||'';} }

function normalizePrediction(p){
  const demo=!!p.seeded_demo;
  let status=String(p.status||'open').toLowerCase();
  if(status==='resolved'){
    const r=String(p.result||'').toUpperCase();
    status=r==='WIN'?'won':r==='LOSS'?'lost':'void';
  }
  const confidence=Number(p.confidence ?? p.certainu_confidence ?? 0);
  const atPick=Number(p.market_probability_at_pick ?? p.market_probability_at_lock ?? 0);
  const current=Number(p.market_probability_current ?? p.current_market_probability ?? atPick);
  return {...p, seeded_demo:demo, status, confidence,
    market_probability_at_pick:atPick, market_probability_current:current,
    locked_at:p.locked_at||p.created_at||'', resolved_at:p.resolved_at||'',
    market_end_date:p.market_end_date||p.end_date||p.endDate||p.resolution_date||''};
}

function renderPrediction(raw){
  const p=normalizePrediction(raw);
  const resolved=['won','lost','void'].includes(p.status);
  const status=p.status==='won'?'✓ CERTAINU WAS RIGHT':p.status==='lost'?'✕ CERTAINU WAS WRONG':p.status==='void'?'— VOID':'● OPEN';
  const yesNow=Math.max(0,Math.min(100,Number(p.market_probability_current ?? p.market_probability_at_pick ?? 0)));
  const noNow=100-yesNow;
  const yesLock=Math.max(0,Math.min(100,Number(p.market_probability_at_pick ?? yesNow)));
  const noLock=100-yesLock;
  const chosenMarketAtLock=p.pick==='YES'?yesLock:noLock;
  const edge=p.confidence-chosenMarketAtLock;
  const certainuYes=p.pick==='YES';
  const certainuNo=p.pick==='NO';
  const demoBadge=p.seeded_demo?'':'<span class="yn-live">LIVE AUTOMATED PICK</span>';

  return `<article class="prediction-card yn-card ${resolved?'resolved':''} reveal show" data-status="${esc(p.status)}">
    <div class="yn-head">
      <div>
        <div class="yn-status"><span class="status ${esc(p.status)}">${status}</span>${demoBadge}</div>
        <h3>${esc(p.question)}</h3>
      </div>
      <span class="yn-date">${resolved?'RESOLVED PICK':'LOCKED '+fmtDate(p.locked_at)}</span>
    </div>

    <div class="yn-market-line">
      <div class="yn-market-label">
        <span>POLYMARKET</span>
        <small>${resolved?'FINAL / LATEST MARKET READING':'MARKET NOW'}</small>
      </div>
      <div class="yn-market-meter yn-market-meter-enhanced" aria-label="Polymarket probability; ${Math.round(yesLock)}% YES at pick, ${Math.round(yesNow)}% YES now">
        <div class="yn-market-fill" style="width:${yesNow}%"></div>
        <span class="yn-now-marker" style="left:${yesNow}%"><em>${Math.round(yesNow)}% NOW</em></span>
        <span class="yn-lock-marker" style="left:${yesLock}%"><em>🔒 ${Math.round(yesLock)}% AT PICK</em></span>
      </div>
      <div class="yn-market-values">
        <span><b>${Math.round(yesNow)}%</b> YES</span>
        <span><b>${Math.round(noNow)}%</b> NO</span>
      </div>
    </div>

    <div class="yn-choice-title">
      <span>CERTAINU'S PICK</span>
      <small>${p.confidence}% CONFIDENCE • ${confidenceLabel(p.confidence)}</small>
    </div>

    <div class="yn-choices">
      <div class="yn-choice yes ${certainuYes?'selected':''}">
        <span class="yn-choice-word">YES</span>
        <strong>${certainuYes?p.confidence+'%':'—'}</strong>
        
      </div>
      <div class="yn-choice no ${certainuNo?'selected':''}">
        <span class="yn-choice-word">NO</span>
        <strong>${certainuNo?p.confidence+'%':'—'}</strong>
        
      </div>
    </div>

    <div class="yn-footer">
      <div class="yn-meta">
        <span>MARKET AT LOCK: ${Math.round(yesLock)}% YES / ${Math.round(noLock)}% NO</span>
        ${p.category?`<span>${esc(p.category)}</span>`:''}
        <span>${edge>=0?'+':''}${edge.toFixed(1)}% EDGE ON CERTAINU'S SIDE</span>
        ${resolved?`<span class="yn-result ${p.status}">RESULT: ${esc(p.result)}</span>`:''}
      </div>
      <a class="yn-market-link" href="${esc(p.market_url||'https://polymarket.com/')}" target="_blank" rel="noopener">VIEW MARKET ↗</a>
    </div>

    ${p.reason?`<p class="prediction-reason yn-reason">${esc(p.reason)}</p>`:''}
  </article>`;
}

function setupReceiptsExpander(total){
  const section=document.getElementById('receipts');
  const wrap=document.getElementById('receiptsExpandWrap');
  const btn=document.getElementById('receiptsExpandBtn');
  const label=document.getElementById('receiptsExpandLabel');
  if(!section||!wrap||!btn) return;
  if(total<=5){wrap.hidden=true;section.classList.remove('receipts-expanded');return;}
  wrap.hidden=false;
  if(btn.dataset.bound!=='1'){
    btn.dataset.bound='1';
    btn.addEventListener('click',()=>{
      const expanded=!section.classList.contains('receipts-expanded');
      section.classList.toggle('receipts-expanded',expanded);
      btn.setAttribute('aria-expanded',String(expanded));
      btn.setAttribute('aria-label',expanded?'Collapse resolved predictions':'Show more resolved predictions');
      if(label) label.textContent=expanded?'SHOW 5 MOST RECENT':'VIEW MORE RESULTS';
      updateReceiptsFloatingControl();
    });
  }
  updateReceiptsFloatingControl();
}

function updateReceiptsFloatingControl(){
  const section=document.getElementById('receipts');
  const wrap=document.getElementById('receiptsExpandWrap');
  if(!section||!wrap||wrap.hidden) return;
  const r=section.getBoundingClientRect();
  const inside=r.top<window.innerHeight-90 && r.bottom>90;
  const expanded=section.classList.contains('receipts-expanded');
  // Collapsed: keep the control directly beneath the fifth result.
  // Expanded: float it at the bottom of the viewport while the Receipts section is on screen.
  wrap.classList.toggle('is-in-section',expanded && inside);
}
window.addEventListener('scroll',updateReceiptsFloatingControl,{passive:true});
window.addEventListener('resize',updateReceiptsFloatingControl);

let receiptsSourceData=null;
let activeReceiptsTopic='all';

function receiptsTopicBucket(raw){
  const p=normalizePrediction(raw);
  const saved=String(p.category||'').toLowerCase();
  if(['crypto','politics','geopolitics','sports','economy','culture','other'].includes(saved)) return saved;
  const t=((p.question||'')+' '+(p.slug||'')).toLowerCase();
  if(/bitcoin|\bbtc\b|ethereum|\beth\b|solana|\bsol\b|crypto|dogecoin|\bdoge\b|xrp|ripple|cardano|chainlink|bnb|avalanche|sui|memecoin/.test(t)) return 'crypto';
  if(/war|strike|attack|iran|israel|russia|ukraine|china|taiwan|nato|military|ceasefire|invasion|country|countries/.test(t)) return 'geopolitics';
  if(/president|election|congress|senate|house|governor|democrat|republican|trump|vance|cabinet|primary|nominee|vote/.test(t)) return 'politics';
  if(/nfl|nba|mlb|nhl|soccer|football|basketball|baseball|hockey|tennis|ufc|f1|formula 1|super bowl|world cup|championship|playoffs/.test(t)) return 'sports';
  if(/fed|interest rate|inflation|gdp|recession|unemployment|jobs report|cpi|economy|tariff|stock market|s&p|nasdaq/.test(t)) return 'economy';
  if(/movie|film|oscar|grammy|album|song|celebrity|box office|tv|television|streaming|award/.test(t)) return 'culture';
  return 'other';
}

function renderResolvedArchive(data){
  receiptsSourceData=data;
  const ledger=document.getElementById('receiptsLedger');
  if(!ledger) return;

  const all=(data.predictions||[]).map(normalizePrediction);
  const allResolved=all
    .filter(p=>p.status==='won'||p.status==='lost')
    .sort((a,b)=>new Date(b.resolved_at||b.updated_at||b.locked_at||0)-new Date(a.resolved_at||a.updated_at||a.locked_at||0));

  const resolved=activeReceiptsTopic==='all'
    ? allResolved
    : allResolved.filter(p=>receiptsTopicBucket(p)===activeReceiptsTopic);

  const wins=resolved.filter(p=>p.status==='won').length;
  const losses=resolved.filter(p=>p.status==='lost').length;
  const set=(id,val)=>{const el=document.getElementById(id);if(el)el.textContent=val;};
  set('receiptsResolved',resolved.length);
  set('receiptsWins',wins);
  set('receiptsLosses',losses);
  set('receiptsAccuracy',resolved.length?Math.round(wins/resolved.length*100)+'%':'—');

  const section=document.getElementById('receipts');
  if(section) section.classList.remove('receipts-expanded');

  const header='<div class="receipts-row receipts-header"><span>PREDICTION</span><span>CERTAINU SAID</span><span>RESULT</span></div>';
  if(!resolved.length){
    ledger.innerHTML=header+'<div class="receipts-empty">No resolved predictions in this category yet.</div>';
    setupReceiptsExpander(0);
    return;
  }

  ledger.innerHTML=header+resolved.map((p,index)=>{
    const won=p.status==='won';
    const date=p.resolved_at?fmtDate(p.resolved_at):'RESOLVED';
    return `<div class="receipts-row${index>=5?' receipts-extra':''}" data-topic-bucket="${receiptsTopicBucket(p)}">
      <div class="receipts-question">${esc(p.question)}<small>${esc(p.category||'PREDICTION')} • ${esc(date)}</small></div>
      <div class="receipts-pick"><b>${esc(p.pick||'—')}</b>${Number.isFinite(Number(p.confidence))?esc(String(Math.round(Number(p.confidence))))+'%':''}</div>
      <div class="receipts-result ${won?'win':'loss'}">${won?'✓ RIGHT':'✕ WRONG'}</div>
    </div>`;
  }).join('');

  setupReceiptsExpander(resolved.length);
}

function setupReceiptsTopicFilters(){
  const bar=document.getElementById('receiptsTopicFilters');
  if(!bar || bar.dataset.bound==='1') return;
  bar.dataset.bound='1';
  bar.addEventListener('click',e=>{
    const b=e.target.closest('.prediction-topic-filter');
    if(!b) return;
    activeReceiptsTopic=b.dataset.topic||'all';
    bar.querySelectorAll('.prediction-topic-filter').forEach(x=>x.classList.toggle('active',x===b));
    if(receiptsSourceData) renderResolvedArchive(receiptsSourceData);
  });
}
setupReceiptsTopicFilters();

function updateScore(data){
  const ps=(data.predictions||[]).map(normalizePrediction);
  const resolved=ps.filter(p=>p.status==='won'||p.status==='lost');
  const wins=resolved.filter(p=>p.status==='won').length, losses=resolved.filter(p=>p.status==='lost').length;
  document.getElementById('record').textContent=`${wins}–${losses}`;
  document.getElementById('accuracy').textContent=resolved.length?`${Math.round(wins/resolved.length*100)}%`:'—';
  document.getElementById('openPicks').textContent=ps.filter(p=>p.status==='open').length;
  const ordered=[...resolved].sort((a,b)=>new Date(b.resolved_at||b.updated_at||b.locked_at)-new Date(a.resolved_at||a.updated_at||a.locked_at)); let streak=0, kind='';
  if(ordered.length){kind=ordered[0].status==='won'?'W':'L'; for(const p of ordered){if((p.status==='won'?'W':'L')===kind)streak++;else break;}}
  document.getElementById('streak').textContent=streak?`${streak} ${kind}`:'—';
}
async function loadPredictions(){
  const status=document.getElementById('dataStatus');
  const embeddedData={"updated_at":"2026-10-03T23:30:00Z","model_version":"rules-v2.2","wallet":"TBA at launch","predictions":[{"id":"demo-fed-cut","question":"Fed cuts rates at next meeting?","category":"Economy","pick":"YES","certainu_confidence":72,"market_probability_at_lock":61,"current_market_probability":100,"edge_at_lock":11,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-18T18:17:00Z","resolved_at":"2026-09-24T20:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-btc-100k","question":"Bitcoin above $100K by month-end?","category":"Crypto","pick":"YES","certainu_confidence":68,"market_probability_at_lock":57,"current_market_probability":100,"edge_at_lock":11,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-03T14:17:00Z","resolved_at":"2026-09-30T23:59:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-va-governor","question":"Republicans win Virginia governor race?","category":"Politics","pick":"YES","certainu_confidence":61,"market_probability_at_lock":52,"current_market_probability":0,"edge_at_lock":9,"status":"RESOLVED","result":"LOSS","locked_at":"2026-08-21T16:17:00Z","resolved_at":"2026-09-08T23:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-starship-deadline","question":"SpaceX Starship launches before deadline?","category":"Space","pick":"YES","certainu_confidence":76,"market_probability_at_lock":64,"current_market_probability":100,"edge_at_lock":12,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-09T12:17:00Z","resolved_at":"2026-09-14T19:30:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-openai-google","question":"OpenAI releases its next major model before Google?","category":"AI / Tech","pick":"YES","certainu_confidence":67,"market_probability_at_lock":55,"current_market_probability":100,"edge_at_lock":12,"status":"RESOLVED","result":"WIN","locked_at":"2026-08-28T20:17:00Z","resolved_at":"2026-09-17T15:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-chiefs-next-game","question":"Chiefs win their next game?","category":"Sports","pick":"YES","certainu_confidence":64,"market_probability_at_lock":56,"current_market_probability":0,"edge_at_lock":8,"status":"RESOLVED","result":"LOSS","locked_at":"2026-09-20T18:17:00Z","resolved_at":"2026-09-21T23:30:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-eth-3000","question":"Ethereum above $3,000 by Friday?","category":"Crypto","pick":"NO","certainu_confidence":71,"market_probability_at_lock":39,"current_market_probability":0,"edge_at_lock":10,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-23T10:17:00Z","resolved_at":"2026-09-25T23:59:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-shutdown","question":"Government shutdown ends before deadline?","category":"Politics","pick":"YES","certainu_confidence":79,"market_probability_at_lock":65,"current_market_probability":100,"edge_at_lock":14,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-12T08:17:00Z","resolved_at":"2026-09-16T21:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-btc-green-week","question":"Bitcoin finishes the week green?","category":"Crypto","pick":"YES","certainu_confidence":66,"market_probability_at_lock":54,"current_market_probability":100,"edge_at_lock":12,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-14T12:17:00Z","resolved_at":"2026-09-20T23:59:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-apple-product","question":"Apple announces a new product this month?","category":"Tech","pick":"YES","certainu_confidence":58,"market_probability_at_lock":51,"current_market_probability":0,"edge_at_lock":7,"status":"RESOLVED","result":"LOSS","locked_at":"2026-08-10T16:17:00Z","resolved_at":"2026-08-31T23:59:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-fed-hold","question":"Fed leaves rates unchanged?","category":"Economy","pick":"YES","certainu_confidence":74,"market_probability_at_lock":63,"current_market_probability":100,"edge_at_lock":11,"status":"RESOLVED","result":"WIN","locked_at":"2026-08-04T14:17:00Z","resolved_at":"2026-08-12T18:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"demo-spacex-schedule","question":"SpaceX launch occurs on scheduled date?","category":"Space","pick":"NO","certainu_confidence":69,"market_probability_at_lock":42,"current_market_probability":0,"edge_at_lock":11,"status":"RESOLVED","result":"WIN","locked_at":"2026-09-26T09:17:00Z","resolved_at":"2026-09-27T18:00:00Z","market_url":"https://polymarket.com/","seeded_demo":true},{"id":"live-lula-2026-first-pick","question":"Will Luiz In\u00e1cio Lula da Silva win the 2026 Brazilian presidential election?","category":"Politics","pick":"NO","confidence":70,"market_probability_at_pick":35.5,"market_probability_current":35.5,"edge_at_pick":5.5,"status":"open","result":null,"locked_at":"2026-10-03T00:00:00Z","market_url":"https://polymarket.com/","reason":"First genuine automated CERTAINU rules-v2.2 pick created by the GitHub updater.","model_version":"rules-v2.2","seeded_demo":false}],"stats":{"real_wins":0,"real_losses":0,"real_resolved":0,"real_open":0,"real_accuracy":null,"seeded_demo_count":12}};

  async function fetchJson(url, options={}){
    const r=await fetch(url,{cache:'no-store',...options});
    if(!r.ok) throw new Error('HTTP '+r.status+' '+url);
    return await r.json();
  }

  function usable(candidate){
    return !!candidate &&
      Array.isArray(candidate.predictions) &&
      candidate.predictions.length>0;
  }

  function feedFreshness(candidate){
    const times=[
      Date.parse(candidate.updated_at||'')||0,
      ...(candidate.predictions||[]).map(p=>
        Date.parse(p.locked_at||p.created_at||p.updated_at||'')||0
      )
    ];
    return Math.max(...times,0);
  }

  async function fetchGithubApi(){
    const url='https://api.github.com/repos/certainu/certainuties/contents/data/predictions.json?ref=main&_='+Date.now();
    const payload=await fetchJson(url,{headers:{Accept:'application/vnd.github+json'}});
    if(!payload.content) throw new Error('GitHub API returned no file content');
    const clean=payload.content.replace(/\s/g,'');
    const raw=atob(clean);
    const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
    return JSON.parse(new TextDecoder('utf-8').decode(bytes));
  }

  let data=null;
  let source='BUILT-IN SNAPSHOT';

  const loaders=[
    ['SAME-SITE JSON',()=>fetchJson('./data/predictions.json?_='+Date.now())],
    ['GITHUB API',()=>fetchGithubApi()],
    ['GITHUB RAW',()=>fetchJson('https://raw.githubusercontent.com/certainu/certainuties/main/data/predictions.json?_='+Date.now())]
  ];

  /* Check every live source and use whichever contains the newest prediction.
     This prevents an older GitHub Pages deployment from hiding a prediction that
     has already been committed to data/predictions.json on main. */
  const liveCandidates=[];

  for(const [name,loader] of loaders){
    try{
      const candidate=await loader();
      if(usable(candidate)){
        liveCandidates.push({name,candidate,freshness:feedFreshness(candidate)});
      }else{
        console.warn('CERTAINU ignored empty/invalid prediction feed from '+name,candidate);
      }
    }catch(err){
      console.warn('CERTAINU prediction source failed: '+name,err);
    }
  }

  if(liveCandidates.length){
    liveCandidates.sort((a,b)=>
      b.freshness-a.freshness ||
      (b.candidate.predictions?.length||0)-(a.candidate.predictions?.length||0)
    );
    data=liveCandidates[0].candidate;
    source='LIVE '+liveCandidates[0].name;
  }else{
    data=embeddedData;
  }

  updateScore(data);
  renderResolvedArchive(data);
  // Always display the most recently made CERTAINU picks first, regardless of feed order.
  // updated_at is deliberately excluded: hourly refreshes must not reorder old picks.
  const pickTime=p=>Date.parse(p.locked_at||p.created_at||'')||0;
  const predictions=(data.predictions||[]).slice().sort((a,b)=>pickTime(b)-pickTime(a));
  const predictionList=document.getElementById('predictionList');
  const expandBtn=document.getElementById('predictionExpandBtn');
  function resolutionBucket(raw){const p=normalizePrediction(raw);const st=String(p.status||'').toLowerCase();if(['won','lost','void','resolved'].includes(st)||p.resolved_at)return 'resolved';const end=Date.parse(p.market_end_date||'');if(!end)return 'long';const h=(end-Date.now())/3600000;if(h<=24)return 'quick';if(h<=72)return 'short';if(h<=168)return 'week';return 'long';}
  function topicBucket(raw){const p=normalizePrediction(raw),saved=String(p.category||'').toLowerCase();if(['crypto','politics','geopolitics','sports','economy','culture','other'].includes(saved))return saved;const t=((p.question||'')+' '+(p.slug||'')).toLowerCase();if(/bitcoin|\bbtc\b|ethereum|\beth\b|solana|\bsol\b|crypto|dogecoin|\bdoge\b|xrp|ripple|cardano|chainlink|bnb|avalanche|sui|memecoin/.test(t))return 'crypto';if(/war|strike|attack|iran|israel|russia|ukraine|china|taiwan|nato|military|ceasefire|invasion|country|countries/.test(t))return 'geopolitics';if(/president|election|congress|senate|house|governor|democrat|republican|trump|vance|cabinet|primary|nominee|vote/.test(t))return 'politics';if(/nfl|nba|mlb|nhl|soccer|football|basketball|baseball|hockey|tennis|ufc|f1|formula 1|super bowl|world cup|championship|playoffs/.test(t))return 'sports';if(/fed|interest rate|inflation|gdp|recession|unemployment|jobs report|cpi|economy|tariff|stock market|s&p|nasdaq/.test(t))return 'economy';if(/movie|film|oscar|grammy|album|song|celebrity|box office|tv|television|streaming|award/.test(t))return 'culture';return 'other';}
  predictionList.innerHTML=predictions.map(p=>renderPrediction(p).replace('<article class="prediction-card','<article data-resolution-bucket="'+resolutionBucket(p)+'" data-topic-bucket="'+topicBucket(p)+'" class="prediction-card')).join('')||'<article class="prediction-card"><h3>No official calls yet.</h3></article>';
  let activeTime='all',activeTopic='all';
  function applyPredictionFilters(){const cards=[...predictionList.querySelectorAll('.prediction-card')];let visibleIndex=0;cards.forEach(card=>{const bucket=card.dataset.resolutionBucket;const timeMatch=activeTime==='all'?bucket!=='resolved':bucket===activeTime;const topicMatch=activeTopic==='all'||card.dataset.topicBucket===activeTopic;const matches=timeMatch&&topicMatch;card.classList.remove('prediction-overflow');if(matches){visibleIndex++;card.style.display='';if(visibleIndex>3)card.classList.add('prediction-overflow');}else card.style.display='none';});const collapse=visibleIndex>3;predictionList.classList.toggle('prediction-list-collapsed',collapse);if(expandBtn){expandBtn.hidden=!collapse;expandBtn.setAttribute('aria-expanded',collapse?'false':'true');}const label=document.getElementById('predictionExpandLabel');if(label){label.hidden=!collapse;label.textContent='SHOW MORE';}}
  const timeBar=document.getElementById('predictionTimeFilters');if(timeBar)timeBar.onclick=e=>{const b=e.target.closest('.prediction-time-filter');if(!b)return;activeTime=b.dataset.filter;timeBar.querySelectorAll('.prediction-time-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
  const topicBar=document.getElementById('predictionTopicFilters');if(topicBar)topicBar.onclick=e=>{const b=e.target.closest('.prediction-topic-filter');if(!b)return;activeTopic=b.dataset.topic;topicBar.querySelectorAll('.prediction-topic-filter').forEach(x=>x.classList.toggle('active',x===b));applyPredictionFilters();};
  applyPredictionFilters();

  if(expandBtn){
    const expandWrap=expandBtn.closest('.prediction-expand-wrap');
    const expandLabel=document.getElementById('predictionExpandLabel');
    expandBtn.setAttribute('aria-expanded','false');
    expandBtn.setAttribute('aria-label','Show more predictions');
    expandBtn.title='Show more predictions';
    if(expandWrap) expandWrap.classList.remove('is-expanded');

    // When minimized, the arrow stays in its normal position below the 3 cards.
    // When expanded, it floats at bottom-center while the CERTAINUTIES section is visible.
    const certainutiesSection=predictionList.closest('section');
    const updateFloatingArrow=()=>{
      if(!expandWrap || !certainutiesSection || expandBtn.hidden) return;
      const expanded=expandBtn.getAttribute('aria-expanded')==='true';
      const r=certainutiesSection.getBoundingClientRect();
      const inSection=r.top < window.innerHeight && r.bottom > 0;
      expandWrap.classList.toggle('is-in-section',expanded && inSection);
    };
    window.addEventListener('scroll',updateFloatingArrow,{passive:true});
    window.addEventListener('resize',updateFloatingArrow);
    updateFloatingArrow();

    expandBtn.onclick=()=>{
      const expanded=expandBtn.getAttribute('aria-expanded')==='true';
      const nextExpanded=!expanded;
      predictionList.classList.toggle('prediction-list-collapsed',!nextExpanded);
      expandBtn.setAttribute('aria-expanded',String(nextExpanded));
      expandBtn.setAttribute('aria-label',nextExpanded?'Show fewer predictions':'Show more predictions');
      expandBtn.title=nextExpanded?'Show fewer predictions':'Show more predictions';
      if(expandLabel) expandLabel.textContent=nextExpanded?'SHOW LESS':'SHOW MORE';
      requestAnimationFrame(updateFloatingArrow);
    };
  }

  status.textContent=`${source} • LAST REFRESH ${fmtDate(data.updated_at)} • AUTO-REFRESH ≈ EVERY HOUR • MODEL ${data.model_version||'rules-v2.2'}`;
  if(data.wallet){
    const walletLabel=document.getElementById('walletLabel');
    if(walletLabel) walletLabel.textContent='Official CERTAINU wallet: '+data.wallet;
  }
}
loadPredictions();