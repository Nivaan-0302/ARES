/* ARES 3.0 — interactive Mars globe with MOLA elevation-colour texture.
   The globe is a visualization, not photographic satellite imagery. */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const host = document.getElementById('mars-globe');
const message = document.getElementById('globe-message');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 1, 0.005, 100);
camera.position.set(0, 0.5, 3.35);
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
host.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 1.4));
const sunlight = new THREE.DirectionalLight(0xffd4b6, 2.2);
sunlight.position.set(4, 3, 5);scene.add(sunlight);
const globe = new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), new THREE.MeshStandardMaterial({color:0xb85c3c, roughness:1}));
scene.add(globe);
const atmosphere = new THREE.Mesh(new THREE.SphereGeometry(1.022,64,48), new THREE.MeshBasicMaterial({color:0xff7c4d, transparent:true, opacity:0.055, side:THREE.BackSide}));
scene.add(atmosphere);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping=true; controls.dampingFactor=.07;controls.minDistance=1.055;controls.maxDistance=6;
controls.enablePan=false;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const markers = [];
let routeLine = null;
let start = null, end = null, version = 0;
let hazardPatch = null, hazardOutline = null, hazardVisible = true, regionalData = null;
const hazardColors = [0x38dca0, 0xffcc55, 0xff844e, 0xe84767];
const regionStatus = document.getElementById('region-status');
const regionCounts = document.getElementById('region-counts');
const overlayToggle = document.getElementById('hazard-toggle');
function clearPatch() {
  if (hazardPatch) {
    scene.remove(hazardPatch);
    hazardPatch.geometry.dispose();
    hazardPatch.material.dispose();
    hazardPatch = null;
  }
  if (hazardOutline) { scene.remove(hazardOutline); hazardOutline.geometry.dispose(); hazardOutline.material.dispose(); hazardOutline = null; }
  regionalData = null;
  document.getElementById('hazard-focus').disabled = true;
  regionStatus.textContent = 'Select a location to analyze a 0.5° MOLA region.';
  regionCounts.textContent = '';
}
function drawHazardPatch(data) {
  clearPatch();
  regionalData = data;
  const grid = data.hazard_grid, rows = grid.length, cols = grid[0].length;
  const {north,south,west,east} = data.bounds;
  const positions=[], colors=[];
  const palette = hazardColors.map(c => new THREE.Color(c));
  const vertex = (lat,lon) => pointVector(lat,lon,1.012);
  const pushTriangle = (a,b,c,color) => {
    for(const v of [a,b,c]) {positions.push(v.x,v.y,v.z);colors.push(color.r,color.g,color.b);}
  };
  const counts=[0,0,0,0], cellLimit=13000;
  const step=Math.max(1,Math.ceil(Math.sqrt(rows*cols/cellLimit)));
  for(let r=0;r<rows;r+=step) for(let c=0;c<cols;c+=step){
    const level=grid[r][c]; if(level<0 || level>3)continue;
    counts[level]++;
    const lat0=north-(r/rows)*(north-south), lat1=north-(Math.min(rows,r+step)/rows)*(north-south);
    const lon0=west+(c/cols)*(east-west), lon1=west+(Math.min(cols,c+step)/cols)*(east-west);
    const a=vertex(lat0,lon0),b=vertex(lat0,lon1),d=vertex(lat1,lon0),e=vertex(lat1,lon1);
    pushTriangle(a,b,d,palette[level]);pushTriangle(b,e,d,palette[level]);
  }
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  hazardPatch=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:.82,side:THREE.DoubleSide,depthWrite:false}));
  hazardPatch.visible=hazardVisible;scene.add(hazardPatch);
  // Draw an accurate outline of the tiny analysis footprint; do not enlarge the actual cells.
  const outlinePoints=[];
  const segments=24;
  const outlineVertex=(lat,lon)=>pointVector(lat,lon,1.019);
  for(let i=0;i<=segments;i++)outlinePoints.push(outlineVertex(north,west+(east-west)*i/segments));
  for(let i=1;i<=segments;i++)outlinePoints.push(outlineVertex(north-(north-south)*i/segments,east));
  for(let i=1;i<=segments;i++)outlinePoints.push(outlineVertex(south,east-(east-west)*i/segments));
  for(let i=1;i<=segments;i++)outlinePoints.push(outlineVertex(south+(north-south)*i/segments,west));
  hazardOutline=new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(outlinePoints),new THREE.LineBasicMaterial({color:0xffffff,depthTest:false}));
  hazardOutline.visible=hazardVisible;hazardOutline.renderOrder=5;scene.add(hazardOutline);
  document.getElementById('hazard-focus').disabled=false;
  const totals={low:0,moderate:0,high:0,extreme:0,missing:0};
  for(const row of grid)for(const v of row){if(v===0)totals.low++;else if(v===1)totals.moderate++;else if(v===2)totals.high++;else if(v===3)totals.extreme++;else totals.missing++;}
  regionStatus.textContent=`Regional MOLA analysis: ${rows} × ${cols} cells. Click Focus on hazards to zoom in and inspect the grid.`;
  regionCounts.textContent=`Low ${totals.low} · Moderate ${totals.moderate} · High ${totals.high} · Extreme ${totals.extreme} · No data ${totals.missing}`;
}
document.getElementById('hazard-focus').addEventListener('click',()=>{
  if(!regionalData)return;
  const b=regionalData.bounds;
  const direction=pointVector((b.north+b.south)/2,(b.west+b.east)/2,1).normalize();
  controls.target.set(0,0,0);
  camera.position.copy(direction.multiplyScalar(1.065));
  camera.lookAt(controls.target);
  controls.update();
  status('Zoomed to the real 0.5° hazard grid. Green=low, yellow=moderate, orange=high, red=extreme.');
});
overlayToggle.addEventListener('click',()=>{hazardVisible=!hazardVisible;if(hazardPatch)hazardPatch.visible=hazardVisible;if(hazardOutline)hazardOutline.visible=hazardVisible;overlayToggle.textContent=hazardVisible?'Hide hazards':'Show hazards';});
async function analyzeRegion3D(lat,lon,requestVersion){
  regionStatus.textContent='Loading regional MOLA hazard grid…';
  try {
    const response=await fetch(`/api/terrain-region?${new URLSearchParams({lat,lon})}`);
    const data=await response.json();
    if(requestVersion!==version)return;
    if(!response.ok)throw new Error(data.error||'Regional data unavailable');
    drawHazardPatch(data);
  }catch(err){if(requestVersion===version){clearPatch();regionStatus.textContent=`Regional hazard grid unavailable: ${err.message}`;}}
}

function status(text){message.textContent=text;}
function pointVector(lat,lon,r=1.014){const a=lat*Math.PI/180,b=lon*Math.PI/180;return new THREE.Vector3(r*Math.cos(a)*Math.sin(b),r*Math.sin(a),r*Math.cos(a)*Math.cos(b));}
function addMarker(lat,lon,color){const mesh=new THREE.Mesh(new THREE.SphereGeometry(.0022,16,12),new THREE.MeshBasicMaterial({color}));mesh.position.copy(pointVector(lat,lon,1.021));scene.add(mesh);markers.push(mesh);}
function reset(){document.getElementById('scientific-report').hidden=true;clearPatch();resetTerrainCard();version++;start=null;end=null;markers.forEach(m=>scene.remove(m));markers.length=0;if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine=null;}document.getElementById('route-status').textContent='AWAITING MISSION';document.getElementById('route-details').hidden=true;status('Explore Mars freely, or choose Select Start to place a landing site.');}
document.getElementById('globe-reset').addEventListener('click',()=>window.ARESMission.clear());
// ARES 3.0 integration: restore original MOLA terrain telemetry for globe selections.
let terrainRequestVersion = 0;
function resetTerrainCard() {
  terrainRequestVersion++;
  document.getElementById('terrain-status').textContent = 'AWAITING LOCATION';
  document.getElementById('terrain-details').hidden = true;
}
async function analyzeGlobeLocation(lat, lon) {
  const requestVersion = ++terrainRequestVersion;
  const terrainStatus = document.getElementById('terrain-status');
  const terrainDetails = document.getElementById('terrain-details');
  terrainStatus.textContent = 'ANALYZING MOLA…';
  terrainDetails.hidden = true;
  const params = new URLSearchParams({lat: String(lat), lon: String(lon)});
  try {
    const [elevationResponse, slopeResponse] = await Promise.all([
      fetch(`/api/elevation?${params}`),
      fetch(`/api/slope?${params}`)
    ]);
    if (requestVersion !== terrainRequestVersion) return;
    const elevation = await elevationResponse.json();
    const slope = await slopeResponse.json();
    if (requestVersion !== terrainRequestVersion) return;
    const elevationValue = Number(elevation.elevation_m);
    const slopeValue = Number(slope.slope_degrees);
    const elevationOK = elevationResponse.ok && Number.isFinite(elevationValue) && elevation.elevation_m != null;
    const slopeOK = slopeResponse.ok && Number.isFinite(slopeValue) && slope.slope_degrees != null;
    if (!elevationOK && !slopeOK) {
      terrainStatus.textContent = 'DATA UNAVAILABLE';
      terrainDetails.hidden = false;
      document.getElementById('terrain-elevation').textContent = 'Elevation: unavailable at this location';
      document.getElementById('terrain-slope').textContent = 'Slope: unavailable at this location';
      document.getElementById('terrain-hazard').textContent = 'Terrain steepness: unavailable';
      return;
    }
    terrainStatus.textContent = elevationOK && slopeOK ? 'DATA AVAILABLE' : 'PARTIAL DATA';
    terrainDetails.hidden = false;
    document.getElementById('terrain-elevation').textContent = elevationOK
      ? `Elevation: ${elevationValue.toLocaleString()} m` : 'Elevation: unavailable';
    document.getElementById('terrain-slope').textContent = slopeOK
      ? `Estimated slope: ${slopeValue.toFixed(3)}°` : 'Estimated slope: unavailable';
    document.getElementById('terrain-hazard').textContent = slopeOK
      ? `Terrain steepness: ${slope.hazard_level ?? 'unavailable'}` : 'Terrain steepness: unavailable';
  } catch (error) {
    if (requestVersion !== terrainRequestVersion) return;
    terrainStatus.textContent = 'ANALYSIS UNAVAILABLE';
    terrainDetails.hidden = false;
    document.getElementById('terrain-elevation').textContent = 'Could not connect to terrain API';
    document.getElementById('terrain-slope').textContent = '';
    document.getElementById('terrain-hazard').textContent = '';
    console.error('ARES globe terrain analysis:', error);
  }
}
function showScientificReport(data, local){
  const panel=document.getElementById('scientific-report');
  panel.hidden=false;
  const refinement=data.refinement;
  const profile=data.scientific_report;
  document.getElementById('report-scope').textContent=local
    ? 'Regional A* on a 64 × 64 MOLA-derived hazard grid.'
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
  const samples=(profile?.elevation_profile||[]).filter(p=>p.elevation_m!=null);
  if(samples.length>=2){
    const min=Math.min(...samples.map(p=>p.elevation_m)),max=Math.max(...samples.map(p=>p.elevation_m));
    const span=Math.max(1,max-min),distance=Math.max(1,samples.at(-1).distance_km);
    const path=document.createElementNS('http://www.w3.org/2000/svg','polyline');
    path.setAttribute('points',samples.map(p=>`${(p.distance_km/distance*100).toFixed(2)},${(42-(p.elevation_m-min)/span*36).toFixed(2)}`).join(' '));
    path.setAttribute('fill','none');path.setAttribute('stroke','#5be7ce');path.setAttribute('stroke-width','1.2');
    path.setAttribute('vector-effect','non-scaling-stroke');svg.appendChild(path);
  }
}
function updateCard(data){const ids={'route-distance':`Distance: ${data.route_distance_km.toFixed(3)} km`,'route-efficiency':`Efficiency: ${data.route_efficiency_percent.toFixed(2)}%`,'route-risk':`Risk index: ${data.terrain_risk_score.toFixed(2)} / 100`,'route-waypoints':`Waypoints: ${data.waypoint_count}`};Object.entries(ids).forEach(([id,value])=>document.getElementById(id).textContent=value);document.getElementById('route-status').textContent='GLOBAL ROUTE CALCULATED';document.getElementById('route-details').hidden=false;}
function drawRoute(coords){if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine.material.dispose();routeLine=null;}const vertices=[];for(let i=0;i<coords.length-1;i++){const a=pointVector(...coords[i],1.018).normalize(),b=pointVector(...coords[i+1],1.018).normalize();const angle=a.angleTo(b);const steps=Math.max(1,Math.ceil(angle/.014));for(let j=0;j<steps;j++){const t=j/steps;const v=a.clone().lerp(b,t).normalize().multiplyScalar(1.018);vertices.push(v.x,v.y,v.z);}}const last=pointVector(...coords.at(-1),1.018);vertices.push(last.x,last.y,last.z);const geom=new THREE.BufferGeometry();geom.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));routeLine=new THREE.Line(geom,new THREE.LineBasicMaterial({color:0x66e6ff}));scene.add(routeLine);}
async function requestRoute(){
  const thisVersion=version;
  status('Calculating terrain-aware route…');
  document.getElementById('route-status').textContent='CALCULATING…';
  try {
    const params=new URLSearchParams({start_lat:start.lat,start_lon:start.lon,end_lat:end.lat,end_lon:end.lon});
    const response=await fetch(`/api/mission-route?${params}`);
    const data=await response.json();
    if(thisVersion!==version)return;
    if(!response.ok||data.status!=='success')throw new Error(data.message||data.error||'Route unavailable');
    drawRoute(data.route_coordinates);
    updateCard(data);
    window.ARESMission.setRoute(data.route_coordinates);
    const regional=data.route_type==='regional_dem_scale';
    document.getElementById('route-status').textContent=regional?'REGIONAL A* CALCULATED':'GLOBAL A* CALCULATED';
    const breakdown=data.hazard_breakdown || {};
    document.getElementById('route-hazards').textContent=`Hazards along route: Low ${breakdown.low||0} · Moderate ${breakdown.moderate||0} · High ${breakdown.high||0} · Extreme ${breakdown.extreme||0}`;
    showScientificReport(data, regional);
    window.dispatchEvent(new CustomEvent('ares:route-analysis', {detail: data}));
    status(`${regional?'Regional 64×64':'Global 1° + sampled refinement'} MOLA route: ${data.route_distance_km.toFixed(2)} km · ${data.waypoint_count} waypoints. Not rover-safe.`);
    document.getElementById('coordinate-feedback').textContent='Route calculated using NASA MOLA terrain. See scientific report.';
  }catch(err){
    if(thisVersion!==version)return;
    status(`Route unavailable: ${err.message}`);
    document.getElementById('route-status').textContent='ROUTE UNAVAILABLE';
    document.getElementById('coordinate-feedback').textContent=`Route unavailable: ${err.message}`;
  }
}
let down=null;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
renderer.domElement.addEventListener('pointerup',e=>{
  if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>6)return;
  const rect=renderer.domElement.getBoundingClientRect();
  pointer.set(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1);
  raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObject(globe)[0];if(!hit)return;
  const p=hit.point.clone().normalize();
  window.ARESMission.selectPointSafely({lat:Math.asin(p.y)*180/Math.PI,lon:Math.atan2(p.x,p.z)*180/Math.PI});
});
function frameMission(a,b){
  const va=pointVector(a.lat,a.lon,1).normalize();
  const vb=b?pointVector(b.lat,b.lon,1).normalize():va;
  const angle=va.angleTo(vb);
  const direction=va.clone().add(vb);
  if(direction.lengthSq()<1e-8)direction.copy(va);
  direction.normalize();
  // Near endpoints are intentionally close on a planetary globe; zoom to inspect.
  const distance=b?Math.min(5.3,Math.max(1.09,1.13+angle*1.5)):2.3;
  controls.target.set(0,0,0);
  camera.position.copy(direction.multiplyScalar(distance));
  camera.lookAt(controls.target);
  controls.update();
}
let previousPointsKey = '';
window.addEventListener('ares:mission', async event=>{
  const {start: nextStart,end: nextEnd} = event.detail;
  const key=JSON.stringify([nextStart,nextEnd]);
  if(key===previousPointsKey)return; // Route results do not restart calculations.
  previousPointsKey=key;
  reset();
  if(!nextStart)return;
  start=nextStart;end=nextEnd;
  addMarker(start.lat,start.lon,0x50e3aa);
  if(end)addMarker(end.lat,end.lon,0xff815b);
  frameMission(start,end);
  const requestVersion=version;
  status(end?'Analyzing terrain and calculating route…':'Landing site selected. Select destination.');
  // Wait for regional data so nearby coordinate-entered routes use regional A*.
  await analyzeRegion3D(start.lat,start.lon,requestVersion);
  if(requestVersion!==version)return;
  analyzeGlobeLocation(end?.lat??start.lat,end?.lon??start.lon);
  if(end)requestRoute();
});
async function loadTexture(){try{status('Loading global NASA MOLA elevation visualization…');const response=await fetch('/api/global-relief');if(!response.ok)throw new Error('Global relief unavailable');const data=await response.json();const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=512;const ctx=canvas.getContext('2d');const image=ctx.createImageData(canvas.width,canvas.height);for(let y=0;y<canvas.height;y++){const row=Math.min(data.height-1,Math.floor(y*data.height/canvas.height));for(let x=0;x<canvas.width;x++){const u=x/canvas.width;const col=Math.min(data.width-1,Math.floor(((.5-u+1)%1)*data.width));const v=data.values[row][col]/255;const idx=(y*canvas.width+x)*4;const shade=Math.max(0,Math.min(1,(v-.16)/.7));image.data[idx]=Math.round(67+165*shade);image.data[idx+1]=Math.round(36+94*shade);image.data[idx+2]=Math.round(31+66*shade);image.data[idx+3]=255;}}ctx.putImageData(image,0,0);const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;globe.material.map=tex;globe.material.color.set(0xffffff);globe.material.needsUpdate=true;status('MOLA elevation-coloured globe ready. Use Select Start or Select Destination to place mission points.');}catch(err){status(`Globe ready with fallback surface. ${err.message}`);}}
function resize(){const w=host.clientWidth,h=host.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}new ResizeObserver(resize).observe(host);resize();function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}animate();loadTexture();
