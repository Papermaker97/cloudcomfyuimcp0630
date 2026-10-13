const E=require('./engine.js'),R=require('./rig.js').create(E);const rig=R.build([]);
const W=2000,H=1500;
// photo keypoints (pixels)
const KP={wBa:[655,1150],wBb:[640,1184],wBtip:[350,1335],wFtip:[1048,530],wFmid:[1295,830],tail:[850,375],beak:[1030,680],head:[955,640],keel:[1030,1275]};
const D2R=Math.PI/180;
const PARAMS=[ // name, lo, hi, init
 ['roll',-20,10,-6],['pitch',-25,25,0],['yaw',-8,8,0],
 ['wBflap',-40,30,-6],['wBfwd',-25,25,0],['wBcurl',-40,40,-6],['wBtwist',-90,90,0],
 ['wFflap',20,90,75],['wFfwd',-25,25,15],['wFcurl',-20,140,40],['wFtwist',-60,60,20],
 ['nbow',-45,40,-10],['nside',-40,60,18],['hnod',-30,90,55],['hturn',-60,60,35],['tup',-10,50,40],['tside',-40,40,0],
 ['caz',-200,-120,-155],['cel',14,22,18],['cdist',1.1,9,2.6],['fov',44,52,48],['tx',-0.5,0.5,0],['ty',0.1,0.9,0.5]];
const sem=v=>({b:{roll:v.roll,pitch:v.pitch,yaw:v.yaw},wB:{flap:v.wBflap,fwd:v.wBfwd,curl:v.wBcurl,twist:v.wBtwist},wF:{flap:v.wFflap,fwd:v.wFfwd,curl:v.wFcurl,twist:v.wFtwist},neck:{bow:v.nbow,side:v.nside},head:{nod:v.hnod,turn:v.hturn},tail:{up:v.tup,side:v.tside}});
function project(v,p){const t=[v.tx,v.ty,0];const az=v.caz*D2R,el=v.cel*D2R;const c=[t[0]+v.cdist*Math.cos(el)*Math.cos(az),t[1]+v.cdist*Math.sin(el),t[2]+v.cdist*Math.cos(el)*Math.sin(az)];
 const f=norm(sub(t,c)),r=norm(cross(f,[0,1,0])),u=cross(r,f);const d=sub(p,c);const x=dot(d,r),y=dot(d,u),z=dot(d,f);
 const k=1/Math.tan(v.fov*D2R/2);return [W/2+ (x/z)*k*H/2, H/2-(y/z)*k*H/2];}
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]],dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=a=>{const l=Math.hypot(...a);return a.map(x=>x/l)};
const hk=rig.chains.neck.joints.findIndex(j=>j.id==='h');
function points(v){const q=R.P(sem(v));return {q,pts:{wBtip:R.handlePos(rig,q,'wB'),wFtip:R.handlePos(rig,q,'wF'),wFmid:R.pointPos(rig,q,'wF',2,[0,1.64]),tail:R.handlePos(rig,q,'tail'),beak:R.handlePos(rig,q,'beak'),head:R.pointPos(rig,q,'neck',hk,rig.chains.neck.joints[hk].p),keel:R.pointPos(rig,q,'body',0,[0,0.95]),wBa:R.pointPos(rig,q,'wB',2,[-0.1,1.62]),wBb:R.pointPos(rig,q,'wB',2,[0.1,1.62])}};}
function cost(v,withColl){const {q,pts}=points(v);let e=0;
 const pa=project(v,pts.wBa),pb=project(v,pts.wBb);const d1=(pa[0]-KP.wBa[0])**2+(pa[1]-KP.wBa[1])**2+(pb[0]-KP.wBb[0])**2+(pb[1]-KP.wBb[1])**2,d2=(pa[0]-KP.wBb[0])**2+(pa[1]-KP.wBb[1])**2+(pb[0]-KP.wBa[0])**2+(pb[1]-KP.wBa[1])**2;e+=Math.min(d1,d2);
 for(const k in KP){if(k==='wBa'||k==='wBb')continue;const pr=project(v,pts[k]);if(!isFinite(pr[0])){e+=1e9;continue;}e+=(pr[0]-KP[k][0])**2+(pr[1]-KP[k][1])**2;}
 e=Math.sqrt(e/Object.keys(KP).length);let reg=0;PARAMS.forEach(([n,lo,hi,i])=>{if(['caz','cel','cdist','fov','tx','ty'].includes(n))return;reg+=((v[n]-i)/(hi-lo))**2;});e+=12*reg;if(withColl){const c=R.collisions(rig,q);e+=c.n*40;}return e;}
// coordinate descent with random restarts
let best=null;const rnd=(a,b)=>a+Math.random()*(b-a);
function descend(v0,withColl,iters){let v={...v0},c=cost(v,withColl);const step={};PARAMS.forEach(([n,lo,hi])=>step[n]=(hi-lo)/8);
 for(let it=0;it<iters;it++){let improved=false;for(const [n,lo,hi] of PARAMS){for(const s of [1,-1]){const w={...v};w[n]=Math.max(lo,Math.min(hi,v[n]+s*step[n]));const cw=cost(w,withColl);if(cw<c){v=w;c=cw;improved=true;break;}}}
  if(!improved){let all=true;for(const n in step){step[n]*=0.5;if(step[n]>0.05)all=false;}if(all)break;}}
 return {v,c};}
const init={};PARAMS.forEach(([n,,,i])=>init[n]=i);
const starts=[init];for(let s=0;s<14;s++){const v={};PARAMS.forEach(([n,lo,hi,i])=>v[n]=Math.max(lo,Math.min(hi,i+rnd(-0.35,0.35)*(hi-lo))));starts.push(v);}
for(const s of starts){const r=descend(s,false,400);if(!best||r.c<best.c)best=r;}
console.log('fit px rms',best.c.toFixed(1));
const r2=descend(best.v,true,150);console.log('with collisions penalty',r2.c.toFixed(1),'collisions',R.collisions(rig,points(r2.v).q).n,'pure rms',cost(r2.v,false).toFixed(1));
const v=r2.v;console.log(JSON.stringify(Object.fromEntries(Object.entries(v).map(([k,x])=>[k,+x.toFixed(1)]))));
const {pts}=points(v);for(const k in KP){const pr=project(v,pts[k]);console.log(k,KP[k].join(','),'->',pr.map(x=>x.toFixed(0)).join(','));}
require('fs').writeFileSync('ref/fit.json',JSON.stringify(v));
