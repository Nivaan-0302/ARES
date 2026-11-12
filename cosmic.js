/* Additive readability enhancements; original element IDs and event handlers untouched. */
(function(){'use strict';
function ready(){
  const top=document.querySelector('.topbar');
  if(top && !document.querySelector('.ares-cosmic-banner')){
    const bar=document.createElement('div');bar.className='ares-cosmic-banner';
    const title=document.createElement('strong');title.textContent='ARES  /  DEEP SPACE OPERATIONS';
    const nav=document.createElement('span');
    [['#terrain','Explore Mars'],['#navigation','Route intelligence'],['#science','Scientific data']].forEach(([href,label],i)=>{if(i)nav.append('   ·   ');const a=document.createElement('a');a.href=href;a.textContent=label;nav.appendChild(a)});
    bar.append(title,nav);top.insertAdjacentElement('afterend',bar);
  }
  // Move only explanatory prose into disclosures, never the maps, forms, charts or telemetry.
  const disclosures=[
    ['#navigation > p','How route planning works'],
    ['#science > p','About the NASA MOLA dataset'],
    ['.terrain-section > .globe-disclaimer','Map controls and scientific limitations']
  ];
  disclosures.forEach(([selector,label])=>{
    const p=document.querySelector(selector);if(!p||p.closest('.ares-cosmic-disclosure'))return;
    const details=document.createElement('details');details.className='ares-cosmic-disclosure';
    const summary=document.createElement('summary');summary.textContent=label;
    const body=document.createElement('div');body.className='ares-cosmic-detail-body';
    p.parentNode.insertBefore(details,p);body.appendChild(p);details.append(summary,body);
  });
  // Keep the scientific report available and readable; its live fields retain their IDs.
  const report=document.getElementById('scientific-report');
  if(report && !report.querySelector('.ares-cosmic-disclosure')){
    const details=document.createElement('details');details.className='ares-cosmic-disclosure';details.open=true;
    const summary=document.createElement('summary');summary.textContent='Detailed scientific measurements and limitations';
    const body=document.createElement('div');body.className='ares-cosmic-detail-body';
    [...report.children].filter(el=>el.tagName!=='H2').forEach(el=>body.appendChild(el));
    details.append(summary,body);report.appendChild(details);
  }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();
