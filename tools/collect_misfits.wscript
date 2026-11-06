// collect_misfits.wscript  -  STAGING: find the vanilla texture Tank_Misfits replaces + the male tank tops (meshes + materials)
// Pulls these base-game files AND everything they reference (layer templates, textures) into the ACTIVE project.
// Run: Tools -> Script Manager -> this script -> Run. Takes under a minute.
const Logger = { Info: m=>logger.Info(m), Success: m=>logger.Success(m) };

const MOD_DEPS = [];
// FNV-1a 64 over lowercase path, 16-bit limbs (no BigInt needed)
function fnv64(str){
  let h=[0x2325,0x8422,0x9ce4,0xcbf2];            // 0xcbf29ce484222325 little-endian limbs
  const P=[0x01b3,0x0000,0x0100,0x0000];          // 0x00000100000001b3
  for(let i=0;i<str.length;i++){
    h[0]^=str.charCodeAt(i)&0xff;
    const r=[0,0,0,0];
    for(let a=0;a<4;a++){ let c=0; for(let b=0;a+b<4;b++){ const t=r[a+b]+h[a]*P[b]+c; r[a+b]=t&0xffff; c=Math.floor(t/65536);} }
    h=r;
  }
  return h;
}
function hx(h){ return h.slice().reverse().map(x=>('0000'+x.toString(16)).slice(-4)).join(''); }
const TARGET='b2b9add34d408bcc';   // Tank_Misfits.archive replaces this vanilla texture
const found=[]; const tanks=[];
{
  const e=wkit.GetArchiveFiles().GetEnumerator();
  while(e.MoveNext()){ const f=e.Current; if(!f) continue; const p=(''+f.FileName).toLowerCase();
    if(p.endsWith('.xbm') && (p.startsWith('base\\characters\\garment\\') || p.indexOf('decal')>=0) && hx(fnv64(p))===TARGET) found.push(p);
    if(p.endsWith('.mesh') && p.indexOf('\\torso\\')>=0 && p.indexOf('tank')>=0 && !/_wa_|pwa|_fa_|woman/.test(p)) tanks.push(p);
  }
}
Logger.Info('Texture match: '+found.join(', ')+' | male tank meshes: '+tanks.length);
MOD_DEPS.push(...found, ...tanks);

const WALK_EXT  = ['mesh','mi','mt','mlsetup','mltemplate','app','ent','inkcc','remt'];
const SKIP_EXT  = ['anims','animgraph','workspot','scene','physicalscene','cookedapp','fb2tl','wem','bk2','streamingsector','streamingblock','csv','json'];

function ext(p){ const i=p.lastIndexOf('.'); return i<0?'':p.substring(i+1).toLowerCase(); }
function isFemale(p){ return /pwa|player_woman|woman_base|_wa_|\\wa_|_pwa_/.test(p); }
function isMale(p){ return /pma|player_man|man_base/.test(p) && !isFemale(p); }

function seedFromPatterns(){
  const seeds=[];
  const e = wkit.GetArchiveFiles().GetEnumerator();
  let n=0;
  while (e.MoveNext()){
    const f=e.Current; if(!f) continue;
    const p=(''+f.FileName).toLowerCase(); n++;
    const x=ext(p);
    if (SKIP_EXT.indexOf(x)>=0) continue;
    if (p.startsWith('base\\characters\\head\\') && isMale(p)) seeds.push(p);
    else if (p.startsWith('base\\characters\\common\\player_base_bodies\\') && isMale(p)) seeds.push(p);
    else if (p.startsWith('base\\characters\\cyberware\\') && !isFemale(p) && /pma|player|\\ma_|_ma_/.test(p)) seeds.push(p);
    else if (x==='inkcc') seeds.push(p);
    else if (x==='rig' && isMale(p)) seeds.push(p);
  }
  Logger.Info('Scanned '+n+' game files, '+seeds.length+' pattern matches');
  return seeds;
}

function depsOf(p){
  if (WALK_EXT.indexOf(ext(p))<0) return [];
  let j=null;
  try { j = wkit.GetFileFromArchive(p, OpenAs.Json); } catch(err) { return []; }
  if (!j) return [];
  const out=[]; const re=/"((?:base|engine|ep1)(?:\\\\[^"\\\\]+)+\.[a-z0-9_]+)"/gi; let m;
  while ((m=re.exec(''+j))!==null){ out.push(m[1].replace(/\\\\/g,'\\').toLowerCase()); }
  return out;
}

const queue = MOD_DEPS.map(s=>s.toLowerCase());
const seen = {}; const added=[]; const missing=[];
while (queue.length){
  const p=queue.shift();
  if (seen[p]) continue; seen[p]=true;
  if (p.indexOf('{')>=0 || p.indexOf('*')>=0) continue;
  const x=ext(p); if (SKIP_EXT.indexOf(x)>=0) continue;
  if (!wkit.FileExistsInArchive(p)) { missing.push(p); continue; }
  wkit.Extract(p); added.push(p);
  if (added.length % 200 === 0) Logger.Info('...added '+added.length+' files');
  for (const d of depsOf(p)) if (!seen[d]) queue.push(d);
}
wkit.SaveToRaw('collect_misfits_manifest.txt', 'MATCH '+found.join(' ; ')+'\nTANKS\n'+tanks.join('\n')+'\n\nADDED '+added.length+'\n'+added.join('\n')+'\n\nMISSING '+missing.length+'\n'+missing.join('\n'));
Logger.Success('Done. Added '+added.length+' files ('+missing.length+' not found). Manifest: source\\raw\\collect_misfits_manifest.txt');
