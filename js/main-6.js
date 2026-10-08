
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
