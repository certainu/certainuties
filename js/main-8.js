
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
