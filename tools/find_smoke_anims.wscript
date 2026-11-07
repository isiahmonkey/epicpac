// find_smoke_anims.wscript: smoking animations (take out / light / drag / ash), plus the cigarette and lighter props
// with their textures, so Claude can build Token's drink-and-smoke idle. Run: Tools -> Script Manager -> Run,
// then run fetch_for_claude.bat.
const KEY=['smok','cigar','lighter','ciggy'];
const SKIP=['female','lipsync','facial','vehicle','_fx','child','_car','sit_','__sit','chair','crowd'];
function ext(p){ const i=p.lastIndexOf('.'); return i<0?'':p.substring(i+1).toLowerCase(); }
function dir(p){ return p.substring(0,p.lastIndexOf('\\')+1); }
const anims=[], spots=[], meshes=[], ex=[], all=[];
const e=wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) { const f=e.Current; if(!f) continue; all.push((''+f.FileName)); }
for (const P of all) {
  const p=P.toLowerCase(), x=ext(p);
  if (!KEY.some(k=>p.indexOf(k)>=0) || SKIP.some(k=>p.indexOf(k)>=0)) continue;
  if (x==='anims' && (p.indexOf('male_average')>=0 || p.indexOf('\\player')>=0 || p.indexOf('male_big')>=0)) { anims.push(P); wkit.Extract(P); ex.push(P); }
  else if (x==='workspot') { spots.push(P); wkit.Extract(P); ex.push(P); }
  else if (x==='mesh' && (p.indexOf('cigarette')>=0 || p.indexOf('lighter')>=0)) meshes.push(P);
}
// props: every cigarette / lighter mesh plus the textures sitting next to it
const pdirs=new Set();
for (const m of meshes) { wkit.Extract(m); ex.push(m); pdirs.add(dir(m.toLowerCase())); }
for (const P of all) { const p=P.toLowerCase(); const x=ext(p);
  if ((x==='xbm'||x==='mi'||x==='mlsetup'||x==='mlmask') && pdirs.has(dir(p).replace(/textures\\$/,''))) { wkit.Extract(P); ex.push(P); }
  else if ((x==='xbm'||x==='mi'||x==='mlsetup'||x==='mlmask') && [...pdirs].some(d=>p.indexOf(d)===0)) { wkit.Extract(P); ex.push(P); } }
wkit.SaveToRaw('find_smoke_anims.txt','ANIMS '+anims.length+'\n'+anims.join('\n')+'\n\nWORKSPOTS '+spots.length+'\n'+spots.join('\n')+'\n\nMESHES '+meshes.length+'\n'+meshes.join('\n'));
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+anims.length+' smoking anims, '+spots.length+' workspots, '+meshes.length+' prop meshes ('+ex.length+' files). Now run fetch_for_claude.bat.');
