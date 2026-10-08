
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
