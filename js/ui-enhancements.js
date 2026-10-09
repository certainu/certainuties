
(function(){
  function emphasizeCertainuDecisions(root=document){
    const candidates = root.querySelectorAll('#markets *');
    candidates.forEach(el => {
      if(el.children.length) return;
      const raw=(el.textContent||'').trim();

      /* Existing sentence such as "CERTAINU IS 70% CERTAIN → NO". */
      const m=raw.match(/^CERTAINU\s+IS\s+(\d{1,3})%\s+CERTAIN\s*(?:→|->|—|-)\s*(YES|NO)$/i);
      if(m && !el.classList.contains('certainu-decision')){
        el.classList.add('certainu-decision');
        el.innerHTML='CERTAINU IS <strong>'+m[1]+'% CERTAIN</strong> → <span class="decision-side">'+m[2].toUpperCase()+'</span>';
      }
    });
  }

  emphasizeCertainuDecisions();
  const markets=document.getElementById('markets');
  if(markets){
    new MutationObserver(()=>emphasizeCertainuDecisions(markets))
      .observe(markets,{childList:true,subtree:true});
  }
})();

;

(function(){
  const section = document.getElementById('markets');
  if(!section) return;

  const arts = Array.from(section.querySelectorAll('.certainuties-side-art'));
  if(!arts.length) return;

  let ticking = false;

  function updateCertainutiesMascots(){
    ticking = false;

    if(window.innerWidth <= 900){
      arts.forEach(el => el.style.removeProperty('transform'));
      return;
    }

    const sectionRect = section.getBoundingClientRect();
    const sectionTop = window.scrollY + sectionRect.top;

    arts.forEach(el => {
      /* Base top is where the graphic naturally starts inside CERTAINUTIES. */
      const baseTop = parseFloat(getComputedStyle(el).top) || 28;
      const artHeight = el.offsetHeight;

      /* Follow the user's viewport around its upper-middle area. */
      const desiredDocumentTop = window.scrollY + (window.innerHeight * 0.22);
      let shift = desiredDocumentTop - (sectionTop + baseTop);

      /* Never move above the original position. */
      shift = Math.max(0, shift);

      /* Never cross the bottom/color boundary into the next section. */
      const bottomPadding = 28;
      const maxShift = Math.max(
        0,
        section.offsetHeight - baseTop - artHeight - bottomPadding
      );
      shift = Math.min(shift, maxShift);

      el.style.setProperty('transform', `translateY(${Math.round(shift)}px)`, 'important');
    });
  }

  function requestMascotUpdate(){
    if(!ticking){
      ticking = true;
      requestAnimationFrame(updateCertainutiesMascots);
    }
  }

  window.addEventListener('scroll', requestMascotUpdate, {passive:true});
  window.addEventListener('resize', requestMascotUpdate);
  window.addEventListener('load', requestMascotUpdate);
  document.addEventListener('DOMContentLoaded', requestMascotUpdate);

  /* Recalculate after predictions expand/collapse and change section height. */
  const observer = new MutationObserver(requestMascotUpdate);
  observer.observe(section, {childList:true, subtree:true, attributes:true});

  requestMascotUpdate();
})();

;

(function(){
  const section=document.getElementById('markets');
  if(!section) return;

  const arts=Array.from(section.querySelectorAll('.certainuties-side-art'));
  if(!arts.length) return;

  let target=0;
  let current=0;
  let running=false;

  function calculateTarget(){
    if(window.innerWidth<=900){
      target=0;
      return;
    }

    const rect=section.getBoundingClientRect();
    const sectionTop=window.scrollY+rect.top;
    const sample=arts[0];
    const baseTop=parseFloat(getComputedStyle(sample).top)||28;
    const artHeight=sample.offsetHeight;

    /* Position the mascots around the upper-middle of the visible screen. */
    const desiredTop=window.scrollY+(window.innerHeight*0.24);
    let next=desiredTop-(sectionTop+baseTop);

    next=Math.max(0,next);

    /* Hard clamp keeps the artwork completely inside the dark-blue area. */
    const bottomPadding=32;
    const maxShift=Math.max(
      0,
      section.offsetHeight-baseTop-artHeight-bottomPadding
    );

    target=Math.min(next,maxShift);
  }

  function animate(){
    /* Ease toward the target instead of jumping to every scroll position. */
    current += (target-current)*0.115;

    if(Math.abs(target-current)<0.08){
      current=target;
    }

    const y=Math.round(current*100)/100;
    arts.forEach(el=>{
      el.style.setProperty(
        'transform',
        'translate3d(0,'+y+'px,0)',
        'important'
      );
    });

    if(Math.abs(target-current)>0.08){
      requestAnimationFrame(animate);
    }else{
      running=false;
    }
  }

  function update(){
    calculateTarget();
    if(!running){
      running=true;
      requestAnimationFrame(animate);
    }
  }

  window.addEventListener('scroll',update,{passive:true});
  window.addEventListener('resize',update,{passive:true});
  window.addEventListener('load',update);
  document.addEventListener('DOMContentLoaded',update);

  /* Recalculate when SHOW MORE / SHOW LESS changes section height. */
  new ResizeObserver(update).observe(section);

  calculateTarget();
  current=target;
  update();
})();

;

(function(){
  const section=document.getElementById('markets');
  if(!section) return;
  const arts=Array.from(section.querySelectorAll('.certainuties-side-art'));
  if(!arts.length) return;

  function lockCertainutiesWallpaper(){
    arts.forEach(el=>{
      el.style.setProperty('transform','none','important');
      el.style.setProperty('translate','none','important');
      el.style.setProperty('position','absolute','important');
      el.style.setProperty('top','0','important');
    });
  }

  lockCertainutiesWallpaper();

  /* Older scroll code may try to write transforms; immediately neutralize them. */
  const observer=new MutationObserver(lockCertainutiesWallpaper);
  arts.forEach(el=>observer.observe(el,{attributes:true,attributeFilter:['style']}));
})();

;

(function(){
  const markets=document.getElementById('markets');
  if(!markets) return;

  function colorCertainuPredictionBubbles(){
    /* Find elements labelled CERTAINU and color the closest compact value bubble. */
    markets.querySelectorAll('*').forEach(label=>{
      if(label.children.length) return;
      if((label.textContent||'').trim().toUpperCase()!=='CERTAINU') return;

      let bubble=label.parentElement;
      if(!bubble) return;

      /* Walk up slightly if the immediate parent is only a label wrapper. */
      for(let i=0;i<2;i++){
        const t=(bubble.textContent||'').toUpperCase();
        if(/\b(YES|NO)\b/.test(t) && /%/.test(t)) break;
        if(bubble.parentElement) bubble=bubble.parentElement;
      }

      const value=(bubble.textContent||'').toUpperCase();
      bubble.classList.remove('certainu-choice-yes','certainu-choice-no');

      if(/\bYES\b/.test(value)){
        bubble.classList.add('certainu-choice-yes');
      }else if(/\bNO\b/.test(value)){
        bubble.classList.add('certainu-choice-no');
      }
    });
  }

  colorCertainuPredictionBubbles();

  new MutationObserver(colorCertainuPredictionBubbles).observe(
    markets,
    {childList:true,subtree:true}
  );
})();

;

(function(){
  const markets=document.getElementById('markets');
  if(!markets) return;

  function fixCertainuHighlight(){
    /* Remove the earlier broad coloring completely. */
    markets.querySelectorAll(
      '.certainu-choice-yes,.certainu-choice-no,.certainu-value-highlight-yes,.certainu-value-highlight-no'
    ).forEach(el=>{
      el.classList.remove(
        'certainu-choice-yes','certainu-choice-no',
        'certainu-value-highlight-yes','certainu-value-highlight-no'
      );
    });

    /* Target only a compact bubble containing:
       CERTAINU + a percentage + YES/NO, like the screenshot. */
    markets.querySelectorAll('*').forEach(el=>{
      const directText=Array.from(el.childNodes)
        .filter(n=>n.nodeType===Node.TEXT_NODE)
        .map(n=>n.textContent)
        .join(' ')
        .trim();

      const full=(el.textContent||'').replace(/\s+/g,' ').trim().toUpperCase();
      if(!full.startsWith('CERTAINU')) return;
      if(!/\b\d{1,3}%\s+(YES|NO)\b/.test(full)) return;

      const r=el.getBoundingClientRect();
      /* Exclude whole prediction cards / large containers. */
      if(r.width>650 || r.height>180) return;

      if(/\b\d{1,3}%\s+YES\b/.test(full)){
        el.classList.add('certainu-value-highlight-yes');
      }else if(/\b\d{1,3}%\s+NO\b/.test(full)){
        el.classList.add('certainu-value-highlight-no');
      }
    });
  }

  fixCertainuHighlight();
  new MutationObserver(fixCertainuHighlight).observe(markets,{childList:true,subtree:true});
})();

;

(function(){
  const markets=document.getElementById('markets');
  if(!markets) return;

  function colorAllCertainuValueBubbles(){
    /* Start clean so only the intended compact CERTAINU bubbles are colored. */
    markets.querySelectorAll(
      '.certainu-value-highlight-yes,.certainu-value-highlight-no'
    ).forEach(el=>{
      el.classList.remove('certainu-value-highlight-yes','certainu-value-highlight-no');
    });

    markets.querySelectorAll('*').forEach(el=>{
      const full=(el.textContent||'').replace(/\s+/g,' ').trim().toUpperCase();

      /* Works for current AND concluded cards:
         CERTAINU / 70% NO / CERTAIN
         CERTAINU / 69% NO / PRETTY CERTAIN
         etc. */
      if(!full.startsWith('CERTAINU')) return;

      const decision=full.match(/\b(\d{1,3})%\s+(YES|NO)\b/);
      if(!decision) return;

      const r=el.getBoundingClientRect();

      /* Keep this limited to the small CERTAINU value bubble,
         never the entire resolved prediction card. */
      if(r.width>650 || r.height>180) return;

      if(decision[2]==='YES'){
        el.classList.add('certainu-value-highlight-yes');
      }else{
        el.classList.add('certainu-value-highlight-no');
      }
    });
  }

  colorAllCertainuValueBubbles();

  new MutationObserver(colorAllCertainuValueBubbles).observe(
    markets,
    {childList:true,subtree:true}
  );

  window.addEventListener('load',colorAllCertainuValueBubbles);
})();

;

(function(){
  const markets=document.getElementById('markets');
  if(!markets) return;

  function applyExactCertainuPickColors(){
    markets.querySelectorAll('.certainu-pick-green,.certainu-pick-red').forEach(el=>{
      el.classList.remove('certainu-pick-green','certainu-pick-red');
    });

    /* Start at the visible "64% YES" / "70% NO" value itself. */
    const leaves=[...markets.querySelectorAll('*')].filter(el=>el.children.length===0);

    leaves.forEach(valueEl=>{
      const value=(valueEl.textContent||'').replace(/\s+/g,' ').trim().toUpperCase();
      const match=value.match(/^(\d{1,3})%\s+(YES|NO)$/);
      if(!match) return;

      /* Walk upward until we find the smallest card that also contains
         the CERTAINU heading. This works for open and resolved cards. */
      let card=valueEl.parentElement;
      let chosen=null;

      for(let depth=0; card && card!==markets && depth<6; depth++,card=card.parentElement){
        const txt=(card.textContent||'').replace(/\s+/g,' ').trim().toUpperCase();
        const rect=card.getBoundingClientRect();

        if(
          txt.includes('CERTAINU') &&
          txt.includes(value) &&
          rect.width>=120 &&
          rect.width<=700 &&
          rect.height>=55 &&
          rect.height<=220
        ){
          chosen=card;
          break;
        }
      }

      if(!chosen) return;

      chosen.classList.add(match[2]==='YES' ? 'certainu-pick-green' : 'certainu-pick-red');
    });
  }

  let queued=false;
  function queueColor(){
    if(queued) return;
    queued=true;
    requestAnimationFrame(()=>{
      queued=false;
      applyExactCertainuPickColors();
    });
  }

  queueColor();
  window.addEventListener('load',queueColor);
  new MutationObserver(queueColor).observe(markets,{childList:true,subtree:true});
})();
