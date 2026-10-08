
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
