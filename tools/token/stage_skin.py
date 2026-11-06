"""Run Token's staging with the FULL wardrobe on, and carry CP skin weights onto every part.
Registered parts: weights straight from their source sub-mesh (same vertex order).
Generated parts (rope chain, frizz layer, ...): weights copied from the nearest skinned vertex."""
import os,sys,pickle,numpy as np
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build']
import mesh
REG={}
_dec=mesh.decode
def decode(*a,**k):
    g=_dec(*a,**k)
    for s in g.get('subs',[]):
        if 'ji' in s: s['_bones']=g['bones']; s['_bonepos']=g['bonepos']; REG[id(s['idx'])]=s
    return g
mesh.decode=decode
os.environ.setdefault('MORPH','2'); os.environ.setdefault('TONE','deep')
os.environ.update(BODY='1',GORILLA='black',HAT='1',SHOW_HAT='1',ACC='cross_bracelet_l',
    OUTFIT=os.environ.get('OUTFIT','misfits,jeans,synthpants,hoodie,pants,longfur,furjacket,bolero,walletchain,vinyl,tron,boots,vcross'))
os.chdir('/home/claude/work/staging')
src=open('/home/claude/work/staging/head1.py').read().split('parts.sort(')[0].replace('print(','(lambda *a,**k:None)(')
src=src.replace("_hidefeet=any(","_hidefeet=False and any(")      # keep the feet skin: it becomes its own bodygroup
G={'__name__':'stage'}; exec(compile(src,'head1','exec'),G)
parts=G['parts']
from scipy.spatial import cKDTree
out=[]; miss=[]
for p in parts:
    s=REG.get(id(p['idx']))
    if s is not None and len(s['pos'])==len(p['pos']) and len(s['_bones'])>0:
        p=dict(p,ji=s['ji'],jw=s['jw'],bones=s['_bones'],bonepos=s['_bonepos'],chunk=s.get('chunk'),src_nrm=s.get('nrm'))
    else: miss.append(p)
    out.append(p)
sk=[p for p in out if 'ji' in p]
# extra donors: vanilla male head (+eyes) - has real bone names; warped onto Token's (Hades/Dionysus) face
import cr2w as _c
_H='/mnt/user-data/uploads/characters/head/player_base_heads/player_man_average/h0_000_pma_c__basehead/'
for _f in ('h0_000_pma_c__basehead.mesh','he_000_pma_c__basehead.mesh'):
    _g=_dec(_c.load_loose(_H+_f))
    for _s in _g['subs']:
        sk.append(dict(name='_donor_head',pos=G['warp_from_vanilla'](_s['pos']),ji=_s['ji'],jw=_s['jw'],bones=_g['bones'],bonepos=_g['bonepos']))
# donor cloud for generated parts: every skinned vertex, with its (bones, ji, jw) row
DP=np.concatenate([p['pos'] for p in sk]); DI=np.concatenate([np.full(len(p['pos']),k) for k,p in enumerate(sk)]); DV=np.concatenate([np.arange(len(p['pos'])) for p in sk])
T=cKDTree(DP)
for p in miss:
    _,i=T.query(p['pos']); src_part=[sk[k] for k in DI[i]]
    # unify to one bone list: union of donor bone names
    names=[]; 
    for q in {id(x):x for x in src_part}.values():
        for b in q['bones']:
            if b not in names: names.append(b)
    bp=[None]*len(names)
    for q in {id(x):x for x in src_part}.values():
        for j,b in enumerate(q['bones']):
            k=names.index(b); bp[k]=q['bonepos'][j] if j<len(q['bonepos']) else (0,0,0)
    nk=max(q['ji'].shape[1] for q in src_part)
    ji=np.zeros((len(p['pos']),nk),int); jw=np.zeros((len(p['pos']),nk),np.float32)
    for v,(q,dv) in enumerate(zip(src_part,DV[i])):
        for c in range(q['ji'].shape[1]):
            bi=q['ji'][dv,c]
            if q['jw'][dv,c]<=0 or bi>=len(q['bones']): continue
            ji[v,c]=names.index(q['bones'][bi]); jw[v,c]=q['jw'][dv,c]
    p.update(ji=ji,jw=jw,bones=names,bonepos=bp,chunk=None,derived=True)
bad=[(p['name'],int((p['ji']>=len(p['bones'])).sum())) for p in sk if (p['ji']>=len(p['bones'])).any()]
print('index>=bones (source):',bad[:8])
out=[p for p in out if p['name']!='_donor_head']
print('parts',len(out),'skinned from source',len(sk),'derived (nearest-weights)',len(miss),sorted({p['name'] for p in miss}))
pickle.dump([{k:v for k,v in p.items() if k not in ('tex',)} | {'tex':p.get('tex')} for p in out],open(os.environ.get('STAGED','/home/claude/work/token/staged_parts.pkl'),'wb'))
