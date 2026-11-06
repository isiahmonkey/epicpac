import sys,json,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/build')
import os,modres,cr2w,mesh,morph,render,xbm
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
GRADE={'05_bl_espresso':(92,60,44),'06_bl_dark':(58,38,28)}
TONES={'01_ca_pale':((171,155,150),0.0),'05_bl_espresso':((117,98,96),0.8),'06_bl_dark':((63,51,39),0.845)}
TONE=os.environ.get('TONE','05_bl_espresso')
def tint_skin(im,tone):
    # skin.mt: albedo multiplied by TintColor, weighted by TintScale x TintColorMask (done in linear space)
    c,k=TONES[tone]; a=np.asarray(im).astype(np.float32)/255; lin=a[...,:3]**2.2
    m=np.asarray(xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/skin/face/h0_000_base__tintcolormask.xbm')).convert('L').resize(im.size)).astype(np.float32)/255
    t=(np.array(c,np.float32)/255)**2.2; w=(k*m)[...,None]
    out=lin*(1-w)+lin*t*w
    return Image.fromarray(np.dstack([np.clip(out**(1/2.2),0,1)*255,a[...,3:]*255]).astype(np.uint8),'RGBA')
def grade(im,rgb):
    # match the mean skin colour to the target tone in linear space, keeping all pore/shading detail
    a=np.asarray(im).astype(np.float32)/255; lin=a[...,:3]**2.2
    cur=lin.reshape(-1,3).mean(0); tgt=(np.array(rgb,np.float32)/255)**2.2
    out=np.clip(lin*(tgt/cur),0,1)**(1/2.2)
    return Image.fromarray(np.dstack([out*255,a[...,3:]*255]).astype(np.uint8),'RGBA')
skin=grade(skin,GRADE[TONE]) if TONE in GRADE else skin
parts=[]
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
bw=np.asarray(xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/character_customisation_items/eyebrows/textures/heb__base_d08.xbm')).convert('RGBA')).astype(float)
g=bw[...,:3].mean(-1,keepdims=True)/255                      # hair strand shading, black_carbon tint
bt=Image.fromarray(np.dstack([g*np.array([34,31,30]),np.clip((bw[...,3]/255)**0.6*1.3,0,1)*255]).astype(np.uint8),'RGBA')   # preview only: thin strands survive downsampling
for i,s in enumerate(BM['geo']['subs']): parts.append(dict(pos=bp[i],idx=s['idx'],uv=s['uv0'],tex=bt,alpha=2))
cy=mesh.decode(A.extract(F[0x4b02f72835f99a29]))
for s in cy['subs']: parts.append(dict(pos=s['pos'],idx=s['idx'],uv=s['uv0'],color=(70,70,78)))
print('cyber bbox',cy['subs'][0]['pos'].min(0).round(3),cy['subs'][0]['pos'].max(0).round(3))
parts.sort(key=lambda p:p.get('alpha',0)==2)
lo=np.array([-0.13,-0.2,1.45]); hi=np.array([0.13,0.15,1.86])
render.sheet([render.view(parts,yaw=y,size=(440,520),focus=(lo,hi)) for y in (0,-0.7,-1.5708)],'/home/claude/work/staging/head1_%s.png'%TONE)
