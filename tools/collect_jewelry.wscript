// collect_jewelry.wscript  -  STAGING: base-game necklace/chain/cross meshes (Valentino set + all neck items) as modelling references
// Pulls these base-game files AND everything they reference (layer templates, textures) into the ACTIVE project.
// Run: Tools -> Script Manager -> this script -> Run. Takes under a minute.
const Logger = { Info: m=>logger.Info(m), Success: m=>logger.Success(m) };

const MOD_DEPS = [];
{ // every Valentino gang jewelry mesh in the game (male + female versions) - real modelled chains/crosses to reference
  const e=wkit.GetArchiveFiles().GetEnumerator();
  while(e.MoveNext()){ const f=e.Current; if(!f) continue; const p=(''+f.FileName).toLowerCase();
    if(p.endsWith('.mesh') && (p.indexOf('\\gang_valentino\\item\\')>=0 || (p.indexOf('\\item\\')>=0 && /neck|necklace|chain|cross|jewel|pendant|rosary/.test(p)))) MOD_DEPS.push(p); }
  Logger.Info('jewelry meshes: '+MOD_DEPS.length);
}

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
wkit.SaveToRaw('collect_jewelry_manifest.txt', 'ADDED '+added.length+'\n'+added.join('\n')+'\n\nMISSING '+missing.length+'\n'+missing.join('\n'));
Logger.Success('Done. Added '+added.length+' files ('+missing.length+' not found). Manifest: source\\raw\\collect_jewelry_manifest.txt');
