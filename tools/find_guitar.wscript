// find_guitar.wscript: guitar props (meshes + their textures/materials) and every guitar-playing animation and
// workspot (NPCs, Kerry, the player), so Claude can give Token a guitar and a playing loop in outfit 2.
// Run: Tools -> Script Manager -> Run, then run fetch_for_claude.bat.
const KEY=['guitar'];
const SKIP=['lipsync','facial','_fx','child','vehicle'];
function ext(p){ const i=p.lastIndexOf('.'); return i<0?'':p.substring(i+1).toLowerCase(); }
function dir(p){ return p.substring(0,p.lastIndexOf('\\')+1); }
const anims=[], spots=[], meshes=[], ents=[], ex=[], all=[];
const e=wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) { const f=e.Current; if(!f) continue; all.push((''+f.FileName)); }
for (const P of all) {
  const p=P.toLowerCase(), x=ext(p);
  if (!KEY.some(k=>p.indexOf(k)>=0) || SKIP.some(k=>p.indexOf(k)>=0)) continue;
  if (x==='anims') { anims.push(P); wkit.Extract(P); ex.push(P); }
  else if (x==='workspot') { spots.push(P); wkit.Extract(P); ex.push(P); }
  else if (x==='mesh') meshes.push(P);
  else if (x==='ent' || x==='app') { ents.push(P); wkit.Extract(P); ex.push(P); }
}
// props: every guitar mesh plus the materials and textures next to it (and in a textures\ subfolder)
const pdirs=new Set();
for (const m of meshes) { wkit.Extract(m); ex.push(m); pdirs.add(dir(m.toLowerCase())); }
for (const P of all) { const p=P.toLowerCase(); const x=ext(p);
  if (x!=='xbm' && x!=='mi' && x!=='mlsetup' && x!=='mlmask' && x!=='mt') continue;
  const d=dir(p);
  if (pdirs.has(d) || pdirs.has(d.replace(/textures\\$/,'')) || [...pdirs].some(q=>d.indexOf(q)===0)) { wkit.Extract(P); ex.push(P); } }
wkit.SaveToRaw('find_guitar.txt','ANIMS '+anims.length+'\n'+anims.join('\n')+'\n\nWORKSPOTS '+spots.length+'\n'+spots.join('\n')+
  '\n\nMESHES '+meshes.length+'\n'+meshes.join('\n')+'\n\nENTS '+ents.length+'\n'+ents.join('\n'));
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+anims.length+' guitar anims, '+spots.length+' workspots, '+meshes.length+' guitar meshes ('+ex.length+' files). Now run fetch_for_claude.bat.');
