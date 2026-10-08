
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
