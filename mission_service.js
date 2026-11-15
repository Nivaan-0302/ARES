/* Shared mission analysis. No Leaflet, Three.js, or WebGL dependency. */
(function(){
  'use strict';
  let generation=0,pointsKey='',start=null,end=null,analysis=null,region=null;
  let controller=null,regionController=null,regionKey=null,hazardsVisible=true;
  const regions=new Map();
  const byId=id=>document.getElementById(id);
  const set=(id,value)=>{const element=byId(id);if(element)element.textContent=value;};
  const emit=(name,detail)=>window.dispatchEvent(new CustomEvent(name,{detail}));
  function status(text){set('globe-message',text);}
  function clearReadouts(){
    for(const id of ['route-distance','route-efficiency','route-risk','route-waypoints','route-hazards','terrain-elevation','terrain-slope','terrain-hazard'])set(id,'');
    for(const id of ['ares-live-distance','ares-live-efficiency','ares-live-risk','ares-live-waypoints','ares-live-elevation','ares-live-slope','ares-live-hazard'])set(id,'—');
    set('terrain-status',start?'ANALYZING MOLA…':'AWAITING LOCATION');
    set('ares-live-terrain',start?'ANALYZING MOLA…':'AWAITING LOCATION');
    set('route-status',end?'CALCULATING…':'AWAITING MISSION');
    byId('route-details').hidden=true;byId('terrain-details').hidden=true;
    byId('scientific-report').hidden=true;
  }
  function serviceError(message,status=0,code='unavailable'){
    const error=new Error(message);error.status=status;error.code=code;return error;
  }
  async function json(url,signal){
    const timeout=new AbortController();
    const cancel=()=>timeout.abort();
    signal?.addEventListener('abort',cancel,{once:true});
    if(signal?.aborted)timeout.abort();
    const timer=setTimeout(()=>timeout.abort(),url.includes('route')?120000:30000);
    try{
      const response=await fetch(url,{signal:timeout.signal});
      let data;
      try{data=await response.json();}catch(_error){throw serviceError('Terrain service returned an unreadable response. Please retry.',response.status,'invalid_response');}
      if(!response.ok){
        const message=response.status===503&&data.status==='busy'
          ? 'Terrain analysis is busy. Wait a moment, then retry the mission.'
          : data.message||data.error||`Terrain service returned HTTP ${response.status}.`;
        throw serviceError(message,response.status,data.status||'unavailable');
      }
      return data;
    }catch(error){
      if(signal?.aborted)throw error;
      if(error.name==='AbortError')throw serviceError('Terrain analysis timed out. Retry the mission or choose closer coordinates.',0,'timeout');
      if(error instanceof TypeError)throw serviceError('Cannot reach the terrain service. Check the server connection, then retry.',0,'offline');
      throw error;
    }finally{clearTimeout(timer);signal?.removeEventListener('abort',cancel);}
  }
  function setPending(pending){
    byId('coordinate-form').setAttribute('aria-busy',String(pending));
    byId('route-status').setAttribute('aria-busy',String(pending));
    const retry=byId('mission-retry');if(retry)retry.hidden=true;
  }
  function routeFailure(error){
    analysis=null;setPending(false);
    set('route-status',error.code==='busy'?'SERVICE BUSY':'ROUTE UNAVAILABLE');
    set('coordinate-feedback',`Route unavailable: ${error.message}`);
    status(`Route unavailable: ${error.message}`);
    const retry=byId('mission-retry');if(retry)retry.hidden=false;
    emit('ares:route-error',{message:error.message,status:error.status||0,code:error.code||'unavailable'});
  }
  function getRegion(lat,lon){
    const key=JSON.stringify([lat,lon]);
    if(regions.has(key))return regions.get(key);
    if(regionKey!==key){regionController?.abort();regionController=new AbortController();regionKey=key;}
    const pending=json('/api/terrain-region?'+new URLSearchParams({lat,lon}),regionController.signal)
      .catch(error=>{if(regions.get(key)===pending)regions.delete(key);throw error;});
    regions.set(key,pending);
    while(regions.size>8)regions.delete(regions.keys().next().value);
    return pending;
  }
  function renderRegion(data){
    const grid=data.hazard_grid;
    if(!Array.isArray(grid)||!grid.length||!Array.isArray(grid[0])||!grid[0].length||
      grid.some(row=>!Array.isArray(row)||row.length!==grid[0].length||row.some(value=>![-1,0,1,2,3].includes(value)))||
      !data.bounds||!['north','south','east','west'].every(key=>Number.isFinite(data.bounds[key])))
      throw serviceError('Regional terrain response is incomplete. Please retry.',0,'invalid_response');
    region=data;
    byId('hazard-focus').disabled=false;
    const totals=[0,0,0,0,0];
    for(const row of grid)for(const value of row)totals[value>=0&&value<=3?value:4]++;
    set('region-status',`Coarse-resolution MOLA slope screening: ${grid.length} × ${grid[0].length} cells. Focus on hazards to inspect the grid.`);
    const meta=data.terrain_metadata;
    const spacing=meta?.pixel_width_range_m;
    const scale=Array.isArray(spacing)&&spacing.every(Number.isFinite)&&Number.isFinite(meta.pixel_height_m)
      ? ` · Pixel spacing E–W ${spacing[0].toFixed(1)}–${spacing[1].toFixed(1)} m; N–S ${meta.pixel_height_m.toFixed(1)} m` : '';
    set('region-counts',`Low ${totals[0]} · Moderate ${totals[1]} · High ${totals[2]} · Extreme ${totals[3]} · No data ${totals[4]}${scale}${meta?.window_clipped_to_dataset?' · Region clipped to available dataset':''}`);
    emit('ares:region',{data,generation});
  }
  async function terrainAt(point,token,signal){
    const query=new URLSearchParams({lat:point.lat,lon:point.lon});
    const results=await Promise.allSettled([json('/api/elevation?'+query,signal),json('/api/slope?'+query,signal)]);
    if(token!==generation)return;
    const elevation=results[0].status==='fulfilled'?results[0].value:null;
    const slope=results[1].status==='fulfilled'?results[1].value:null;
    const elevationOK=typeof elevation?.elevation_m==='number'&&Number.isFinite(elevation.elevation_m);
    const slopeOK=typeof slope?.slope_degrees==='number'&&Number.isFinite(slope.slope_degrees);
    set('terrain-status',elevationOK&&slopeOK?'DATA AVAILABLE':elevationOK||slopeOK?'PARTIAL DATA':'DATA UNAVAILABLE');
    byId('terrain-details').hidden=false;
    const detail=index=>results[index].status==='rejected'?results[index].reason.message:'No valid reading';
    set('terrain-elevation',elevationOK?`Elevation: ${elevation.elevation_m.toLocaleString()} m`:`Elevation: unavailable — ${detail(0)}`);
    set('terrain-slope',slopeOK?`Estimated slope: ${slope.slope_degrees.toFixed(3)}°`:`Estimated slope: unavailable — ${detail(1)}`);
    set('terrain-hazard',slopeOK?`Terrain steepness: ${slope.hazard_level??'unavailable'}`:'Terrain steepness: unavailable');
  }
function showScientificReport(data, local){
  const panel=document.getElementById('scientific-report');
  panel.hidden=false;
  const refinement=data.refinement;
  const profile=data.scientific_report;
  document.getElementById('report-scope').textContent=local
    ? 'Regional A* on a MOLA-derived hazard grid.'
    : `Global A* with ${refinement?.sampled_windows ?? 0} locally inspected windows across ${refinement?.total_coarse_segments ?? 0} coarse segments; ${refinement?.modified_windows ?? 0} windows rerouted. This is partial, not continuous high-resolution validation.`;
  const low=profile?.minimum_elevation_m,high=profile?.maximum_elevation_m;
  const summary=document.getElementById('report-route-metrics');
  if(summary)summary.textContent=`Start ${start.lat.toFixed(5)}°, ${start.lon.toFixed(5)}° · Destination ${end.lat.toFixed(5)}°, ${end.lon.toFixed(5)}° · Great-circle ${data.direct_distance_km.toFixed(3)} km · Terrain-weighted A* ${data.route_distance_km.toFixed(3)} km · Efficiency ${data.route_efficiency_percent.toFixed(2)}% · Risk index ${data.terrain_risk_score.toFixed(2)}/100`;
  const scope=document.getElementById('report-hazard-scope');
  if(scope)scope.textContent=profile?.hazard_metric_scope||'Hazard classification is an estimate at DEM scale.';
  document.getElementById('report-elevation').textContent=low==null || high==null
    ? 'Elevation profile: not available for this route.'
    : `Sampled MOLA elevation: ${low.toFixed(0)} m to ${high.toFixed(0)} m (${profile.elevation_sample_count} samples).`;
  const slopeSummary=document.getElementById('report-slope');
  if(slopeSummary)slopeSummary.textContent=profile?.slope_sample_count ? `MOLA-scale sampled slope: mean ${profile.mean_sampled_slope_degrees.toFixed(3)}° · maximum ${profile.maximum_sampled_slope_degrees.toFixed(3)}° · ${profile.slope_sample_count} readings (not a continuous slope survey).` : 'Sampled slope data unavailable.';
  document.getElementById('report-limits').textContent=profile?.limitations ||
    'Regional MOLA DEM estimates only. No rover-scale obstacle detection.';
  const svg=document.getElementById('elevation-chart');
  svg.replaceChildren();
  const allSamples=profile?.elevation_profile||[];
  const segments=window.ARESGeometry.profileSegments(allSamples);
  const samples=segments.flat();
  const missing=allSamples.length-samples.length;
  const caption=document.getElementById('profile-caption');
  if(caption)caption.textContent=samples.length
    ? `${samples.length} valid elevation samples; ${missing} missing or invalid. Gaps remain unconnected. Horizontal axis: route distance (km); vertical axis: elevation (m, source vertical reference unresolved).`
    : 'No valid elevation samples are available for this route.';
  svg.setAttribute('aria-label',samples.length?`Sampled elevation profile with ${samples.length} readings and ${missing} gaps`:'Elevation profile unavailable');
  if(samples.length){
    const min=Math.min(...samples.map(p=>p.elevation_m)),max=Math.max(...samples.map(p=>p.elevation_m));
    const span=Math.max(1,max-min);
    const distance=Math.max(Number.EPSILON,...allSamples.map(p=>Number.isFinite(p.distance_km)?p.distance_km:0));
    const x=p=>(p.distance_km/distance*100).toFixed(2);
    const y=p=>(42-(p.elevation_m-min)/span*36).toFixed(2);
    for(const segment of segments){
      const path=document.createElementNS('http://www.w3.org/2000/svg',segment.length>1?'polyline':'circle');
      if(segment.length>1){path.setAttribute('points',segment.map(p=>`${x(p)},${y(p)}`).join(' '));path.setAttribute('fill','none');}
      else{path.setAttribute('cx',x(segment[0]));path.setAttribute('cy',y(segment[0]));path.setAttribute('r','.8');path.setAttribute('fill','#5be7ce');}
      path.setAttribute('stroke','#5be7ce');path.setAttribute('stroke-width','1.2');
      path.setAttribute('vector-effect','non-scaling-stroke');svg.appendChild(path);
    }
  }
}
function updateCard(data){const ids={'route-distance':`Distance: ${data.route_distance_km.toFixed(3)} km`,'route-efficiency':`Efficiency: ${data.route_efficiency_percent.toFixed(2)}%`,'route-risk':`Risk index: ${data.terrain_risk_score.toFixed(2)} / 100`,'route-waypoints':`Waypoints: ${data.waypoint_count}`};Object.entries(ids).forEach(([id,value])=>document.getElementById(id).textContent=value);document.getElementById('route-status').textContent='GLOBAL ROUTE CALCULATED';document.getElementById('route-details').hidden=false;}

  async function requestRoute(token,signal){
    try{
      const params=new URLSearchParams({start_lat:start.lat,start_lon:start.lon,end_lat:end.lat,end_lon:end.lon});
      const data=await json('/api/mission-route?'+params,signal);
      if(token!==generation)return;
      if(data.status!=='success')throw serviceError(data.message||'No route is available for these coordinates.',0,data.status);
      if(!Array.isArray(data.route_coordinates)||data.route_coordinates.length<2||
        data.route_coordinates.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite))||
        !['route_distance_km','direct_distance_km','route_efficiency_percent','terrain_risk_score','waypoint_count'].every(key=>Number.isFinite(data[key])&&data[key]>=0))
        throw serviceError('Route response is incomplete. Please retry.',0,'invalid_response');
      analysis=data;
      updateCard(data);
      const regional=data.route_type==='regional_dem_scale';
      set('route-status',regional?'REGIONAL A* CALCULATED':'GLOBAL A* CALCULATED');
      const h=data.hazard_breakdown||{};
      set('route-hazards',`Hazards along route: Low ${h.low||0} · Moderate ${h.moderate||0} · High ${h.high||0} · Extreme ${h.extreme||0}`);
      showScientificReport(data,regional);
      window.ARESMission.setRoute(data.route_coordinates);
      emit('ares:route-analysis',data);
      status(`${regional?'Regional':'Global + sampled refinement'} MOLA route: ${data.route_distance_km.toFixed(2)} km · ${data.waypoint_count} waypoints. Not rover-safe.`);
      set('coordinate-feedback','Route calculated using NASA MOLA terrain. See scientific report.');
      setPending(false);
    }catch(error){
      if(token!==generation||error.name==='AbortError')return;
      routeFailure(error);
    }
  }
  window.addEventListener('ares:mission',event=>{
    const state=event.detail,key=JSON.stringify([state.start,state.end]);
    if(key===pointsKey&&state.route)return;
    pointsKey=key;generation++;controller?.abort();controller=new AbortController();
    start=state.start;end=state.end;analysis=null;region=null;
    const nextRegionKey=start?JSON.stringify([start.lat,start.lon]):null;
    if(regionKey!==nextRegionKey){regionController?.abort();if(regionKey)regions.delete(regionKey);regionKey=null;regionController=null;}
    const token=generation;
    clearReadouts();setPending(Boolean(end));byId('hazard-focus').disabled=true;
    set('region-status',start?'Loading regional MOLA hazard grid…':'Select a location for coarse-resolution MOLA slope screening.');
    set('region-counts','');emit('ares:region',{data:null,generation});
    if(!start){status('Explore Mars freely, or choose Select Start to place a landing site.');return;}
    status(end?'Analyzing terrain and calculating route…':'Landing site selected. Select a destination.');
    getRegion(start.lat,start.lon).then(data=>{if(token===generation)renderRegion(data);}).catch(error=>{
      if(token!==generation||error.name==='AbortError')return;
      set('region-status',`Regional hazard grid unavailable: ${error.message}`);
    });
    terrainAt(end||start,token,controller.signal);
    // Regional rendering is independent of routing; global journeys never wait for it.
    if(end)requestRoute(token,controller.signal);
  });
  byId('mission-retry')?.addEventListener('click',()=>{if(start&&end)window.ARESMission.setPoints(start,end);});
  byId('globe-reset').addEventListener('click',()=>window.ARESMission.clear());
  byId('hazard-toggle').addEventListener('click',()=>{
    hazardsVisible=!hazardsVisible;set('hazard-toggle',hazardsVisible?'Hide hazards':'Show hazards');
    emit('ares:hazard-visibility',{visible:hazardsVisible});
  });
  byId('hazard-focus').addEventListener('click',()=>{if(region)emit('ares:hazard-focus',{data:region});});
  window.ARESService={getRegion,getState:()=>({generation,region,analysis,hazardsVisible})};
})();
