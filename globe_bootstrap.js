/* Optional 3D renderer: mission analysis and 2D navigation work independently. */
(function(){
  'use strict';
  const button=document.getElementById('view-toggle');
  let unavailable=false;
  function showMap(show){
    document.getElementById('mars-map').hidden=!show;
    document.getElementById('mars-globe').hidden=show;
    button.textContent=unavailable?'2D map (3D unavailable)':show?'Switch to 3D globe':'Switch to 2D map';
    window.dispatchEvent(new CustomEvent('ares:view',{detail:{map:show}}));
    if(show)setTimeout(()=>{
      const map=window.aresMap;
      if(!map)return;
      map.invalidateSize();
      const state=window.ARESMission.get();
      if(state.start&&state.end){
        const a=state.start,b=state.end;
        // At a dateline crossing show the complete wrapped route, not a false chord.
        const crossing=Math.abs(a.lon-b.lon)>180;
        map.fitBounds(crossing?[[-90,-180],[90,180]]:[[Math.min(a.lat,b.lat),Math.min(a.lon,b.lon)],[Math.max(a.lat,b.lat),Math.max(a.lon,b.lon)]],{padding:[32,32],maxZoom:6});
      }else if(state.start)map.setView([state.start.lat,state.start.lon],Math.max(map.getZoom(),3));
    },0);
  }
  function fallback(error){
    unavailable=true;
    button.disabled=true;
    showMap(true);
    const message=document.getElementById('globe-message');
    message.textContent='3D view unavailable. Use the 2D map or coordinate form; terrain analysis and route calculations remain available.';
    console.warn('ARES 3D renderer unavailable:',error);
  }
  window.ARESViews={showMap,fallback};
  button.addEventListener('click',()=>showMap(document.getElementById('mars-map').hidden));
  import('./globe.js').catch(fallback);
})();
