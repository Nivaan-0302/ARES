/* ARES public-facing refinements. Presentation only: no routing, terrain, or event handlers changed. */
(()=>{'use strict';
function init(){
 const intro=document.querySelector('.ares-orbital-intro');
 if(!intro||document.body.dataset.aresPublicPolish)return;
 document.body.dataset.aresPublicPolish='ready';
 const old=intro.querySelector('.ares-orbital-orbit');
 if(old){const image=document.createElement('img');image.className='ares-public-mars';image.src='mars_hero.png';image.alt='Mars, the red planet';image.width=176;image.height=176;image.decoding='async';old.replaceWith(image);}
 // Provide short, task-oriented explanations, anchored to the actual ARES controls.
 const explain=[
  ['#navigation > .ares-cosmic-disclosure', 'How route planning works', [
   ['1 · Choose a destination','Open Planetary Explorer. Enter start and destination latitude/longitude, or select the points directly on the 3D globe or 2D map. Use Explore mode when you want to inspect Mars without changing the mission.'],
   ['2 · Calculate a route','Select “Plot coordinates & calculate route.” ARES uses terrain-weighted A* on a regional MOLA grid when both points fit that region. Longer journeys use coarse global A* with selected local refinement.'],
   ['3 · Understand the result','Open Route Intelligence to read route distance, efficiency, sampled hazard exposure, and the regional Distance (Dijkstra) versus Terrain (A*) comparison. A longer route can have a lower modeled terrain cost.'],
   ['What the comparison means','Distance-optimized Dijkstra and terrain-weighted A* are compared only when both endpoints fit one regional analysis window. Global routes cannot be compared on that same regional grid.']
  ]],
  ['#science > .ares-cosmic-disclosure','About NASA MOLA terrain data',[
   ['What the data represents','ARES reads elevation from NASA Mars Orbiter Laser Altimeter (MOLA) data. It estimates local slope from neighboring elevation samples and assigns a terrain hazard class.'],
   ['Where to see it','In Planetary Explorer, choose a point to inspect its surrounding regional hazard grid. Open Science Lab to view elevation, estimated slope, hazard class, and the route elevation profile.'],
   ['How to interpret the classes','Low: up to 5°; Moderate: above 5° to 15°; High: above 15° to 25°; Extreme: above 25°. These are ARES planning categories, not validated rover traversability thresholds.'],
   ['Resolution matters','The supplied MOLA product’s resolution and latitude determine its ground sampling; it cannot identify individual rocks, sand traps, or small obstacles. ARES provides terrain-scale planning evidence, not a safe-driving guarantee.']
  ]],
  ['#terrain .ares-cosmic-disclosure','Map controls and scientific limitations',[
   ['Explore safely','Explore mode lets you rotate and inspect the globe without changing the mission endpoints. Choose Select Start or Select Destination before clicking a new location.'],
   ['Switch views','Use “Switch to 2D map” for a flat map of the same mission, and switch back to 3D for planetary context. “Focus on hazards” centers the available regional terrain analysis.'],
   ['Read the hazard overlay','Green, yellow, orange, and red show ARES slope-based hazard classes on the selected regional grid. The overlay describes the analyzed region; it is not a continuous rover-scale obstacle map.'],
   ['Route scope','Global routes are planned on a coarse grid with selected high-resolution checks. A low displayed global risk index does not mean every meter of the route was verified.']
  ]]
 ];
 for(const [selector,title,items] of explain){const details=document.querySelector(selector);if(!details)continue;const summary=details.querySelector('summary');if(summary)summary.textContent=title;const body=details.querySelector('.ares-cosmic-detail-body');if(!body)continue;const content=document.createElement('div');content.className='ares-public-guide';for(const [heading,description] of items){const article=document.createElement('article');const h=document.createElement('h4');h.textContent=heading;const p=document.createElement('p');p.textContent=description;article.append(h,p);content.appendChild(article);}body.replaceChildren(content);}
 // Put the comparison where users expect it: Route Intelligence, not under mission configuration.
 const comparison=document.getElementById('ares-phase5');const navigation=document.getElementById('navigation');
 if(comparison&&navigation){navigation.appendChild(comparison);comparison.classList.add('ares-public-comparison');}
 const renameComparison=()=>{const panel=document.getElementById('ares-phase5');if(!panel)return;const heading=panel.firstElementChild;if(heading&&/PHASE\s*5/i.test(heading.textContent||''))heading.textContent='ROUTE STRATEGY COMPARISON';};
 renameComparison();
 // The comparison script can mount after this script, so re-check once the page finishes loading.
 window.addEventListener('load',()=>{const panel=document.getElementById('ares-phase5');if(panel&&navigation&&!navigation.contains(panel)){navigation.appendChild(panel);panel.classList.add('ares-public-comparison');}renameComparison();},{once:true});
 // Dynamic scientific measurements remain untouched. Only the interface's own internal milestone label changes.
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
