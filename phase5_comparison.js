/* Phase 5 comparison is read-only: it does not change map routes or mission state. */
(function(){'use strict';
const root=document.createElement('section');root.id='ares-phase5';root.style.cssText='margin:18px 0;padding:18px;border:1px solid #385065;border-radius:14px;background:#101c2b;color:#e5effa;font:14px system-ui';
root.innerHTML='<div style="font-weight:700;letter-spacing:.08em;color:#8ddcf5">ROUTE STRATEGY COMPARISON</div><p id="ares-p5-status">Calculate a mission route to compare distance-optimized Dijkstra and terrain-weighted A* where regional data is available.</p><div id="ares-p5-data" style="display:none"></div><p style="font-size:12px;color:#9fb4c6">Comparison is independent of the displayed mission route. Regional MOLA-scale heuristic analysis only; not rover safety certification.</p>';
function mount(){const anchor=document.getElementById('ares-risk-scope');if(anchor){const panel=anchor.closest('section')||anchor.closest('article')||anchor.parentElement;panel.insertAdjacentElement('afterend',root);}else{(document.querySelector('main')||document.body).appendChild(root);}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
const status=()=>document.getElementById('ares-p5-status');const dataBox=()=>document.getElementById('ares-p5-data');
let generation=0,controller=null;
window.addEventListener('ares:mission',()=>{generation++;controller?.abort();if(status())status().textContent='Calculate a route to compare both strategies.';if(dataBox())dataBox().style.display='none';});
window.addEventListener('ares:route-error',()=>{controller?.abort();generation++;if(status())status().textContent='A mission route is unavailable. Retry the mission before comparing strategies.';if(dataBox())dataBox().style.display='none';});
window.addEventListener('ares:route-analysis',async ev=>{
 controller?.abort();controller=new AbortController();
 const token=++generation,route=ev.detail||{};
 const start=route.requested_start||route.scientific_report?.start_coordinates;
 const end=route.requested_destination||route.scientific_report?.destination_coordinates;
 if(!Array.isArray(start)||!Array.isArray(end))return;
 status().textContent='Computing distance-optimized Dijkstra and terrain-weighted A* on the same regional grid…';dataBox().style.display='none';
 const q=new URLSearchParams({start_lat:start[0],start_lon:start[1],end_lat:end[0],end_lon:end[1]});
 try{const res=await fetch('/api/route-comparison?'+q,{signal:controller.signal});const result=await res.json();if(token!==generation)return;
 if(result.status!=='success'){status().textContent=result.reason||result.error||'Comparison unavailable for this route.';return;}
 const a=result.distance_optimized,b=result.terrain_weighted,c=result.comparison;
 status().textContent='Independent regional distance-optimized Dijkstra and terrain-weighted A* routes · '+result.scope;
 const fmt=n=>Number(n).toLocaleString(undefined,{maximumFractionDigits:3});
 const rows=[['Distance (km)',a.route_distance_km,b.route_distance_km],['High + extreme cells',a.high_extreme_cells,b.high_extreme_cells],['Weighted grid cost (km-equivalent)',a.weighted_grid_cost_km,b.weighted_grid_cost_km],['Path cells',a.path_cells,b.path_cells]];
 const table=document.createElement('table');table.style.cssText='width:100%;border-collapse:collapse;text-align:left;font-size:13px';
 const head=document.createElement('tr');['Metric','Distance (Dijkstra)','Terrain (A*)'].forEach(x=>{const th=document.createElement('th');th.textContent=x;th.style.padding='9px 4px';head.appendChild(th)});table.appendChild(head);
 rows.forEach(row=>{const tr=document.createElement('tr');row.forEach((x,i)=>{const td=document.createElement('td');td.textContent=i?fmt(x):x;td.style.cssText='padding:8px 4px;border-top:1px solid #34465b';tr.appendChild(td)});table.appendChild(tr)});
 const note=document.createElement('p');note.textContent='Terrain A* difference: '+fmt(c.distance_difference_km)+' km distance; '+fmt(c.high_extreme_cells_avoided)+' fewer high/extreme path cells; '+fmt(c.weighted_cost_improvement_percent)+'% lower weighted grid cost. Negative values indicate no improvement for that metric.';
 dataBox().replaceChildren(table,note);dataBox().style.display='block';
 }catch(e){if(token===generation&&e.name!=='AbortError')status().textContent='Route comparison is temporarily unavailable. Please verify that the mission service is running.';}
});
})();
