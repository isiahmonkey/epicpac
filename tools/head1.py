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
GRADE={'05_bl_espresso':(92,60,44),'06_bl_dark':(58,38,28),'deep':(66,42,30)}
TONES={'01_ca_pale':((171,155,150),0.0),'05_bl_espresso':((117,98,96),0.8),'06_bl_dark':((63,51,39),0.845)}
TONE=os.environ.get('TONE','deep')
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
for i,s in enumerate(HM['geo']['subs']): parts.append(dict(pos=hp[i],idx=s['idx'],uv=s['uv0'],tex=skin,alpha=0,name='skin'))
def basemorph(fn,w):
    M=morph.load(U+fn); n=[t['name'] for t in M['d']['targets']]; return M,morph.apply(M,{k:v for k,v in w.items() if k in n})
import names
_ea=modres.AR['HighTech_Eyes_pack']; _ef={f['hash']:f for f in _ea.files}
EYE=xbm.load(_ea.extract(_ef[names.fnv('base\\eyes\\textures\\eye_14_diffuse.xbm')])).convert('RGBA'); EYE.save('/home/claude/work/staging/eye14.png')
# dv: iris centred 1.3 mm lower (v grows upward on the eyeball) so the upper lid doesn't cut it
def bake_eye(im,iris_size=0.7373740077018738,r_src=0.165,r_out=0.30,dv=0.040):
    # emulate eye_gradient.mt for a flat bake: iris shrunk by IrisSize (radial remap, sclera kept),
    # limbal ring, cornea 'Blick' reflection and a wet sheen
    a=np.asarray(im).astype(np.float32); Hh,Ww=a.shape[:2]
    yy,xx=np.mgrid[0:Hh,0:Ww].astype(np.float32); u=(xx+0.5)/Ww-0.5; v=(yy+0.5)/Hh-0.5+dv; r=np.sqrt(u*u+v*v)+1e-9
    r_new=r_src*iris_size
    rs=np.where(r<r_new, r/iris_size, np.where(r<r_out, r_src+(r-r_new)*(r_out-r_src)/(r_out-r_new), r))
    sx=np.clip((0.5+u*rs/r)*Ww-0.5,0,Ww-1); sy=np.clip((0.5+v*rs/r)*Hh-0.5,0,Hh-1)
    sy=np.where(r<r_out,sy,np.clip(yy,0,Hh-1))
    x0=np.floor(sx).astype(int); y0=np.floor(sy).astype(int); x1=np.minimum(x0+1,Ww-1); y1=np.minimum(y0+1,Hh-1); fx=(sx-x0)[...,None]; fy=(sy-y0)[...,None]
    o=a[y0,x0]*(1-fx)*(1-fy)+a[y0,x1]*fx*(1-fy)+a[y1,x0]*(1-fx)*fy+a[y1,x1]*fx*fy
    limb=np.exp(-((r-r_new)/(0.012))**2)*0.45; o[...,:3]*=(1-limb[...,None])        # dark limbal ring
    sc=(r>r_new*1.08)&(r<r_out); o[...,:3]=np.where(sc[...,None],o[...,:3]*0.65+np.array([228,222,216])*0.35,o[...,:3])  # cleaner sclera
    g1=np.exp(-(((u+0.035)**2+(v+0.045)**2)/(2*0.011**2)))                      # cornea highlight (key light)
    g2=np.exp(-(((u-0.05)**2+(v-0.02)**2)/(2*0.006**2)))*0.5                     # small secondary blick
    sh=np.exp(-(r/(r_new*1.15))**8)*0.10                                         # wet cornea sheen
    hl=np.clip(g1*0.85+g2+sh,0,1)[...,None]; o[...,:3]=o[...,:3]*(1-hl)+255*hl
    # emission: the saturated red/amber hues of the implant iris + brackets glow faintly
    mx=o[...,:3].max(-1); mn=o[...,:3].min(-1); sat=(mx-mn)/(mx+1e-6)
    em=np.clip((sat-0.45)/0.4,0,1)*np.clip((mx-110)/120,0,1)*(r<r_out*0.95)
    global EYE_EMIT; EYE_EMIT=Image.fromarray(np.dstack([o[...,:3]*em[...,None],np.full(em.shape,255)]).astype(np.uint8),'RGBA')
    return Image.fromarray(np.clip(o,0,255).astype(np.uint8),'RGBA')
EYE=bake_eye(EYE); EYE_EMIT.save('/home/claude/work/staging/eye14_emit.png'); EYE.save('/home/claude/work/staging/eye14_baked.png')
EM,ep=basemorph('he_000_pma__morphs.morphtarget',W)
def fit_sphere(q):
    A=np.c_[2*q,np.ones(len(q))]; b=(q**2).sum(1); x=np.linalg.lstsq(A,b,rcond=None)[0]; c=x[:3]; return c,np.sqrt(x[3]+c@c)
def clear_eyes(H,eye,gap=0.0004):
    # Hades lids were sculpted without the eyeballs: push any lid vertex that cuts into an eyeball back onto its surface
    H=H.copy(); n=0
    for sg in (1,-1):
        c,R=fit_sphere(eye[(eye[:,0]*sg)>0]); v=H-c; d=np.linalg.norm(v,axis=1)
        m=(d<R+gap)&(v[:,1]>-0.25*R)                      # front half only (the socket behind stays)
        H[m]=c+v[m]/d[m,None]*(R+gap); n+=int(m.sum())
    return H,n
if os.environ.get('MORPH','1')=='2' and os.environ.get('CLEAR','1')=='1':
    hp[0],_n=clear_eyes(hp[0],ep[2]); print('lid verts pushed off eyeballs',_n)
_sm=np.asarray(Image.open('/home/claude/work/tex/base/eye_shadow_mask.png')).astype(float)
SHADOW=Image.fromarray(np.dstack([np.full(_sm.shape[:2],8),np.full(_sm.shape[:2],6),np.full(_sm.shape[:2],6),np.clip(_sm[...,0]/255*0.92,0,1)*255]).astype(np.uint8),'RGBA')
for i,s in enumerate(EM['geo']['subs']):
    if i==1:   # eye shadow / wetness shell: occlusion in the corners and under the lid (eyeshadow_base.mi, R channel)
        parts.append(dict(pos=ep[i],idx=s['idx'],uv=s['uv0'],tex=SHADOW,alpha=2,name='eyeshadow')); continue
    if i==0:
        _l=Image.open('/home/claude/work/tex/base/eyelashes_ma_01_lod1.png'); _L=np.asarray(_l.convert('L')).astype(float); _al=np.asarray(_l)[...,3].astype(float) if _l.mode=='RGBA' else np.clip(_L/max(_L.max(),1)*1.15,0,1)*255
        LASH=Image.fromarray(np.dstack([np.full(_L.shape,14),np.full(_L.shape,12),np.full(_L.shape,12),_al]).astype(np.uint8),'RGBA')
        parts.append(dict(pos=ep[i],idx=s['idx'],uv=s['uv0'],tex=LASH,alpha=2,name='lashes'))
    else: parts.append(dict(pos=ep[i],idx=s['idx'],uv=s['uv0'],tex=EYE,alpha=0,emit=EYE_EMIT,name='eyes'))
BM,bp=basemorph('heb_000_pma__morphs.morphtarget',W)
bw=np.asarray(xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/character_customisation_items/eyebrows/textures/heb__base_d08.xbm')).convert('RGBA')).astype(float)
g=bw[...,:3].mean(-1,keepdims=True)/255                      # hair strand shading, black_carbon tint
# brow = soft density underlay (SecondaryDiffuseAlpha, ds08) + individual strands (d08 alpha), black_carbon
_ds=np.asarray(xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/character_customisation_items/eyebrows/textures/heb_wa__base_ds08.xbm')).convert('RGBA').resize(bw.shape[1::-1],Image.BICUBIC)).astype(float)[...,3]/255
_sa=bw[...,3]/255; _a=np.clip(1-(1-_ds*0.75)*(1-_sa),0,1)
_col=np.array([22,19,18.0])*(1-_sa[...,None])+g*np.array([34,31,30])*_sa[...,None]
bt=Image.fromarray(np.dstack([_col,_a*255]).astype(np.uint8),'RGBA')
def vnormals(p,idx):
    t=idx.reshape(-1,3); n=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]); vn=np.zeros_like(p)
    for k in range(3): np.add.at(vn,t[:,k],n)
    return -vn/np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-9)   # CP winding is clockwise: flip to outward
def float_on(p,hpos,hidx,gap=0.0008):
    # decals (brows) were authored for the vanilla head: lift any vertex that sinks into the re-sculpted Hades head
    hn=vnormals(hpos,hidx); d,i=cKDTree(hpos).query(p,k=6); w=1/(d+1e-6); w/=w.sum(1,keepdims=True)
    sp=(hpos[i]*w[...,None]).sum(1); sn=(hn[i]*w[...,None]).sum(1); sn/=np.linalg.norm(sn,axis=1,keepdims=True)
    h=((p-sp)*sn).sum(1); lift=np.clip(gap-h,0,None); return p+sn*lift[:,None],lift
for i,s in enumerate(BM['geo']['subs']):
    q,l=float_on(bp[i],hp[0],HM['geo']['subs'][0]['idx']); print('brow chunk',i,'verts lifted',int((l>0).sum()),'/',len(l),'max %.1f mm'%(l.max()*1000))
    parts.append(dict(pos=q,idx=s['idx'],uv=s['uv0'],tex=bt,alpha=2,name='brows'))
for _p in parts:
    if _p.get('tex') is LASH:
        _p['pos'],_l=float_on(_p['pos'],hp[0],HM['geo']['subs'][0]['idx'],gap=0.0003); print('lash verts lifted',int((_l>0).sum()),'/',len(_l),'max %.1f mm'%(_l.max()*1000))
cy=mesh.decode(A.extract(F[0x4b02f72835f99a29]))
# Takemura neck cyberware: ml_h1_001_ma_cyberware__takemura.mlsetup baked (titanium / cast iron / enamel / red tech plastic)
CWA=np.asarray(Image.open('/home/claude/work/staging/cw_albedo.png').convert('RGB')).astype(np.float32)
_met=np.asarray(Image.open('/home/claude/work/staging/cw_metal.png')).astype(np.float32)[...,None]/255
_rg=np.asarray(Image.open('/home/claude/work/staging/cw_rough.png')).astype(np.float32)[...,None]/255
_n=np.asarray(Image.open('/home/claude/work/staging/cw_n01.png').convert('RGB').resize(CWA.shape[1::-1],Image.BICUBIC)).astype(np.float32)/127.5-1
_nx,_ny=_n[...,0],_n[...,1]
_cav=np.gradient(_nx,axis=1)+np.gradient(_ny,axis=0)                     # normal-map curvature: panel seams / bolt holes
from PIL import ImageFilter as _IF
_cav=np.asarray(Image.fromarray(np.clip(_cav*40+128,0,255).astype(np.uint8)).filter(_IF.GaussianBlur(1.2))).astype(np.float32)/128-1
_emb=0.5*(_nx*-0.6+_ny*0.8)                                                # emboss: GlobalNormal lit from above
shade=np.clip(1+_emb-0.9*np.clip(-_cav,0,1)+0.35*np.clip(_cav,0,1),0.35,1.6)[...,None]
CWT=Image.fromarray(np.clip(CWA*(1+0.35*_met*(1-_rg))*shade,0,255).astype(np.uint8)).convert('RGBA')   # preview: polished metal reads a touch brighter
for s in cy['subs']: parts.append(dict(pos=s['pos'],idx=s['idx'],uv=s['uv0'],tex=CWT,alpha=0,name='cyberware'))
print('cyber bbox',cy['subs'][0]['pos'].min(0).round(3),cy['subs'][0]['pos'].max(0).round(3))
parts.sort(key=lambda p:p.get('alpha',0)==2)
lo=np.array([-0.13,-0.2,1.45]); hi=np.array([0.13,0.15,1.86])
render.sheet([render.view(parts,yaw=y,size=(440,520),focus=(lo,hi)) for y in (0,-0.7,-1.5708)],'/home/claude/work/staging/head1_%s.png'%TONE)
