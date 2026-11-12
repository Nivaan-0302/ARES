/* ARES Mission Decision Brief — deterministic interpretation of mission-route API results. */
(() => {
  'use strict';
  const root = document.getElementById('ares-mission-brief');
  if (!root) return;
  const $ = id => document.getElementById(id);
  const fmt = (v, digits=2) => Number(v).toLocaleString(undefined,{maximumFractionDigits:digits,minimumFractionDigits:digits});
  const safe = v => typeof v === 'number' && Number.isFinite(v);
  const set = (id, value) => { $(id).textContent = value; };
  function empty(message) {
    set('ares-brief-headline', 'Awaiting route analysis');
    set('ares-brief-summary', message);
    set('ares-brief-exposure', '—');
    set('ares-brief-distance', '—');
    set('ares-brief-scope', 'No route calculated');
    set('ares-brief-guidance', 'Choose a starting point and destination in Planetary Explorer, then calculate a route.');
  }
  function render(data) {
    if (!data || data.status !== 'success') return;
    const regional = data.route_type === 'regional_dem_scale';
    const counts = data.hazard_breakdown || {};
    const low = Math.max(0, Number(counts.low)||0), moderate=Math.max(0,Number(counts.moderate)||0);
    const high=Math.max(0,Number(counts.high)||0), extreme=Math.max(0,Number(counts.extreme)||0);
    const total=low+moderate+high+extreme;
    const risk=Number(data.terrain_risk_score), route=Number(data.route_distance_km), direct=Number(data.direct_distance_km);
    set('ares-brief-scope',regional?'Regional MOLA terrain-grid route':'Global coarse-grid route with sampled refinement');
    const exposed=high+extreme;
    const fraction=total ? exposed/total*100 : null;
    set('ares-brief-exposure',total ? `${exposed} of ${total} classified samples (${fmt(fraction,1)}%)`:'No classified samples reported');
    set('ares-brief-distance',safe(route)&&safe(direct)?`${fmt(route)} km route · ${fmt(direct)} km great-circle reference`:'Distance metrics unavailable');
    if (!total) {
      set('ares-brief-headline','Route calculated; exposure data unavailable');
      set('ares-brief-summary','ARES calculated a route, but did not return a usable hazard breakdown. Do not infer that the route is low-risk.');
    } else if (exposed > 0) {
      set('ares-brief-headline','Elevated terrain exposure detected');
      set('ares-brief-summary',`The calculated route includes ${high} high-hazard and ${extreme} extreme-hazard classified samples, plus ${moderate} moderate-hazard samples. Review the terrain exposure chart before interpreting this route.`);
    } else if (moderate > 0) {
      set('ares-brief-headline','Moderate terrain exposure detected');
      set('ares-brief-summary',`No high- or extreme-hazard samples were reported among ${total} classified samples; ${moderate} are moderate hazard. This does not establish a hazard-free route.`);
    } else {
      set('ares-brief-headline','Low classified exposure on sampled route');
      set('ares-brief-summary',`All ${total} classified samples were marked low hazard at the available analysis scale. Unsampled obstacles and smaller terrain features remain unknown.`);
    }
    const extra=safe(route)&&safe(direct)?Math.max(0,route-direct):null;
    let guidance=regional
      ? 'This is a regional terrain-weighted A* result. Open Route Intelligence for terrain exposure and the separate distance-versus-safety comparison, when available.'
      : 'This is a coarse global planning result, not a rover-ready traverse. Regional distance-versus-safety comparisons are not directly applicable to this global route.';
    if (extra !== null) guidance+=` The calculated path is ${fmt(extra)} km longer than the geometric great-circle reference; that reference is not a traversable alternative.`;
    if (safe(risk)) guidance+=` Reported terrain risk index: ${fmt(risk)} / 100 (model-specific score, not a probability of failure).`;
    guidance+=' NASA MOLA elevation data cannot resolve every rover-scale obstacle.';
    set('ares-brief-guidance',guidance);
  }
  window.addEventListener('ares:route-analysis',event=>render(event.detail));
  window.addEventListener('ares:mission',event=>{
    const state=event.detail||{};
    if (!state.route) empty(state.start&&state.end?'Calculating a new route…':'Select mission coordinates to generate an evidence-based decision brief.');
  });
  empty('Select mission coordinates to generate an evidence-based decision brief.');
})();
