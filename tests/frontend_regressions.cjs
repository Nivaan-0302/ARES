/* Run with: node --test tests/frontend_regressions.cjs */
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function environment(){
  const handlers={},elements=new Map(),requests=[],events=[];
  const element=id=>{
    if(!elements.has(id))elements.set(id,{textContent:'',hidden:false,disabled:false,attributes:{},
      setAttribute(name,value){this.attributes[name]=value;},replaceChildren(){},addEventListener:(event,fn)=>{
      handlers[id+':'+event]=fn;
    }});
    return elements.get(id);
  };
  const window={
    addEventListener:(name,fn)=>(handlers[name]??=[]).push(fn),
    dispatchEvent:event=>{events.push(event);for(const fn of handlers[event.type]||[])fn(event);},
    ARESMission:{get:()=>({start:null,end:null,route:null}),clear(){},setRoute(route){window.dispatchEvent({type:'ares:mission',detail:{...state,route}});}}
  };
  let state={start:null,end:null,route:null};
  const select=(start,end)=>{state={start,end,route:null};window.dispatchEvent({type:'ares:mission',detail:state});};
  const document={getElementById:element,createElementNS:()=>({setAttribute(){}})};
  const fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve:(data,status=200)=>resolve({status,ok:status>=200&&status<300,json:async()=>data}),reject}));
  const context={window,document,fetch,AbortController,URLSearchParams,console,
    setTimeout:(fn,delay)=>{const timer=setTimeout(fn,delay);timer.unref();return timer;},clearTimeout,
    CustomEvent:class{constructor(type,init){this.type=type;this.detail=init.detail;}}};
  vm.runInNewContext(read('mission_geometry.js'),context);
  vm.runInNewContext(read('mission_service.js'),context);
  return {window,document,requests,events,select,handlers};
}
test('relief texture longitude agrees with sphere coordinates',()=>{
  const window={};vm.runInNewContext(read('mission_geometry.js'),{window});
  for(const [u,column]of[[0,90],[.25,180],[.5,270],[.75,0]])assert.equal(window.ARESGeometry.reliefColumn(u,360),column);
});
test('two-waypoint dateline crossings retain drawable segments in both directions',()=>{
  const window={};vm.runInNewContext(read('mission_geometry.js'),{window});
  for(const route of [[[0,179],[0,-179]],[[30,-179],[32,179]]]){
    const segments=window.ARESGeometry.splitRoute(route);
    assert.equal(segments.length,2);assert.ok(segments.every(segment=>segment.length>=2));
    for(const segment of segments)for(let i=1;i<segment.length;i++)assert.ok(Math.abs(segment[i][1]-segment[i-1][1])<=180);
    assert.equal(Math.abs(segments[0].at(-1)[1]),180);assert.equal(segments[0].at(-1)[0],segments[1][0][0]);
  }
});
test('analysis starts without a map or WebGL and shares region request across endpoint changes',()=>{
  const e=environment(),a={lat:0,lon:0},b={lat:1,lon:1};
  e.select(a,null);assert.equal(e.requests.filter(r=>r.url.startsWith('/api/terrain-region')).length,1);
  e.select(a,b);
  assert.equal(e.requests.filter(r=>r.url.startsWith('/api/terrain-region')).length,1);
  assert.equal(e.requests.filter(r=>r.url.startsWith('/api/mission-route')).length,1);
  assert.ok(e.requests.some(r=>r.url.startsWith('/api/slope')));
});
test('late region and telemetry responses cannot replace a newer mission',async()=>{
  const e=environment();e.select({lat:0,lon:0},null);
  const old=[...e.requests];e.select({lat:10,lon:10},null);
  const latest=e.requests.slice(old.length);
  const region=x=>({hazard_grid:[[0]],bounds:{north:x+.25,south:x-.25,west:x-.25,east:x+.25}});
  for(const r of latest)r.resolve(r.url.startsWith('/api/terrain-region')?region(10):r.url.startsWith('/api/elevation')?{elevation_m:200}:{slope_degrees:2,hazard_level:'LOW'});
  await tick();
  for(const r of old)r.resolve(r.url.startsWith('/api/terrain-region')?region(0):r.url.startsWith('/api/elevation')?{elevation_m:999}:{slope_degrees:30,hazard_level:'EXTREME'});
  await tick();
  assert.equal(e.window.ARESService.getState().region.bounds.north,10.25);
  assert.match(e.document.getElementById('terrain-elevation').textContent,/200/);
  assert.ok(old[0].options.signal.aborted);
});
test('new missions clear all route and terrain measurements',()=>{
  const e=environment();
  e.document.getElementById('route-distance').textContent='Distance: 123 km';
  e.document.getElementById('ares-live-elevation').textContent='Elevation: 999 m';
  e.select({lat:0,lon:0},null);
  assert.equal(e.document.getElementById('route-distance').textContent,'');
  assert.equal(e.document.getElementById('ares-live-elevation').textContent,'—');
});
test('shared hazard controls emit actions for either renderer',()=>{
  const e=environment();
  e.handlers['hazard-toggle:click']();
  assert.equal(e.window.ARESService.getState().hazardsVisible,false);
  assert.equal(e.events.at(-1).type,'ares:hazard-visibility');
});
test('missing profile readings remain separate segments',()=>{
  const window={};vm.runInNewContext(read('mission_geometry.js'),{window});
  const segments=window.ARESGeometry.profileSegments([
    {distance_km:0,elevation_m:1},{distance_km:1,elevation_m:null},
    {distance_km:2,elevation_m:3},{distance_km:3,elevation_m:4}]);
  assert.equal(segments.length,2);assert.equal(segments[0].length,1);assert.equal(segments[1].length,2);
});
test('busy route reports retryable failure and clears loading state',async()=>{
  const e=environment();e.select({lat:0,lon:0},{lat:1,lon:1});
  e.requests.find(r=>r.url.startsWith('/api/mission-route')).resolve({status:'busy',error:'busy'},503);
  await tick();
  assert.equal(e.document.getElementById('route-status').textContent,'SERVICE BUSY');
  assert.equal(e.document.getElementById('coordinate-form').attributes['aria-busy'],'false');
  assert.equal(e.document.getElementById('mission-retry').hidden,false);
  assert.equal(e.events.at(-1).type,'ares:route-error');
});
