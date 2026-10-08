
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
