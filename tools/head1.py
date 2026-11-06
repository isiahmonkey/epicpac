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
for _s,_nm in HSUBS:
    q=warp_from_vanilla(_s['pos'],k=6)
    if _nm=='haircap': q,_l=float_on(q,hp[0],HM['geo']['subs'][0]['idx'],gap=0.0005)
    parts.append(dict(pos=q,idx=_s['idx'],uv=_s['uv0'],tex=HAIR_CARDS if _nm=='hair' else HAIR_CAP,alpha=2,name=_nm))
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
