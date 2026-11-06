// node shot.js scene.glb out.png "yaw,el,d,tx,ty,tz" ...  (env W,H,FOV,EXP,LI) -> out_N.png and out_N_emit.png
const {chromium}=require('playwright'); const path=require('path'),http=require('http'),fs=require('fs');
(async()=>{const [f,out,...views]=process.argv.slice(2); const W=+process.env.W||900,H=+process.env.H||1100;
const glbAbs=path.resolve(f);
const srv=http.createServer((q,s)=>{let u=decodeURIComponent(q.url.split('?')[0]); let fp=u==='/scene.glb'?glbAbs:path.join(__dirname,u);
  fs.readFile(fp,(e,d)=>{if(e){s.writeHead(404);s.end();return} s.writeHead(200,{'Content-Type':fp.endsWith('.html')?'text/html':'application/octet-stream'}); s.end(d)})}).listen(0);
const port=srv.address().port;
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:W,height:H}}); p.on('pageerror',e=>console.log('pageerror',e.message)); const shots=[];
for(const v of views){ const [yaw,el,d,tx,ty,tz]=v.split(',').map(Number);
 for(const em of [0,1]){
  const q=`f=/scene.glb&w=${W}&h=${H}&yaw=${yaw}&el=${el}&d=${d}&emit=${em}`+(isNaN(tx)?'':`&t=[${tx},${ty},${tz}]`)+['FOV','EXP','LI','DBG'].map(k=>process.env[k]?`&${k.toLowerCase()}=${process.env[k]}`:'').join('');
  await p.goto(`http://127.0.0.1:${port}/render.html?`+q); await p.waitForFunction(()=>document.title!=='',null,{timeout:+process.env.TO||600000});
  const t=await p.title(); if(t!=='done'){console.log(t);break}
  const fn=out.replace('.png',`_${shots.length>>1}${em?'_emit':''}.png`); await p.screenshot({path:fn}); shots.push(fn);}}
await b.close(); srv.close(); console.log(shots.join('\n'));})();
