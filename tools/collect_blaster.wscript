// collect_blaster.wscript: the vanilla Malorian Overture rail material the Blade Runner Blaster (Dark) reuses,
// plus every surface template its .mlsetup points at. Run: Tools -> Script Manager -> Run, then fetch_for_claude.bat.
const T='base\\weapons\\firearms\\revolver\\malorian_overture\\entities\\meshes\\textures\\';
const FILES=[T+'ml_w_revolver__malorian_overture__base1_01_rail.mlsetup',T+'ml_w_revolver__malorian_overture__base1_01_rail_masksset.mlmask',
             T+'ml_w_revolver__malorian_overture__base1_01_rail_maskssettpp.mlmask',T+'tpp\\w_revolver__malorian_overture__base1_01_rail_n01.xbm',
             'base\\surfaces\\microblends\\edgewear_01.xbm','base\\surfaces\\microblends\\scratches_horizontal_01.xbm','base\\surfaces\\microblends\\scratches_random_01.xbm',
             'base\\surfaces\\microblends\\swipes_and_smears_a.xbm','base\\surfaces\\microblends\\default.xbm'];
const ex=[];
for (const p of FILES) { if (wkit.FileExistsInArchive(p)) { wkit.Extract(p); ex.push(p); } else logger.Warning('not found '+p); }
// every metal / paint template folder (small): covers whatever the rail .mlsetup references
const e=wkit.GetArchiveFiles().GetEnumerator(); const DIRS=['base\\surfaces\\materials\\metal\\','base\\surfaces\\materials\\paint\\'];
while (e.MoveNext()) { const f=e.Current; if(!f) continue; const p=''+f.FileName; const l=p.toLowerCase();
  if (DIRS.some(d=>l.indexOf(d)===0) && (l.endsWith('.mltemplate') || l.endsWith('.xbm'))) { wkit.Extract(p); ex.push(p); } }
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+ex.length+' files extracted. Now run fetch_for_claude.bat.');
