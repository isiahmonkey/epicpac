// collect_headset2.wscript: the 3 surface templates (and their textures) the braindance headset's black finish is made of.
// Run: Tools -> Script Manager -> Run, then run fetch_for_claude.bat.
const DIRS = ['base\\surfaces\\materials\\metal\\steel_dented\\',
              'base\\surfaces\\materials\\plastic\\plastic_tech\\',
              'base\\surfaces\\materials\\plastic\\rubber_simple\\'];
const FILES = ['base\\surfaces\\microblends\\stripes_hazard_a.xbm'];
const ex=[];
const e = wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) { const f=e.Current; if(!f) continue; const p=''+f.FileName; const l=p.toLowerCase();
  if (DIRS.some(d=>l.indexOf(d)===0) || FILES.indexOf(l)>=0) { wkit.Extract(p); ex.push(p); } }
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+ex.length+' files extracted. Now run fetch_for_claude.bat.');
