import json,sys
out=json.load(open('male_cco.json'))
pre=[l.strip() for l in open('/mnt/user-data/uploads/V_Gmod/New Mods/takemura hades edition.preset') if l.strip()]
def fnv(s):
  h=0xcbf29ce484222325
  for c in s.encode(): h=((h^c)*0x100000001b3)&0xFFFFFFFFFFFFFFFF
  return h
byname={}
for i,(cn,d) in enumerate(out):
  if 'name' in d: byname.setdefault(d['name'],[]).append((i,cn,d))
H={fnv(n):n for n in byname}
res=[]
for l in pre:
  h=int(l.split('#')[1].split(':')[0]); ix=int(l.split(':')[1]); n=H[h]
  for i,cn,d in byname[n]:
    if cn=='gameuiSwitcherInfo':
      o=[x for x in d['options'] if x.get('index',0)==ix]; pick=o[0]['names'] if o else None; rr=None
    elif cn=='gameuiMorphInfo':
      t=[x for x in d.get('morphNames',[]) if x.get('index',0)==ix]; pick=('morph',t[0].get('morphName','<none>') if t else None,d.get('localizedName')); rr=d.get('targets') or {k:v for k,v in d.items() if k not in('morphNames','editTags','localizedName','name','uiSlot','index','randomizeCategory')}
    else:
      df=[x for x in d.get('definitions',[]) if x.get('index',0)==ix]; pick=(df[0].get('name'),df[0].get('localizedName')) if df else None
      rr=d.get('resource',[None,None])[1]
    res.append(dict(slot=n,idx=ix,cls=cn,pick=pick,resource=rr))
json.dump(res,open('preset_resolved.json','w'),indent=1,default=str)
for r in res: print(r['slot'],r['idx'],r['cls'][6:],str(r['pick'])[:150],'|',r['resource'])
