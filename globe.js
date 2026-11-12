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
renderer.domElement.setAttribute('role','img');
renderer.domElement.setAttribute('aria-label','Interactive Mars globe. Use the coordinate form to select precise locations with a keyboard.');
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
let start = null, end = null;
let hazardPatch = null, hazardOutline = null, hazardVisible = window.ARESService.getState().hazardsVisible, regionalData = null;
const hazardColors = [0x38dca0, 0xffcc55, 0xff844e, 0xe84767];
function clearPatch() {
  if (hazardPatch) {
    scene.remove(hazardPatch);
    hazardPatch.geometry.dispose();
    hazardPatch.material.dispose();
    hazardPatch = null;
  }
  if (hazardOutline) { scene.remove(hazardOutline); hazardOutline.geometry.dispose(); hazardOutline.material.dispose(); hazardOutline = null; }
  regionalData = null;
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
    const level=grid[r][c]; if(level< -1 || level>3)continue;
    counts[level]++;
    const lat0=north-(r/rows)*(north-south), lat1=north-(Math.min(rows,r+step)/rows)*(north-south);
    const lon0=west+(c/cols)*(east-west), lon1=west+(Math.min(cols,c+step)/cols)*(east-west);
    const a=vertex(lat0,lon0),b=vertex(lat0,lon1),d=vertex(lat1,lon0),e=vertex(lat1,lon1);
    const color=level===-1?new THREE.Color(0x64748b):palette[level];
    pushTriangle(a,b,d,color);pushTriangle(b,e,d,color);
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
}
window.addEventListener('ares:hazard-focus',()=>{
  if(!regionalData || host.hidden)return;
  const b=regionalData.bounds;
  const direction=pointVector((b.north+b.south)/2,(b.west+b.east)/2,1).normalize();
  controls.target.set(0,0,0);
  camera.position.copy(direction.multiplyScalar(1.065));
  camera.lookAt(controls.target);
  controls.update();
  status('Zoomed to the regional hazard grid. Green=low, yellow=moderate, orange=high, red=extreme.');
});
window.addEventListener('ares:hazard-visibility',event=>{
  hazardVisible=event.detail.visible;
  if(hazardPatch)hazardPatch.visible=hazardVisible;
  if(hazardOutline)hazardOutline.visible=hazardVisible;
});
window.addEventListener('ares:region',event=>{
  if(event.detail.data)drawHazardPatch(event.detail.data);else clearPatch();
});

function status(text){message.textContent=text;}
function pointVector(lat,lon,r=1.014){const a=lat*Math.PI/180,b=lon*Math.PI/180;return new THREE.Vector3(r*Math.cos(a)*Math.sin(b),r*Math.sin(a),r*Math.cos(a)*Math.cos(b));}
function addMarker(lat,lon,color){const mesh=new THREE.Mesh(new THREE.SphereGeometry(.0022,16,12),new THREE.MeshBasicMaterial({color}));mesh.position.copy(pointVector(lat,lon,1.021));scene.add(mesh);markers.push(mesh);}
function disposeObject(object){
  scene.remove(object);object.geometry?.dispose();
  if(Array.isArray(object.material))object.material.forEach(material=>material.dispose());else object.material?.dispose();
}
function reset(){
  clearPatch();start=null;end=null;
  markers.forEach(disposeObject);markers.length=0;
  if(routeLine){disposeObject(routeLine);routeLine=null;}
}
function drawRoute(coords){if(routeLine){scene.remove(routeLine);routeLine.geometry.dispose();routeLine.material.dispose();routeLine=null;}const vertices=[];for(let i=0;i<coords.length-1;i++){const a=pointVector(...coords[i],1.018).normalize(),b=pointVector(...coords[i+1],1.018).normalize();const angle=a.angleTo(b);const steps=Math.max(1,Math.ceil(angle/.014));for(let j=0;j<steps;j++){const t=j/steps;const v=a.clone().lerp(b,t).normalize().multiplyScalar(1.018);vertices.push(v.x,v.y,v.z);}}const last=pointVector(...coords.at(-1),1.018);vertices.push(last.x,last.y,last.z);const geom=new THREE.BufferGeometry();geom.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));routeLine=new THREE.Line(geom,new THREE.LineBasicMaterial({color:0x66e6ff}));scene.add(routeLine);}
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
function synchronizeGlobe(event){
  const {start:nextStart,end:nextEnd,route}=event.detail;
  const key=JSON.stringify([nextStart,nextEnd]);
  if(key!==previousPointsKey){
    previousPointsKey=key;reset();
    if(nextStart){
      start=nextStart;end=nextEnd;
      addMarker(start.lat,start.lon,0x50e3aa);
      if(end)addMarker(end.lat,end.lon,0xff815b);
      frameMission(start,end);
      const currentRegion=window.ARESService.getState().region;
      if(currentRegion)drawHazardPatch(currentRegion);
    }
  }
  if(route?.length>1)drawRoute(route);
}
window.addEventListener('ares:mission',synchronizeGlobe);
synchronizeGlobe({detail:window.ARESMission.get()});
const existingRegion=window.ARESService.getState().region;
if(existingRegion)drawHazardPatch(existingRegion);
renderer.domElement.addEventListener('webglcontextlost',event=>{
  event.preventDefault();window.ARESViews?.fallback(new Error('WebGL context lost'));
});
async function loadTexture(){try{if(!window.ARESMission.get().start)status('Loading global NASA MOLA elevation visualization…');const response=await fetch('/api/global-relief');if(!response.ok)throw new Error('Global relief unavailable');const data=await response.json();const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=512;const ctx=canvas.getContext('2d');const image=ctx.createImageData(canvas.width,canvas.height);for(let y=0;y<canvas.height;y++){const row=Math.min(data.height-1,Math.floor(y*data.height/canvas.height));for(let x=0;x<canvas.width;x++){const u=x/canvas.width;const col=window.ARESGeometry.reliefColumn(u,data.width);const v=data.values[row][col]/255;const idx=(y*canvas.width+x)*4;const shade=Math.max(0,Math.min(1,(v-.16)/.7));image.data[idx]=Math.round(67+165*shade);image.data[idx+1]=Math.round(36+94*shade);image.data[idx+2]=Math.round(31+66*shade);image.data[idx+3]=255;}}ctx.putImageData(image,0,0);const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;globe.material.map=tex;globe.material.color.set(0xffffff);globe.material.needsUpdate=true;if(!window.ARESMission.get().start)status('MOLA elevation-coloured globe ready. Use Select Start or Select Destination to place mission points.');}catch(err){if(!window.ARESMission.get().start)status(`Globe ready with fallback surface. ${err.message}`);}}
function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);}
let animationFrame=null;
function visible(){return !document.hidden&&!host.hidden&&host.getClientRects().length>0;}
function animate(){animationFrame=null;if(!visible())return;controls.update();renderer.render(scene,camera);animationFrame=requestAnimationFrame(animate);}
function updateVisibility(){
  if(visible()){resize();if(animationFrame===null)animationFrame=requestAnimationFrame(animate);}
  else if(animationFrame!==null){cancelAnimationFrame(animationFrame);animationFrame=null;}
}
new ResizeObserver(updateVisibility).observe(host);
new MutationObserver(updateVisibility).observe(host,{attributes:true,attributeFilter:['hidden']});
document.addEventListener('visibilitychange',updateVisibility);
window.addEventListener('ares:view',updateVisibility);
window.addEventListener('ares:workspace',()=>requestAnimationFrame(updateVisibility));
updateVisibility();loadTexture();
