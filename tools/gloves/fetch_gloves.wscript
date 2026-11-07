// fetch_gloves.wscript: base-game textures the Judy tuner gloves (tq mod) use: the glove mask set and normal map,
// the brand decals on the glove, and the little wrist screen. Run: Tools -> Script Manager -> Run, then fetch_for_claude.bat.
const WANT=[
 'base\\characters\\main_npc\\judy\\textures\\ml_g1_001_wa_glove__judy_masksset.mlmask',
 'base\\characters\\main_npc\\judy\\textures\\g1_001_wa_glove__judy_n01.xbm',
 'base\\characters\\common\\textures\\decals\\decals_kangtao_d01.xbm',
 'base\\characters\\common\\textures\\decals\\decals_kangtao_n01.xbm',
 'base\\characters\\common\\textures\\decals\\decals_max_tac_d01.xbm',
 'base\\characters\\common\\textures\\decals\\decals_militech_d01.xbm',
 'base\\characters\\common\\textures\\decals\\decals_militech_n01.xbm',
 'base\\characters\\common\\textures\\decals\\garment_decals_d01.xbm',
 'base\\characters\\common\\textures\\decals\\garment_decals_n01.xbm',
 'base\\materials\\mesh_decal.mt',
 'base\\materials\\screen\\screen_fluff_blue.mi',
 'base\\surfaces\\textures\\screens\\generic\\colorless\\06_civil_16x9_gold.xbm',
 'base\\surfaces\\textures\\screens\\generic\\masks\\06_civil_16x9_scroll_mask.xbm'];
const ex=[]; const all=new Set();
const e=wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) { const f=e.Current; if(!f) continue; all.add((''+f.FileName).toLowerCase()); }
for (const p of WANT) { if (all.has(p.toLowerCase())) { wkit.Extract(p); ex.push(p); } else logger.Warning('not found: '+p); }
// anything else of Judy's glove (mask layers, other variants)
for (const p of all) if (p.indexOf('main_npc\\judy\\textures\\')>=0 && p.indexOf('g1_001_wa_glove__judy')>=0 && ex.indexOf(p)<0) { wkit.Extract(p); ex.push(p); }
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+ex.length+' glove files. Now run fetch_for_claude.bat.');
