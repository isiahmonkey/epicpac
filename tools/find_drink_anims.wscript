// find_drink_anims.wscript: lists every Cyberpunk animation that involves drinking (alcohol, bottles, glasses, bars)
// and extracts the .anims files so Claude can retarget them for Token. Run: Tools -> Script Manager -> Run.
const KEY = ['drink','alcohol','whisk','beer','bottle','glass','shot','toast','sip','bar_','_bar','booze','liquor','cheers','pour'];
const SKIP = ['glasses','eyeglass','sunglass','shotgun','screenshot','barrel','bartender_clean'];
function ext(p){ const i=p.lastIndexOf('.'); return i<0?'':p.substring(i+1).toLowerCase(); }
const anims=[], spots=[], ents=[]; let n=0;
const e = wkit.GetArchiveFiles().GetEnumerator();
while (e.MoveNext()) {
  const f=e.Current; if(!f) continue; const p=(''+f.FileName).toLowerCase(); n++;
  const x=ext(p); if (x!=='anims' && x!=='workspot' && x!=='ent') continue;
  if (!KEY.some(k=>p.indexOf(k)>=0) || SKIP.some(k=>p.indexOf(k)>=0)) continue;
  if (x==='anims') { anims.push(p); if (p.indexOf('\\player\\')>=0 || p.indexOf('male_average')>=0 || p.indexOf('\\man_')>=0 || p.indexOf('generic_characters\\male')>=0) wkit.Extract(p); }
  else if (x==='workspot') { spots.push(p); wkit.Extract(p); }
  else if (p.indexOf('\\drink')>=0 || p.indexOf('bottle')>=0 || p.indexOf('glass')>=0) ents.push(p);
}
const ex=anims.filter(p=>p.indexOf('\\player\\')>=0 || p.indexOf('male_average')>=0 || p.indexOf('\\man_')>=0 || p.indexOf('generic_characters\\male')>=0).concat(spots);
wkit.SaveToRaw('find_drink_anims.txt','scanned '+n+' files\n\nANIMS '+anims.length+'\n'+anims.join('\n')+'\n\nWORKSPOTS '+spots.length+'\n'+spots.join('\n')+'\n\nPROP ENTITIES '+ents.length+'\n'+ents.join('\n'));
wkit.SaveToRaw('fetch_extra.txt', ex.join('\n'));
logger.Success('Done: '+anims.length+' animation sets, '+spots.length+' workspots ('+ex.length+' extracted). Now run fetch_for_claude.bat.');
