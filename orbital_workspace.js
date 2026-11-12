/* ARES Orbital Workspace: presentation only; preserves existing IDs, handlers, calculations. */
(()=>{'use strict';
function init(){
 const main=document.querySelector('.main-content'), top=main?.querySelector('.topbar'), terrain=document.getElementById('terrain'), form=document.getElementById('coordinate-form'), overview=document.getElementById('overview'), navigation=document.getElementById('navigation'), science=document.getElementById('science'), report=document.getElementById('scientific-report');
 if(!main||!top||!terrain||!form||!overview||!navigation||!science||document.getElementById('ares-orbital-tabs'))return;
 document.body.classList.add('ares-orbital');
 document.querySelectorAll('.sidebar-footer').forEach(el=>{el.textContent='ARES  /  MARS OPERATIONS';});
 document.querySelectorAll('body *').forEach(el=>{if(el.children.length===0&&/\bprototype\b|\bunder development\b|\bbeta\b/i.test(el.textContent||'')&&!['SCRIPT','STYLE'].includes(el.tagName))el.textContent=el.textContent.replace(/\bprototype\b/gi,'MISSION SYSTEM').replace(/\bunder development\b/gi,'MISSION OPERATIONS').replace(/\bbeta\b/gi,'');});
 const tabs=document.createElement('div');tabs.id='ares-orbital-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','ARES workspaces');
 const modes=[['mission','Planetary Explorer'],['routes','Route Intelligence'],['science','Science Lab']];
 modes.forEach(([key,label])=>{const b=document.createElement('button');b.type='button';b.setAttribute('role','tab');b.dataset.orbitalTab=key;b.textContent=label;b.addEventListener('click',()=>activate(key,true));tabs.appendChild(b);});
 const intro=document.createElement('div');intro.className='ares-orbital-intro';intro.innerHTML='<div><span class="ares-orbital-eyebrow">ARES / PLANETARY OPERATIONS</span><h1>Explore the red planet.</h1><p>Navigate Mars. Examine terrain. Make evidence-led mission decisions.</p></div><span class="ares-orbital-orbit" aria-hidden="true">◌</span>';
 const stage=document.createElement('div');stage.id='ares-orbital-stage';stage.className='ares-orbital-stage';
 const afterTop=main.querySelector('.ares-cosmic-banner')||top;
 afterTop.insertAdjacentElement('afterend',intro);intro.insertAdjacentElement('afterend',tabs);tabs.insertAdjacentElement('afterend',stage);
 // Reparent live DOM nodes rather than cloning: existing event listeners, globe canvas and data bindings remain intact.
 stage.append(terrain,form,overview,navigation);if(report)stage.append(report);stage.append(science);
 const kicker=main.querySelector('.ares-mission-kicker');if(kicker)kicker.hidden=true;
 const label=main.querySelector('.ares-workspace-label');if(label)label.hidden=true;
 const banner=main.querySelector('.ares-cosmic-banner');if(banner)banner.hidden=true;
 const mini=document.createElement('div');mini.className='ares-orbital-section-label';mini.textContent='MISSION SNAPSHOT';overview.prepend(mini);
 const nav=document.querySelector('.sidebar nav');if(nav){nav.querySelectorAll('a').forEach(a=>{const href=a.getAttribute('href');const key=href==='#navigation'?'routes':href==='#science'?'science':'mission';a.dataset.orbitalNav=key;a.addEventListener('click',e=>{e.preventDefault();activate(key,true);});});}
 const more=document.createElement('div');more.className='ares-orbital-note';more.textContent='MOLA-derived terrain intelligence is a planning aid, not rover-scale safety certification.';stage.appendChild(more);
 function activate(key,scroll){document.body.dataset.orbitalView=key;tabs.querySelectorAll('button').forEach(b=>{const selected=b.dataset.orbitalTab===key;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});nav?.querySelectorAll('a').forEach(a=>a.classList.toggle('ares-orbital-active',a.dataset.orbitalNav===key));if(scroll)tabs.scrollIntoView({behavior:'smooth',block:'start'});if(key==='mission'){setTimeout(()=>{window.dispatchEvent(new Event('resize'));try{window.aresMap?.invalidateSize?.();}catch(_){}},100);}}
 tabs.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const i=modes.findIndex(x=>x[0]===document.body.dataset.orbitalView);const next=modes[(i+(e.key==='ArrowRight'?1:2))%3][0];activate(next,true);tabs.querySelector(`[data-orbital-tab="${next}"]`)?.focus();});
 activate(location.hash==='#science'?'science':location.hash==='#navigation'?'routes':'mission',false);
 // Keep live route/scientific updates intact; do not mutate any dynamic readouts.
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
