/* Read-only route intelligence; does not initiate routes or change mission state. */
(function(){'use strict';
  const byId=id=>document.getElementById(id);
  const classes=[['low','Low','#38dca0'],['moderate','Moderate','#ffcc55'],['high','High','#ff844e'],['extreme','Extreme','#e84767']];
  let lastPoints='';
  const number=(n,d=2)=>Number(n).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});
  function reset(){
    byId('ares-risk-scope').textContent='AWAITING ROUTE';
    byId('ares-risk-empty').hidden=false;
    byId('ares-risk-content').hidden=true;
    byId('ares-risk-bar').replaceChildren();
    byId('ares-risk-legend').replaceChildren();
  }
  window.addEventListener('ares:mission',event=>{
    const key=JSON.stringify([event.detail.start,event.detail.end]);
    if(key!==lastPoints){lastPoints=key;reset();}
  });
  window.addEventListener('ares:route-analysis',event=>{
    const data=event.detail||{};
    const breakdown=data.hazard_breakdown||{};
    const values=classes.map(([key])=>Number(breakdown[key]||0));
    if(values.some(v=>!Number.isFinite(v)||v<0))return;
    const total=values.reduce((a,b)=>a+b,0);
    const route=Number(data.route_distance_km),direct=Number(data.direct_distance_km);
    if(!Number.isFinite(route)||!Number.isFinite(direct))return;
    byId('ares-risk-empty').hidden=true;
    byId('ares-risk-content').hidden=false;
    byId('ares-risk-scope').textContent=data.route_type==='regional_dem_scale'?'REGIONAL MOLA ROUTE':'GLOBAL COARSE + SAMPLED REFINEMENT';
    const bar=byId('ares-risk-bar'),legend=byId('ares-risk-legend');bar.replaceChildren();legend.replaceChildren();
    classes.forEach(([key,label,color],i)=>{
      const value=values[i],percentage=total?value/total*100:0;
      if(value){const segment=document.createElement('span');segment.style.width=percentage+'%';segment.style.background=color;segment.title=label+': '+value+' ('+number(percentage,1)+'%)';bar.appendChild(segment);}
      const item=document.createElement('div');const name=document.createElement('span');name.textContent='● '+label;name.style.color=color;
      const count=document.createElement('b');count.textContent=value+' · '+(total?number(percentage,1)+'%':'—');item.append(name,count);legend.appendChild(item);
    });
    bar.setAttribute('aria-label',total?'Route hazard sample distribution: '+classes.map((c,i)=>c[1]+' '+values[i]).join(', '):'No classified hazard samples available');
    byId('ares-risk-direct').textContent=number(direct,3)+' km';
    byId('ares-risk-route').textContent=number(route,3)+' km';
    const extra=route-direct;
    byId('ares-risk-extra').textContent=(extra>=0?'+':'')+number(extra,3)+' km';
    const higher=values[2]+values[3];
    byId('ares-risk-explanation').textContent=total
      ? 'ARES classified '+total+' route samples: '+higher+' high/extreme ('+number(higher/total*100,1)+'%). The terrain-aware route is '+number(route,3)+' km versus a '+number(direct,3)+' km geometric great-circle reference. The extra distance alone does not prove improved safety.'
      : 'This route response contains no classified hazard samples. Distance comparison is available, but terrain exposure cannot be quantified from this response.';
  });
})();
