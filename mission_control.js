/* Read-only telemetry mirror. No routing or map handlers are changed. */
(function(){'use strict';
const mappings=[['route-distance','ares-live-distance'],['route-efficiency','ares-live-efficiency'],['route-risk','ares-live-risk'],['route-waypoints','ares-live-waypoints'],['terrain-status','ares-live-terrain'],['terrain-elevation','ares-live-elevation'],['terrain-slope','ares-live-slope'],['terrain-hazard','ares-live-hazard']];
function mirror(){for(const [sourceId,targetId] of mappings){const source=document.getElementById(sourceId),target=document.getElementById(targetId);if(!source||!target)continue;const txt=(source.textContent||'').trim();if(txt)target.textContent=txt;}}
function init(){mirror();const observer=new MutationObserver(mirror);for(const [sourceId] of mappings){const el=document.getElementById(sourceId);if(el)observer.observe(el,{childList:true,characterData:true,subtree:true});}window.addEventListener('ares:mission',mirror);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
