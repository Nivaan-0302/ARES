/* Geographic display helpers. Coordinates are [latitude, east-positive longitude]. */
(function () {
  'use strict';
  const radians = Math.PI / 180;
  const vector = p => [Math.cos(p[0]*radians)*Math.cos(p[1]*radians), Math.cos(p[0]*radians)*Math.sin(p[1]*radians), Math.sin(p[0]*radians)];
  function interpolate(a, b, t) {
    const x=vector(a), y=vector(b);
    const dot=Math.max(-1,Math.min(1,x.reduce((s,v,i)=>s+v*y[i],0)));
    const angle=Math.acos(dot);
    let v;
    if (angle < 1e-10) return [...a];
    if (Math.PI-angle < 1e-8) {
      // A deterministic great circle when the endpoints alone do not define one.
      const axis=Math.abs(x[2])<.9?[0,0,1]:[0,1,0];
      const tangent=[axis[1]*x[2]-axis[2]*x[1],axis[2]*x[0]-axis[0]*x[2],axis[0]*x[1]-axis[1]*x[0]];
      const length=Math.hypot(...tangent);
      v=x.map((value,i)=>value*Math.cos(Math.PI*t)+tangent[i]/length*Math.sin(Math.PI*t));
    } else {
      const left=Math.sin((1-t)*angle)/Math.sin(angle), right=Math.sin(t*angle)/Math.sin(angle);
      v=x.map((value,i)=>value*left+y[i]*right);
    }
    return [Math.atan2(v[2],Math.hypot(v[0],v[1]))/radians,Math.atan2(v[1],v[0])/radians];
  }
  function splitRoute(coords) {
    if (!Array.isArray(coords) || coords.length<2) return [];
    // Densification matches the short great-circle arcs used on the globe.
    const points=[coords[0]];
    for(let i=1;i<coords.length;i++) {
      const a=vector(coords[i-1]),b=vector(coords[i]);
      const angle=Math.acos(Math.max(-1,Math.min(1,a.reduce((s,v,j)=>s+v*b[j],0))));
      const steps=Math.max(1,Math.ceil(angle/(Math.PI/180)));
      for(let j=1;j<=steps;j++) points.push(j===steps?coords[i]:interpolate(coords[i-1],coords[i],j/steps));
    }
    const segments=[];
    let segment=[points[0]];
    for(let i=1;i<points.length;i++) {
      const a=points[i-1],b=points[i];
      if(Math.abs(b[1]-a[1])>180) {
        const seam=a[1]>=0?180:-180;
        let low=0,high=1;
        for(let j=0;j<45;j++) {
          const mid=(low+high)/2,p=interpolate(a,b,mid);
          const lon=p[1]+(seam===180&&p[1]<0?360:seam===-180&&p[1]>0?-360:0);
          if((seam===180&&lon<seam)||(seam===-180&&lon>seam))low=mid;else high=mid;
        }
        const latitude=interpolate(a,b,(low+high)/2)[0];
        segment.push([latitude,seam]);segments.push(segment);
        segment=[[latitude,-seam],b];
      } else segment.push(b);
    }
    if(segment.length>1)segments.push(segment);
    return segments;
  }
  // Default THREE.SphereGeometry: u=.25 is longitude 0 in pointVector's convention.
  function reliefColumn(u,width){return Math.min(width-1,Math.floor(((u+.25)%1)*width));}
  // Preserve missing readings as gaps, including invalid/absent distance samples.
  function profileSegments(samples){
    const segments=[];let segment=[];
    for(const sample of samples||[]){
      if(typeof sample?.elevation_m!=='number'||!Number.isFinite(sample.elevation_m)||
         typeof sample.distance_km!=='number'||!Number.isFinite(sample.distance_km)||sample.distance_km<0){
        if(segment.length)segments.push(segment);segment=[];
      }else segment.push(sample);
    }
    if(segment.length)segments.push(segment);
    return segments;
  }
  window.ARESGeometry={interpolate,splitRoute,reliefColumn,profileSegments};
})();
