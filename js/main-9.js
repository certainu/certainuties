
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
