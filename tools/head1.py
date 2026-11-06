import os,sys,json,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/build')
import os,modres,cr2w,mesh,morph,render,xbm
from PIL import Image
def morph_segs(segs):
    b=segs[0]; r=cr2w.parse(b); _,d=cr2w.chunk(b,r,0)
    mb=[i for i,(c,_,_) in enumerate(r['chunks']) if c=='rendRenderMorphTargetMeshBlob'][0]; _,md=cr2w.chunk(b,r,mb)
    return dict(segs=segs,r=r,d=d,md=md,geo=mesh.decode(segs,lod=1,blob=md['baseBlob'][1]))
A=modres.AR['Hades_Edition_Takemura_Cyberware__Head']; F={f['hash']:f for f in A.files}
HM=morph_segs(A.extract(F[0x6f945da744b29d05]))
tn=[t['name'] for t in HM['d']['targets']]; print(len(tn),'targets', [n for n in tn if n in('h141','h102','h143','h034')])
FACES={'hades':{'h141':1,'h102':1,'h143':1,'h034':1},          # takemura hades edition.preset
       'dionysus':{'h111':1,'h122':1,'h143':1,'h144':1,'h025':1}}  # PANTHEON_MASC_DIONYSUS.preset (eyes 11, nose 12, mouth 14, jaw 14, ear 2)
FACE=os.environ.get('FACE','dionysus'); W=FACES[FACE]
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
    tgt=(np.array(rgb,np.float32)/255)**2.2
    # luminance-only transfer: the light-skin texture's grey stubble/shadow patches would otherwise turn into black
    # 'makeup' smears on deep skin. Keep its detail (pores, creases) as luminance, take the hue from the target tone.
    Y=lin@np.array([0.2126,0.7152,0.0722],np.float32); Ym=np.median(Y)
    r=(Y/max(Ym,1e-6)); r=np.exp(np.log(np.clip(r,1e-3,None))*0.75)        # soften contrast so stubble zones don't go black
    warm=lin/np.maximum(Y[...,None],1e-6); warm=warm/np.median(warm.reshape(-1,3),0)   # keep a little of the original redness (lips, ears)
    hue=np.clip(1+(warm-1)*0.35,0.6,1.6)
    out=np.clip(tgt*r[...,None]*hue,0,1)**(1/2.2)
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
_sa=np.clip(bw[...,3]/255*1.6,0,1); _ds=np.clip(_ds*1.25,0,1); _a=np.clip(1-(1-_ds*0.92)*(1-_sa),0,1)   # fuller, denser brows on deep skin
_col=np.array([9,8,8.0])*(1-_sa[...,None])+g*np.array([22,20,19])*_sa[...,None]
bt=Image.fromarray(np.dstack([_col,_a*255]).astype(np.uint8),'RGBA')
_st=np.clip(bw[...,3]/255*1.8,0,1)
BROW_STRANDS={k:Image.fromarray(np.dstack([g*np.array([30,27,25])+6,np.clip(_st**1.3*k,0,1)*255]).astype(np.uint8),'RGBA') for k in (0.85,0.6)}
BROW_N=xbm.load(cr2w.load_loose('/mnt/user-data/uploads/characters/common/character_customisation_items/eyebrows/textures/heb__base_n08.xbm')).convert('RGB')
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
    # volume: two raised strand shells (0.7 / 1.4 mm) carrying only the individual hairs, so the brow has depth, not a flat print
    _bn=vnormals(q,s['idx'])
    for _h,_k in ((0.0007,0.85),(0.0014,0.6)):
        parts.append(dict(pos=q+_bn*_h,idx=s['idx'],uv=s['uv0'],tex=BROW_STRANDS[_k],alpha=2,name='brows_s%d'%int(_h*1e4)))
for _p in parts:
    if _p.get('tex') is LASH:
        _p['pos'],_l=float_on(_p['pos'],hp[0],HM['geo']['subs'][0]['idx'],gap=0.0003); print('lash verts lifted',int((_l>0).sum()),'/',len(_l),'max %.1f mm'%(_l.max()*1000))
cy=mesh.decode(A.extract(F[0x4b02f72835f99a29]))
# ---- ANRUI ear cyberware (Base_07..10 are identical; colour/metal/rough/normal come from the customization archives)
def warp_from_vanilla(pts,k=8):
    """carry geometry authored on the vanilla (preset-morphed) head onto the re-sculpted Hades head"""
    global _VW
    if '_VW' not in globals():
        V=morph.load(U+'h0_000_pma__morphs.morphtarget'); vb=morph.apply(V,W)[0]
        _, j=cKDTree(hp[0]).query(vb); disp=hp[0][j]-vb
        dd,ii=cKDTree(vb).query(vb,k=12); ww=1/(dd+1e-4); ww/=ww.sum(1,keepdims=True); disp=(disp[ii]*ww[...,None]).sum(1)   # smooth
        _VW=(cKDTree(vb),disp)
    T,disp=_VW; d,i=T.query(pts,k=k); w=1/(d+1e-4); w/=w.sum(1,keepdims=True); return pts+(disp[i]*w[...,None]).sum(1)
import rdar as _rd
EAR_COLOR=os.environ.get('EAR','Black')
_AN='/mnt/user-data/uploads/V_Gmod/New Mods/ANRUI_EarCyberware_Customization/'
def _anx(sub,idx=0):
    a=_rd.Archive(_AN+sub); fs=[f for f in a.files if a.extract(f)]; return xbm.load(a.extract(fs[idx]))
EAR_D=_anx('Colors/ANRUI_EarCyberware_Color_%s.archive'%EAR_COLOR).convert('RGBA')
EAR_N=_anx('Normals/ANRUI_EarCyberware_Normals_OG.archive',0).convert('RGB')
EAR_M=_anx('Metalness/ANRUI_EarCyberware_Metalness_Full.archive').convert('L'); EAR_R=_anx('Roughness/ANRUI_EarCyberware_Roughness_Half.archive').convert('L')
_ea7=modres.AR['ANRUI_MEarCyberware_Base_07']; _ec=[f for f in _ea7.files if cr2w.parse(_ea7.extract(f)[0])['chunks'][0][0]=='CMesh'][0]
EARG=mesh.decode(_ea7.extract(_ec))
_EA=np.asarray(EAR_D)[...,3]
def tuck_under(H,P,uv,idx,gap=0.0015,reach=0.012):
    # skin under a cyber shell: any head vertex sitting above the visible shell surface is pushed just beneath it
    t=idx.reshape(-1,3); h,w=_EA.shape
    vis=_EA[np.clip((uv[:,1]%1*h).astype(int),0,h-1),np.clip((uv[:,0]%1*w).astype(int),0,w-1)]>100
    if not vis.any(): return H,0
    pn=vnormals(P,idx); c=H.mean(0); pn*=np.sign(((P-c)*pn).sum(1,keepdims=True)+1e-12)   # outward from the head
    tv=t[vis[t].all(1)]                                   # densify: sample points across every visible shell triangle
    bc=np.array([(a,b,1-a-b) for a in np.linspace(0,1,6) for b in np.linspace(0,1,6) if a+b<=1.0001])
    V=np.einsum('kj,tjd->tkd',bc,P[tv]).reshape(-1,3); N=np.einsum('kj,tjd->tkd',bc,pn[tv]).reshape(-1,3); N/=np.linalg.norm(N,axis=1,keepdims=True)
    _hn=vnormals(H,HM['geo']['subs'][0]['idx']); _j=cKDTree(H).query(V)[1]; N=np.where(((N*_hn[_j]).sum(1)<0)[:,None],-N,N)   # orient by the skin it covers
    T=cKDTree(V); d,i=T.query(H)
    m=(d<reach)&(np.abs(H[:,0])>0.055); hgt=((H[m]-V[i[m]])*N[i[m]]).sum(1)   # height of skin above shell (ear region only)
    mv=hgt>-gap; idxm=np.nonzero(m)[0][mv]
    H=H.copy(); H[idxm]-=N[i[idxm]]*(hgt[mv]+gap)[:,None]; return H,len(idxm)
EAR_SIDES=os.environ.get('EAR_SIDES','R')            # CP: +X is the character's RIGHT (l_ joints sit at -X)
for s in EARG['subs']:
    _t=s['idx'].reshape(-1,3); _cx=s['pos'][_t].mean(1)[:,0]
    s=dict(s,idx=_t[((_cx>0) if EAR_SIDES=='R' else (_cx<0) if EAR_SIDES=='L' else np.ones(len(_t),bool))].ravel())
    q=warp_from_vanilla(s['pos']); q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0012)
    hp[0],_n=tuck_under(hp[0],q,s['uv0'],s['idx']); print('ear: skin verts tucked under shell',_n)
    # the Takemura neck piece reaches up behind the ear lobe and pokes through the shell: lift the shell over it
    _cp=cy['subs'][0]['pos']; _near=np.nonzero(cKDTree(_cp).query(q)[0]<0.006)[0]
    if len(_near):
        _cn=vnormals(_cp,cy['subs'][0]['idx']); _c=hp[0].mean(0); _cn*=np.sign(((_cp-_c)*_cn).sum(1,keepdims=True)+1e-12)
        dd,ii=cKDTree(_cp).query(q[_near],k=6); w_=1/(dd+1e-6); w_/=w_.sum(1,keepdims=True)
        sp=(_cp[ii]*w_[...,None]).sum(1); sn=(_cn[ii]*w_[...,None]).sum(1); sn/=np.linalg.norm(sn,axis=1,keepdims=True)
        hh=((q[_near]-sp)*sn).sum(1); lift=np.clip(0.0008-hh,0,0.006); q[_near]+=sn*lift[:,None]; print('ear: shell verts lifted over neck cyberware',int((lift>0).sum()))
    parts[0]['pos']=hp[0]
    parts.append(dict(pos=q,idx=s['idx'],uv=s['uv0'],tex=EAR_D,alpha=2,name='earcyber'))
# ---- Hair: Half Bun Dreads (Male V), black_carbon (hair.mt cards + gradient-recoloured cap decal)
def _hgrad(entries,x):
    e=sorted([(d.get('value',0.0),np.array([d.get('color',{}).get(k,0) for k in ('Red','Green','Blue')],float)) for d in entries],key=lambda t:t[0])
    xs=np.array([v for v,_ in e]); cs=np.array([c for _,c in e]); return np.stack([np.interp(x,xs,cs[:,k]) for k in range(3)],-1)
_HU='/mnt/user-data/uploads/characters/common/hair/'
_hpb=open(_HU+'textures/hair_profiles/black_carbon.hp','rb').read(); _hpr=cr2w.parse(_hpb); HPROF=cr2w.chunk(_hpb,_hpr,0)[1]
def _hl(f,size=None):
    im=xbm.load(cr2w.load_loose(_HU+f)).convert('L'); im=im.resize(size,Image.LANCZOS) if size else im; return np.asarray(im).astype(np.float32)/255
HAIR=os.environ.get('HAIR','keelan')
def hair_cards(ha,hi,hg):
    # hair.mt: strand colour = ID gradient (per-strand tint) x root-to-tip gradient (black_carbon profile)
    hc=_hgrad(HPROF['gradientEntriesID'],hi)/255*_hgrad(HPROF['gradientEntriesRootToTip'],hg); hc*=(0.80+0.20*np.clip(ha*1.4,0,1))[...,None]; hc*=0.62   # CP hair.mt reads black_carbon far darker than the raw profile (strand self-shadowing)
    return Image.fromarray(np.dstack([np.clip(hc,0,255),ha*255]).astype(np.uint8),'RGBA')
_gm=np.asarray(xbm.load(cr2w.load_loose(_HU+'textures/cap_gradiants/hh_cap_grad__black_carbon.xbm')).convert('RGB')).astype(np.float32)[1]
def hair_cap(cd,cm):     # mesh_decal_gradientmap_recolor
    gx=np.clip((cd*(len(_gm)-1)).astype(int),0,len(_gm)-1); return Image.fromarray(np.dstack([_gm[gx],cm*255]).astype(np.uint8),'RGBA')
def _L(im,size=None): im=im.convert('L'); im=im.resize(size,Image.LANCZOS) if size else im; return np.asarray(im).astype(np.float32)/255
if HAIR=='dreads':
    _ha=_hl('textures/hh_dread01_alpha01_r.xbm'); _sz=_ha.shape[::-1]
    HAIR_CARDS=hair_cards(_ha,_hl('textures/hh_dread01_id01_r.xbm',_sz),_hl('textures/hh_dread01_grad01_r.xbm',_sz))
    _cd=_hl('hh_060_wa__voodoo_03/textures/hh_60_wa__voodoo_03_cap_d02.xbm'); HAIR_CAP=hair_cap(_cd,_hl('hh_060_wa__voodoo_03/textures/hh_60_wa__voodoo_03_cap_mask.xbm',_cd.shape[::-1]))
    _hs=mesh.decode(modres.get('base\\characters\\common\\hair\\hh_060_wa__voodoo_03\\hh_060_ma__voodoo_03.mesh'))['subs']; HSUBS=[(_hs[0],'hair'),(_hs[1],'haircap')]
else:   # MELUMINARY CCXL "Keelan" top locs (ArchiveXL @long/@cap dynamic materials -> black_carbon)
    import rdar as _rd2
    _ka=_rd2.Archive('/home/claude/work/new1/src/mods/MELUMINARY_KEELAN_TOP_LOCS.archive'); _kf={f['hash']:f for f in _ka.files}
    _kx=lambda p: xbm.load(_ka.extract(_kf[names.fnv(p.lower())]))
    _K='base\\mel_ccxl_hair\\materials\\custom_tx\\'
    _ha=_L(_kx(_K+'keelan001_alpha.xbm')); _sz=_ha.shape[::-1]
    HAIR_CARDS=hair_cards(_ha,_L(_kx(_K+'keelan001_id.xbm'),_sz),_L(_kx(_K+'keelan001_grad.xbm'),_sz))
    _cd=_L(_kx(_K+'hh_201_wa__dawn_cap_d02.xbm')); HAIR_CAP=hair_cap(_cd,_L(_kx(_K+'hh_201_wa__dawn_cap_mask.xbm'),_cd.shape[::-1]))
    _km=lambda p: mesh.decode(_ka.extract(_kf[names.fnv(p.lower())]))['subs']
    HSUBS=[(_km('base\\mel_ccxl_hair\\meshes\\keelan001_hair_pt1.mesh')[0],'hair'),(_km('base\\mel_ccxl_hair\\meshes\\keelan001_hair_pt2.mesh')[0],'haircap')]
if os.environ.get('HIDE_HAIR','0')=='1': HSUBS=[]
for _s,_nm in HSUBS:
    q=warp_from_vanilla(_s['pos'],k=6)
    if _nm=='haircap': q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0005)
    parts.append(dict(pos=q,idx=_s['idx'],uv=_s['uv0'],tex=HAIR_CARDS if _nm=='hair' else HAIR_CAP,alpha=2,name=_nm))
# ---- Kwek simple cross earrings (earrings_06, kwek_silver) - LEFT ear only (-X); dyng_earring_left_01/02 dangle in CP
import rdar as _rd3
_kw=_rd3.Archive('/home/claude/work/new1/src/mods/kwek_earrings06.archive'); _kwf={f['hash']:f for f in _kw.files}
EARRING=mesh.decode(_kw.extract(_kwf[names.fnv('kwek\\items\\clothing\\face\\earrings_06\\earrings_06.mesh')]))['subs'][0]
_et=EARRING['idx'].reshape(-1,3); _keep=EARRING['pos'][_et].mean(1)[:,0]<0
_ER=dict(EARRING,idx=_et[_keep].ravel())
# rigid: a per-vertex warp bends the metal, so move the whole earring by the warp at its hoop (top), then seat the hoop
_used=np.unique(_ER['idx']); _top=_used[np.argsort(_ER['pos'][_used,2])[-12:]]
_d=(warp_from_vanilla(_ER['pos'][_top])-_ER['pos'][_top]).mean(0)
EARRING_LIFT=float(os.environ.get('EARRING_LIFT','0.005'))          # hoop up into the lobe so it reads as pierced
_q=_ER['pos']+_d+np.array([0,0,EARRING_LIFT])
parts.append(dict(pos=_q,idx=_ER['idx'],uv=_ER['uv0'],tex=Image.open('/home/claude/work/staging/ear06_albedo.png').convert('RGBA'),alpha=0,name='earring'))
# ---- axellysse fur hat (hat_fur_m_base_body.mesh), black_carbon: fur cards on hair.mt (hh_short01 + black_carbon.hp) + cap
HAT=os.environ.get('HAT','1')=='1'
HAT_GEO=HAT and os.environ.get('SHOW_HAT','1')=='1'   # SHOW_HAT=0: keep the black_carbon fur materials (fur jacket uses them) but hide the hat itself
if HAT:
    _fa=modres.AR['axellysse_fur_collection']; _ff={f['hash']:f for f in _fa.files}
    _hat=mesh.decode(_fa.extract(_ff[names.fnv('axellysse\\fur_collection\\mesh\\hat_fur_m_base_body.mesh')]))['subs']
    _fla=_hl('textures/hh_short01_alpha01_r.xbm'); _fsz=_fla.shape[::-1]
    HAT_CARDS=hair_cards(_fla,_hl('textures/hh_short01_id01_r.xbm',_fsz),_hl('textures/hh_short01_grad01_r.xbm',_fsz))
    _capm=os.path.exists('/mnt/user-data/uploads/characters/garment/citizen_fashion/torso/t1_104_dress__golden/textures/t1_104_wa_dress__golden_black_carbon__cap.mi')
    # garment fur = the real black_carbon profile (near-black roots -> warm grey-brown tips), made frizzy:
    _jc=np.asarray(HAT_CARDS).astype(np.float32); _H,_W=_jc.shape[:2]; _rng=np.random.default_rng(7)
    _sn=np.repeat(_rng.random((1,_W)),_H,0); _sn=np.asarray(Image.fromarray((_sn*255).astype(np.uint8)).resize((_W,_H))).astype(np.float32)/255   # per-strand random
    _v=np.linspace(0,1,_H)[:,None]
    _brk=(_rng.random((_H//6+1,_W))>0.10).repeat(6,0)[:_H]            # broken / split strands
    _jc[...,3]*=np.where(_v>0.55,_brk,1)*(0.75+0.25*_sn)                # thinned, ragged tips
    _jc[...,:3]*=(0.75+0.5*_sn[...,None])                               # strand-to-strand value variation (no uniform sheet)
    JACKET_CARDS=Image.fromarray(np.clip(_jc,0,255).astype(np.uint8),'RGBA')
    _fd=os.path.join('/mnt/user-data/uploads/characters/garment/citizen_fashion/torso/t1_104_dress__golden/textures/','t1_104_dress__golden_fur_d02.xbm')
    JACKET_CAP=hair_cap(np.tile(np.asarray(xbm.load(cr2w.load_loose(_fd)).convert('L')).astype(np.float32)/255,(2,2)),np.ones((1024,1024))) if os.path.exists(_fd) else None   # black_carbon cap = gradient-map recolour of the fur detail
    HAT_CAP=Image.new('RGBA',(64,64),tuple(int(x) for x in _gm[1])+(255,))   # under-fur skin layer: darkest black_carbon cap tone (the t1_104 cap mi is a near-uniform root colour)
    for _k,_s in enumerate(_hat):
        q=warp_from_vanilla(_s['pos'],k=6)
        if _k==0: q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0008)
        if HAT_GEO: parts.append(dict(pos=q,idx=_s['idx'],uv=_s['uv0'],tex=HAT_CAP if _k==0 else HAT_CARDS,alpha=0 if _k==0 else 2,name='hatcap' if _k==0 else 'hatfur'))
# ---- Emmerich's face cyberware (CC cyberware_13: face plate on tattoo_06 decal + nose plate on freckles_01 decal), painted BLACK
FACE_CW=os.environ.get('FACE_CW','1')=='1'
if FACE_CW:
    import json as _js
    _P=_js.load(open('/home/claude/work/build/parts.json')); _T='/home/claude/work/tex/base/'
    _CW={'face':dict(d='hx_cyberware_13_n02',n='hx_cyberware_13_m02',m='hx_cyberware_13_d03',r='hx_cyberware_13_r02',k='hx_cyberware_13_d04'),   # decoded from cyberware_13 *.mi
         'nose':dict(d='hx_cyberware_13_n01',n='hx_cyberware_13_d02',m='hx_cyberware_13_r01',r='hx_cyberware_13_m01',k='hx_cyberware_13_d01')}
    def _cwL(n,sz=None): im=Image.open(_T+n+'.png').convert('L'); im=im.resize(sz,Image.LANCZOS) if sz else im; return np.asarray(im).astype(np.float32)/255
    FACECW={}
    for _k,_pk in (('face','cw13_face'),('nose','cw13_nose')):
        c=_CW[_k]; dimg=Image.open(_T+c['d']+'.png').convert('RGB'); sz=dimg.size
        met=_cwL(c['k'],sz); msk=_cwL(c['m'],sz); rgh=_cwL(c['r'],sz)
        from PIL import ImageFilter as _IF
        rim=np.clip(msk-met,0,1); rim=np.asarray(Image.fromarray((rim*255).astype(np.uint8)).filter(_IF.GaussianBlur(3))).astype(np.float32)/255
        a=np.maximum(met,rim*0.55)
        # plates: black paint (was pearl-white chrome);  incision rims: darkened deep skin
        paint=np.array([11,11,12.0]); rimc=np.array([30,19,14.0])
        rgb=paint*met[...,None]+rimc*(1-met[...,None])
        FACECW[_k]=dict(base=Image.fromarray(np.dstack([rgb,a*255]).astype(np.uint8),'RGBA'),
                       normal=Image.open(_T+c['n']+'.png').convert('RGB'),
                       rough=Image.fromarray((np.clip(0.28+0.25*rgh,0,1)*255).astype(np.uint8)),   # glossy lacquer
                       metal=Image.fromarray((met*0.15*255).astype(np.uint8)))                      # paint over metal: mostly dielectric
        M_=morph.load(_P[_pk]['morph']); nm=[t['name'] for t in M_['d']['targets']]; pp=morph.apply(M_,{a_:b_ for a_,b_ in W.items() if a_ in nm})
        for i,sb in enumerate(M_['geo']['subs']):
            q=warp_from_vanilla(pp[i]); q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0004)
            parts.append(dict(pos=q,idx=sb['idx'],uv=sb['uv0'],tex=FACECW[_k]['base'],alpha=2,name='facecw_'+_k))
# ---- Emmerich's piercing (CC piercings set 03: i1_000_pma_c__basehead_earring_03, plastic_black = nose ring)
if os.environ.get('PIERCING','1')=='1':
    import json as _js2, collections as _co
    _PP=_js2.load(open('/home/claude/work/build/parts.json'))['piercing']
    _MP=morph.load(_PP['morph']); _nm=[t['name'] for t in _MP['d']['targets']]; _pp=morph.apply(_MP,{a_:b_ for a_,b_ in W.items() if a_ in _nm})
    for i,sb in enumerate(_MP['geo']['subs']):
        p=_pp[i]; t=sb['idx'].reshape(-1,3); par=np.arange(len(p))
        def _f(a):
            while par[a]!=a: par[a]=par[par[a]]; a=par[a]
            return a
        for a,b,c in t:
            for y in (b,c): ra,rb=_f(a),_f(y); par[ra]=rb
        roots=np.array([_f(k) for k in range(len(p))]); q=p.copy()
        for r_ in np.unique(roots):                      # rigid per ring: translate each piece by the warp at its centre
            m_=roots==r_; c_=p[m_].mean(0,keepdims=True); q[m_]=p[m_]+(warp_from_vanilla(c_)-c_)
        parts.append(dict(pos=q,idx=sb['idx'],uv=sb['uv0'],color=(18,18,20),tex=Image.new('RGBA',(4,4),(16,16,18,255)),alpha=0,name='piercing'))
# ---- ANRUI "Maine" face cyberware (MeshM, own morphtarget -> follows the face shape); colour set via MAINE env
MAINE=os.environ.get('MAINE','Color/Black Line/ANRUI_Maine_Cyberware_Color_BRed.archive')
if MAINE:
    import rdar as _rd4
    _MA='/mnt/user-data/uploads/V_Gmod/New Mods/ARCHIVES/'
    _ma=_rd4.Archive(_MA+'Mesh/MeshM/ANRUI_Maine_Cyberware_MeshM_01.archive')
    _segs={cr2w.parse(_ma.extract(f)[0])['chunks'][0][0]:_ma.extract(f) for f in _ma.files}
    _mm=morph.load.__globals__['mesh']  # noqa
    _b=_segs['MorphTargetMesh']; _r=cr2w.parse(_b[0]); _d=cr2w.chunk(_b[0],_r,0)[1]
    _mbi=[i for i,(c,_,_) in enumerate(_r['chunks']) if c=='rendRenderMorphTargetMeshBlob'][0]; _md=cr2w.chunk(_b[0],_r,_mbi)[1]
    _MM=dict(segs=_b,r=_r,d=_d,md=_md,geo=mesh.decode(_b,lod=1,blob=_md['baseBlob'][1]))
    _nm=[t['name'] for t in _d['targets']]; _mp=safe_apply(_MM,{a_:b_ for a_,b_ in W.items() if a_ in _nm})
    MAINE_D=xbm.load(_rd4.Archive(_MA+MAINE).extract([f for f in _rd4.Archive(_MA+MAINE).files][0])).convert('RGBA')
    _mA=np.asarray(MAINE_D).copy(); _mA[...,3]=np.where(_mA[...,3]<12,0,_mA[...,3]); MAINE_D=Image.fromarray(_mA,'RGBA')   # kill faint white haze
    for i,sb in enumerate(_MM['geo']['subs']):
        q=warp_from_vanilla(_mp[i]); q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0005)
        parts.append(dict(pos=q,idx=sb['idx'],uv=sb['uv0'],tex=MAINE_D,alpha=2,name='maine'))
# ---- BODY: player_man_average base body (censored skin texture) + HQ arms + nails, graded to the same deep tone as the head
BODY=os.environ.get('BODY','0')=='1'
if BODY:
    _B='/mnt/user-data/uploads/characters/common/player_base_bodies/player_man_average/'; _TB='/home/claude/work/tex/base/'
    _tone=GRADE.get(TONE,(66,42,30))
    BODY_D=grade(Image.open(_TB+'t0_000_ma__c_base_d03_censored.png').convert('RGBA'),_tone)
    ARMS_D=grade(Image.open(_TB+'a0_000_ma__c_base_hq_d01.png').convert('RGBA'),_tone)
    TATTOO=os.environ.get('TATTOO','1')=='1'     # VTK Malvina (Female V) transferred to the male body/arm UVs
    if TATTOO:
        def _ink(d,t):
            t=Image.open(t).resize(d.size,Image.LANCZOS); a=np.asarray(t)[...,3].astype(np.float32)/255*0.9   # healed ink, not marker-flat
            o=np.asarray(d).astype(np.float32); o[...,:3]=o[...,:3]*(1-a[...,None])+np.array([13,13,17])*a[...,None]; return Image.fromarray(o.astype(np.uint8),'RGBA')
        BODY_D=_ink(BODY_D,'/home/claude/work/tattoo/male_body_tattoo.png'); ARMS_D=_ink(ARMS_D,'/home/claude/work/tattoo/male_arms_tattoo.png')
    BODY_N=Image.open(_TB+'t0_000_ma__c_base_n03_censored.png').convert('RGB'); ARMS_N=Image.open(_TB+'a0_000_ma_base__hq_nd01.png').convert('RGB')
    _hidefeet=any(x in os.environ.get('OUTFIT','').split(',') for x in ('platform','boots'))
    for s_ in mesh.decode(cr2w.load_loose(_B+'t0_000_pma_base__full.mesh'))['subs']:
        if _hidefeet and s_['chunk']==7: continue
        parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],tex=BODY_D,alpha=0,name='body'))
    GORILLA=os.environ.get('GORILLA','')        # '', 'black', 'silver' -> both arms Gorilla Arms (TPP holstered)
    import mats as _mats
    _GA='/mnt/user-data/uploads/characters/cyberware/player/a0_005__strongarms/entities/meshes/'
    import garments as _gmt
    def _dx(p): return xbm.load(_gmt.segs_of(p)).convert('RGBA')
    _GT='base\\characters\\cyberware\\player\\a0_005__strongarms\\entities\\meshes\\textures\\'; _DT='base\\characters\\common\\textures\\decals\\'
    _fists=_dx(_DT+'decals_gorilla_fists_d01.xbm')
    if GORILLA=='black': _fa=np.asarray(_fists).copy(); _fa[...,:3]=(_fa[...,:3]*0.12).astype(np.uint8); _fists=Image.fromarray(_fa,'RGBA')   # black arms: dark tape/print
    GA_DEC={'decal_holstered_forearm_01':_dx(_GT+'a0_005_ma__strongarms_v2_dec_04_d01.xbm'),'decal_holes':_dx(_GT+'a0_005_ma__strongarms_v2_dec_04_d01.xbm'),
            'decal_tapes2':_fists,'decal_hand_top':_fists,'decal_cyberware_text':_fists,
            'decal_under_cyberware':_dx(_GT+'a0_005_wa__strongarms_cyberware_dec_01_d01.xbm'),'decal_betewwn_fingers':_dx(_GT+'a0_005_wa__strongarms_cyberware_dec_02_d01.xbm')} if GORILLA else {}
    if GORILLA=='black':
        for _k in list(GA_DEC): _a=np.asarray(GA_DEC[_k]).copy(); _a[...,:3]=(_a[...,:3]*0.12).astype(np.uint8); GA_DEC[_k]=Image.fromarray(_a,'RGBA')
    for side in 'lr':
        if not GORILLA and False: pass
        if not GORILLA:
            for k_,s_ in enumerate(mesh.decode(cr2w.load_loose(_B+'arms_hq/a0_000_pma_base_hq__%s.mesh'%side))['subs'][:3]):
                parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],tex=ARMS_D,alpha=0,name='arms'))
            continue
        _sg=cr2w.load_loose(_GA+'a0_005_ma__strongarms_holstered_%s.mesh'%side); _ch,_=_mats.appearance_refs(_sg,'default')
        for s_ in mesh.decode(_sg)['subs']:
            mn=_ch[s_['chunk']] if s_['chunk']<len(_ch) else ''
            nm='arms' if mn.startswith(('arm','forearm')) else 'ga_fingers' if mn=='fingers' else 'ga_end' if 'strongarms_end' in mn else 'ga_glass' if mn=='glass' else None
            if mn in GA_DEC: nm='ga_dec_'+mn
            if nm: parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],tex=GA_DEC.get(mn,ARMS_D),alpha=2 if mn in GA_DEC else 0,name=nm))
        for s_ in mesh.decode(cr2w.load_loose(_GA+'a0_005_ma__strongarms_holstered_cyberware_%s.mesh'%side))['subs']:
            parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],tex=ARMS_D,alpha=0,name='ga_cyber'))
        if GORILLA: continue                     # Gorilla fingers are cyber: no organic nails (they floated off the fingertips)
        for s_ in mesh.decode(cr2w.load_loose(_B+'arms_hq/nails/a0_000_pma_base__nails_%s.mesh'%side))['subs']:
            parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],tex=Image.new('RGBA',(4,4),(74,52,44,255)),alpha=0,name='nails'))
# ---- OUTFIT: PinkyDude Denim Edgerunner (hoodie + pants + chain) + yusei platform ankle boots (black)
OUTFIT=[x for x in os.environ.get('OUTFIT','').split(',') if x]
if OUTFIT and BODY:
    import rdar as _rd5
    _dn=_rd5.Archive('/home/claude/work/new1/src/mods/PinkyDude_DenimEdgerunner.archive'); _dnf={f['hash']:f for f in _dn.files}
    _dx2=lambda p: xbm.load(_dn.extract(_dnf[names.fnv(p.lower())]))
    _DT2='pkd_rvcoondumpster\\denimedgerunner\\textures\\denimedgerunner_'
    DEN={k:_dx2(_DT2+k+'.xbm') for k in ('d01','m01','r01','n01','e01')}
    _pre={'hoodie':'t1','pants':'l1','chain':'i1','jacket':'t2','belt':'i1','kneepads':'i1','elbowpads':'i1','bandolier':'i1','glove':'g1','boots':'s1'}
    for it in OUTFIT:
        if it=='furjacket':      # axellysse fur jacket, black_carbon: same fur cards + cap material as the hat
            _fa2=modres.AR['axellysse_fur_collection']; _ff2={f['hash']:f for f in _fa2.files}
            _jsubs=mesh.decode(_fa2.extract(_ff2[names.fnv('axellysse\\fur_collection\\mesh\\jacket_fur_m_base_body.mesh')]))['subs']
            _cp_=_jsubs[0]['pos']; _cn_=_jsubs[0]['nrm'][:,:3]; _cn_=_cn_/np.linalg.norm(_cn_,axis=1,keepdims=True)
            _cc=_cp_.mean(0); _cn_*=np.sign(((_cp_-_cc)*_cn_).sum(1,keepdims=True)+1e-9)                      # outward
            _jsubs[1]=dict(_jsubs[1],nrm=_cn_[cKDTree(_cp_).query(_jsubs[1]['pos'])[1]])                   # fur cards take the smooth under-layer normal
            for _k,_s in enumerate(_jsubs):
                parts.append(dict(pos=_s['pos'],idx=_s['idx'],uv=_s['uv0'],nrm=_s.get('nrm'),tex=(JACKET_CAP or HAT_CAP) if _k==0 else JACKET_CARDS,alpha=0 if _k==0 else 2,name='jacketcap' if _k==0 else 'jacketfur'))
            # frizz layer: a second, sparser copy of the fur cards lifted 2-4mm and jittered toward the tips (flyaways, broken silhouette)
            _s=_jsubs[1]; _r2=np.random.default_rng(11); _uvv=_s['uv0'][:,1]; _tip=(_uvv-_uvv.min())/max(np.ptp(_uvv),1e-6)
            _jit=_r2.normal(0,1,(len(_s['pos']),3)); _jit=np.asarray(_jit)*(0.0015+0.006*_tip)[:,None]
            _fz=_s['pos']+_s['nrm'][:,:3]*0.003+_jit
            _tri=_s['idx'].reshape(-1,3); _keep=_r2.random(len(_tri))<0.45
            parts.append(dict(pos=_fz.astype(np.float32),idx=_tri[_keep].ravel(),uv=_s['uv0'],nrm=_s['nrm'],tex=JACKET_CARDS,alpha=2,name='jacketfrizz'))
            continue
        if it=='platform':
            _yb=_rd5.Archive('/home/claude/work/new1/src/mods/yusei_short_heeled_boots.archive'); _ybf={f['hash']:f for f in _yb.files}
            _YT='base\\characters\\garment\\player_equipment\\feet\\s1_yusei_short_heeled_boots\\textures\\'
            PLAT={k:xbm.load(_yb.extract(_ybf[names.fnv((_YT+k+'.xbm').lower())])) for k in ('boots_d','boots_n','boots_m','boots_r','metal_d','metal_n','metal_m','metal_r') if names.fnv((_YT+k+'.xbm').lower()) in _ybf}
            print('platform textures',sorted(PLAT))
            for k_,s_ in enumerate(mesh.decode(_yb.extract(_ybf[2721687290290620523]))['subs']):
                parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=PLAT['boots_d' if k_==0 else 'metal_d'].convert('RGBA'),alpha=0,name='plat_'+('boots' if k_==0 else 'metal')))
            continue
        if it=='synthpants':     # tq Synth Pants, default appearance = Black (synth_black_basic.mlsetup over the vanilla Militech l1_078 mask set)
            import ml as _ml,garments as _ga
            _SP=r'base\tq\meshes\synth_pants.mesh'; _MK=r'base\characters\garment\corp_militech\legs\l1_078_pants__militech\textures\ml_l1_078_ma_pants__militech_masksset.mlmask'
            _ml.FALLBACK_MASK=[np.full((8,8),255,np.uint8)]
            SYN=_ml.bake(r'base\tq\textures\pants\synth_black_basic.mlsetup',_MK,2048); SYN['interim']=_ga.segs_of(_MK) is None
            _nm=_ga.segs_of(r'base\characters\garment\corp_militech\legs\l1_078_pants__militech\textures\l1_078_ma_pants__militech_n01.xbm')
            SYN['n01']=xbm.load(_nm) if _nm else None
            _gd=xbm.load(_ga.segs_of(r'base\characters\common\textures\decals\garment_decals_d01.xbm')).convert('RGBA')
            SYN['dec_n']=xbm.load(_ga.segs_of(r'base\characters\common\textures\decals\garment_decals_n01.xbm'))
            _st=np.asarray(_gd).copy(); _st[...,:3]=(22,22,24); SYN['stitch']=Image.fromarray(_st,'RGBA'); SYN['zip']=_gd
            print('synth pants interim(no mask)' if SYN['interim'] else 'synth pants full mask', _ml.MISSING)
            for k_,s_ in enumerate(mesh.decode(_ga.segs_of(_SP))['subs']):
                nm_=['syn_pants','syn_zip','syn_stitch','syn_stitch'][min(k_,3)]
                parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=Image.fromarray((SYN['albedo']*255).astype(np.uint8)).convert('RGBA') if k_==0 else (SYN['zip'] if k_==1 else SYN['stitch']),alpha=0 if k_==0 else 2,name=nm_))
            continue
        if it=='misfits':        # Johnny's tank (t1_090, 'fuk' appearance) with Tank_Misfits.archive's print swapped in
            import ml as _ml2,garments as _ga3,struct as _st,io as _io
            _ml2.FALLBACK_MASK=None
            _SH='base\\characters\\main_npc\\silverhand\\textures\\'
            MIS=_ml2.bake(_SH+'ml_t1_002_ma_tank__silverhand.mlsetup',_SH+'ml_t1_002_ma_tank__silverhand_masksset.mlmask',2048)
            MIS['n01']=xbm.load(_ga3.segs_of(_SH+'t1_002_ma_tank__silverhand_n01.xbm'))
            _ds=_ga3.segs_of('base\\characters\\garment\\player_equipment\\torso\\t1_090_tank__johnny\\textures\\fuk_d01.xbm')
            try:
                _b=_ds[0]; _r=cr2w.parse(_b); _hd=cr2w.chunk(_b,_r,1)[1]['header']; _w=_hd['sizeInfo']['width']; _h=_hd['sizeInfo']['height']; _sz=_hd['mipMapInfo'][0]['placement']['size']
                _raw=_ds[-1][:_sz]; _pf=_st.pack('<II4sIIIII',32,4,b'DX10',0,0,0,0,0)
                _hdr=b'DDS '+_st.pack('<IIIIIII',124,0x1|0x2|0x4|0x1000|0x80000,_h,_w,len(_raw),0,1)+b'\0'*44+_pf+_st.pack('<IIIII',0x1000,0,0,0,0)
                MIS['print']=Image.open(_io.BytesIO(_hdr+_st.pack('<IIIII',xbm.DXGI['BC7'],3,0,1,0)+_raw)); MIS['print'].load(); MIS['print']=MIS['print'].convert('RGBA')
            except Exception as _e: MIS['print']=xbm.load(_ds).convert('RGBA')
            _gd2=xbm.load(_ga3.segs_of('base\\characters\\common\\textures\\decals\\garment_decals_d01.xbm')).convert('RGBA'); _gs=np.asarray(_gd2).copy(); _gs[...,:3]=(18,18,19); MIS['stitch']=Image.fromarray(_gs,'RGBA')
            for k_,s_ in enumerate(mesh.decode(_ga3.segs_of('base\\characters\\garment\\player_equipment\\torso\\t1_090_tank__johnny\\t1_090_pma_tank__johnny.mesh'))['subs']):
                nm_=['mis_tank','mis_print','mis_stitch'][min(k_,2)]
                parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=[Image.fromarray((MIS['albedo']*255).astype(np.uint8)).convert('RGBA'),MIS['print'],MIS['stitch']][min(k_,2)],alpha=0 if k_==0 else 2,name=nm_))
            continue
        if it=='walletchain':    # Edgerunner wallet chain re-finished in polished silver
            q='pkd_rvcoondumpster\\denimedgerunner\\i1_pma_denimedgerunner_chain_base_body.mesh'
            for s_ in mesh.decode(_dn.extract(_dnf[names.fnv(q.lower())]))['subs']:
                parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=DEN['d01'],alpha=0,name='chain_silver'))
            continue
        q='pkd_rvcoondumpster\\denimedgerunner\\%s_pma_denimedgerunner_%s_base_body.mesh'%(_pre[it],it)
        for s_ in mesh.decode(_dn.extract(_dnf[names.fnv(q.lower())]))['subs']:
            parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=DEN['d01'],alpha=0,name='den_'+it))
# ---- ACCESSORIES: ND Barbed (nola_dreamer) - ACC=cross_collar,moon_bracelet_l,...  ACC_COLOR=silver|gold
ACC=[x for x in os.environ.get('ACC','').split(',') if x]; ACC_COLOR=os.environ.get('ACC_COLOR','silver')
if ACC and BODY:
    import garments as _ga2
    _NT='base\\nd_base\\textures\\nd_barbed_accessories_'
    NDT={k:xbm.load(_ga2.segs_of(_NT+k+'.xbm')) for k in ('d_'+ACC_COLOR,'n','r','m')}
    for it in ACC:
        for s_ in mesh.decode(_ga2.segs_of('base\\nd_base\\nd_barbed_%s_m_base_body.mesh'%it))['subs']:
            parts.append(dict(pos=s_['pos'],idx=s_['idx'],uv=s_['uv0'],nrm=s_.get('nrm'),tex=NDT['d_'+ACC_COLOR].convert('RGBA'),alpha=0,name='nd_acc'))
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
