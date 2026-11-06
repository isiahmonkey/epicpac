import sys,json,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/build')
import modres,cr2w,mesh,morph,render,xbm
from PIL import Image
def morph_segs(segs):
    b=segs[0]; r=cr2w.parse(b); _,d=cr2w.chunk(b,r,0)
    mb=[i for i,(c,_,_) in enumerate(r['chunks']) if c=='rendRenderMorphTargetMeshBlob'][0]; _,md=cr2w.chunk(b,r,mb)
    return dict(segs=segs,r=r,d=d,md=md,geo=mesh.decode(segs,lod=1,blob=md['baseBlob'][1]))
A=modres.AR['Hades_Edition_Takemura_Cyberware__Head']; F={f['hash']:f for f in A.files}
HM=morph_segs(A.extract(F[0x6f945da744b29d05]))
tn=[t['name'] for t in HM['d']['targets']]; print(len(tn),'targets', [n for n in tn if n in('h141','h102','h143','h034')])
W={'h141':1,'h102':1,'h143':1,'h034':1}
U='/mnt/user-data/uploads/characters/head/player_base_heads/player_man_average/'
def xpng(p): return xbm.load(cr2w.load_loose(p)).convert("RGBA")
skin=xpng(U+'h0_000_pma_c__basehead/textures/h0_000_pma_c__basehead_d01.xbm')
parts=[]
import os
from scipy.spatial import cKDTree
def transfer(HMm,w):
    # the Hades head is re-sculpted/re-ordered but keeps vanilla-indexed morph diffs: carry the vanilla deltas over by nearest vertex
    V=morph.load(U+'h0_000_pma__morphs.morphtarget'); vb=V['geo']['subs'][0]['pos']
    vp=morph.apply(V,w)[0]; dv=vp-vb
    a=HMm['geo']['subs'][0]['pos']; d,i=cKDTree(vb).query(a,k=4); wt=1/(d+1e-5); wt/=wt.sum(1,keepdims=True)
    return [a+(dv[i]*wt[...,None]).sum(1)]+[s['pos'] for s in HMm['geo']['subs'][1:]]
def safe_apply(M,w):
    pos=[s['pos'].copy() for s in M['geo']['subs']]
    for n,v in w.items():
        for ci,(idx,dl) in morph.target_deltas(M,n).items():
            if ci<len(pos): ok=idx<len(pos[ci]); pos[ci][idx[ok]]+=v*dl[ok]
    return pos
hp=transfer(HM,{k:v for k,v in W.items() if k in tn}) if os.environ.get('MORPH','1')=='2' else safe_apply(HM,{k:v for k,v in W.items() if k in tn}) if os.environ.get('MORPH','1')=='1' else [s['pos'] for s in HM['geo']['subs']]
for i,s in enumerate(HM['geo']['subs']): parts.append(dict(pos=hp[i],idx=s['idx'],uv=s['uv0'],tex=skin,alpha=0))
def basemorph(fn,w):
    M=morph.load(U+fn); n=[t['name'] for t in M['d']['targets']]; return M,morph.apply(M,{k:v for k,v in w.items() if k in n})
EM,ep=basemorph('he_000_pma__morphs.morphtarget',W)
for i,s in enumerate(EM['geo']['subs']):
    if i==1: continue
    parts.append(dict(pos=ep[i],idx=s['idx'],uv=s['uv0'],color=(25,22,22) if i==0 else (200,40,40)))
BM,bp=basemorph('heb_000_pma__morphs.morphtarget',W)
brow=np.asarray(xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/character_customisation_items/eyebrows/textures/heb__base_d08.xbm')).convert("L")).astype(float)
bt=Image.fromarray(np.dstack([np.full(brow.shape,20),np.full(brow.shape,18),np.full(brow.shape,18),np.clip(brow/brow.max()*1.1,0,1)*255]).astype(np.uint8),'RGBA')
for i,s in enumerate(BM['geo']['subs']): parts.append(dict(pos=bp[i],idx=s['idx'],uv=s['uv0'],tex=bt,alpha=2))
cy=mesh.decode(A.extract(F[0x4b02f72835f99a29]))
for s in cy['subs']: parts.append(dict(pos=s['pos'],idx=s['idx'],uv=s['uv0'],color=(70,70,78)))
print('cyber bbox',cy['subs'][0]['pos'].min(0).round(3),cy['subs'][0]['pos'].max(0).round(3))
parts.sort(key=lambda p:p.get('alpha',0)==2)
lo=np.array([-0.13,-0.2,1.45]); hi=np.array([0.13,0.15,1.86])
render.sheet([render.view(parts,yaw=y,size=(440,520),focus=(lo,hi)) for y in (0,-0.7,-1.5708)],'/home/claude/work/staging/head1_m%s.png'%os.environ.get('MORPH','1'))
