// collect_headset.wscript: extracts the vanilla files the Modular Male Headset mod reuses (braindance headset + tactical
// specs materials, decals) so Claude can rebuild the black headset for Token.
// Run: Tools -> Script Manager -> Run, then run fetch_for_claude.bat.
const DIRS = ['base\\characters\\garment\\citizen_casual\\head\\h1_033_specs__braindance\\',
              'base\\characters\\garment\\gang_6thstreet\\head\\h1_052_specs__tactical\\'];
const FILES = ['base\\weapons\\common\\textures\\w_midnight_decal_01_d01.xbm',
               'base\\surfaces\\masks\\decal_normals\\militarism\\militarism_devices_01.mi',
               'base\\materials\\glass.mt'];
const ex=[]; const all=[];
const e = wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) { const f=e.Current; if(!f) continue; all.push(''+f.FileName); }
for (const p of all) { const l=p.toLowerCase(); if (DIRS.some(d=>l.indexOf(d)===0) || FILES.indexOf(l)>=0) { wkit.Extract(p); ex.push(p); } }
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+ex.length+' headset files extracted. Now run fetch_for_claude.bat.');
