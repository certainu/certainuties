
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
