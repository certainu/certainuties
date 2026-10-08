
function copyCA(){const t=document.getElementById('contract').textContent;navigator.clipboard?.writeText(t);const b=document.querySelector('.copy');const old=b.textContent;b.textContent='COPIED';setTimeout(()=>b.textContent=old,1200)}
const obs=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('show')}),{threshold:.12});document.querySelectorAll('.reveal').forEach(e=>obs.observe(e));
