"""Modular Male Headset (black): braindance frame (SLOT1 black) + tactical specs visor (SLOT2 black), rigged to Head.
Geometry comes from the mod archives; colours are baked from the vanilla mlsetups the mod points at."""
import sys,os,pickle,numpy as np
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/pbr']
import rdar,mesh,ml
from PIL import Image
H='/home/claude/work/headset/'
D='base\\characters\\garment\\'
BD_SETUP=(D+r'citizen_casual\head\h1_033_specs__braindance\textures\ml_h1_033_wa_specs__braindance.mlsetup',D+r'citizen_casual\head\h1_033_specs__braindance\textures\ml_h1_033_wa_specs__braindance_masksset.mlmask')
SP_SETUP=(D+r'gang_6thstreet\head\h1_052_specs__tactical\textures\ml_h1_052_ma_specs__tactical.mlsetup',D+r'gang_6thstreet\head\h1_052_specs__tactical\textures\ml_h1_052_ma_specs__tactical_masksset.mlmask')
def _bake(key,setup,R=2048):
    f=H+key+'_bake.pkl'
    ml.MISSING.clear(); B=ml.bake(*setup,R)
    if ml.MISSING: print('headset',key,'missing',sorted(ml.MISSING))
    pickle.dump(B,open(f,'wb')); return B
def _img(B): return Image.fromarray((np.clip(B['albedo'],0,1)*255).astype(np.uint8)).convert('RGBA')
def _mesh(arch):
    A=rdar.Archive(H+arch); f=max(A.files,key=lambda x:len(A.extract(x)[0]) if isinstance(A.extract(x),(list,tuple)) else 0)
    return mesh.decode(A.extract(f))
def _rigid(warp,P):
    """fit ONE similarity transform to the head warp (a per-vertex warp bends hard plastic): keeps the frame crisp"""
    Q=warp(P); mp,mq=P.mean(0),Q.mean(0); A=(P-mp); B=(Q-mq)
    U,S,Vt=np.linalg.svd(A.T@B); d=np.sign(np.linalg.det(U@Vt)); D_=np.diag([1,1,d]); R=(U@D_@Vt).T
    sc=(S*np.diag(D_)).sum()/(A**2).sum(); return lambda X:(sc*(R@(X-mp).T)).T+mq
def _mats(B,n01=None):
    import glb
    nx=B['nxy']; gn=np.zeros_like(nx) if n01 is None else np.asarray(n01.convert('RGB').resize(nx.shape[1::-1],Image.BICUBIC)).astype(np.float32)[...,:2]/127.5-1
    xy=np.clip(gn+nx,-0.95,0.95); ni=Image.fromarray(((np.dstack([xy,np.zeros(xy.shape[:2])])+1)*127.5).clip(0,255).astype(np.uint8))
    return dict(base=None,normal=glb.cp_normal(ni),mr=glb.mr_map(Image.fromarray((B['rough']*255).astype(np.uint8)),Image.fromarray((B['metal']*255).astype(np.uint8))),rough=None,metal=None)
def _clean(B,n01,base,metal,rough,edge=0.10,R=2048):
    """clean black finish: one flat colour + crisp edge highlights from the normal map (CP's low-res wear mask reads as blotches in Gmod)"""
    if n01 is not None:
        g=np.asarray(n01.convert('RGB').resize((R,R),Image.BICUBIC)).astype(np.float32)[...,:2]/127.5-1
        xy=np.clip(g,-0.95,0.95)
    else:
        from scipy.ndimage import gaussian_filter
        xy=np.dstack([gaussian_filter(B['nxy'][...,c],1.2)*0.5 for c in (0,1)])
    tilt=np.clip(np.hypot(xy[...,0],xy[...,1])*2.2,0,1)          # bevels / panel edges
    col=np.ones((R,R,3),np.float32)*np.array(base,np.float32)
    col=col+edge*tilt[...,None]                                   # edges catch light: silhouette of every screw/vent/panel line
    return dict(albedo=np.clip(col,0,1),nxy=xy.astype(np.float32),rough=np.full((R,R),rough,np.float32)-0.2*tilt,metal=np.full((R,R),metal,np.float32))
def clear_brows(out,brows,margin=0.0055,sigma=0.014,iters=4):
    """push the visor (specs frame + lens) forward (+y in CP space) just where eyebrow hair pokes through it; smooth falloff so it bends, not kinks"""
    from scipy.spatial import cKDTree
    vis=[p for p in out if p['name'] in ('hs_specs','hs_glass')]
    B=np.concatenate([np.asarray(b['pos'],np.float64) for b in brows])
    for it in range(iters):
        L=np.concatenate([np.asarray(p['pos'],np.float64) for p in vis]); T=cKDTree(L[:,[0,2]])
        nb=T.query_ball_point(B[:,[0,2]],0.002); front=np.array([L[n,1].max() if n else -9 for n in nb])
        need=np.where(front>-9,B[:,1]+margin-front,0); need=np.clip(need,0,None); k=need>0
        print('   brow clearance pass',it,'poking',int(k.sum()),'max %.1f mm'%(need.max()*1000))
        if not k.any(): break
        Bk=B[k]; nk=need[k]
        for p in vis:
            P=np.asarray(p['pos'],np.float64); d2=((P[:,None,[0,2]]-Bk[None,:,[0,2]])**2).sum(2)
            push=(nk[None,:]*np.exp(-d2/(2*sigma**2))).max(1); P[:,1]+=push; p['pos']=P.astype(np.float32)
    return out
def parts(warp,brows=None):
    import garments,xbm
    out=[]; BD=_bake('bd',BD_SETUP); SP=_bake('specs',SP_SETUP)
    n01=xbm.load(garments.segs_of(D+r'citizen_casual\head\h1_033_specs__braindance\textures\h1_033_wa_specs__braindance_n01.xbm'))
    BD=_clean(BD,n01,(0.045,0.045,0.05),0.85,0.38); SP=_clean(SP,None,(0.035,0.035,0.04),0.0,0.25,edge=0.06)
    pickle.dump({'hs_bd':_mats(BD,None),'hs_specs':_mats(SP)},open(H+'headset_mats.pkl','wb'))
    _all=[]
    glass=Image.new('RGBA',(8,8),(8,8,10,255))
    for arch,names,texs in [('basegame_net_head_male_SLOT1_BDance_black.archive',['hs_bd']*4,[_img(BD)]*4),
                            ('basegame_net_head_male_SLOT2_Specs_black.archive',['hs_specs','hs_glass'],[_img(SP),glass])]:
        g=mesh.decode(rdar.Archive(H+arch).extract(rdar.Archive(H+arch).files[0])) if 'BDance' in arch else _mesh(arch)
        _all.append((arch,names,texs,g))
    PP=np.concatenate([np.asarray(s['pos'],np.float64) for _,_,_,g in _all for s in g['subs'] if len(s['pos'])>=10]); fit=_rigid(warp,PP)
    for arch,names,texs,g in _all:
        for k,s in enumerate(g['subs']):
            if k>=len(names) or len(s['pos'])<10: continue      # skip the empty decal chunks
            out.append(dict(pos=fit(np.asarray(s['pos'],np.float64)).astype(np.float32),idx=np.asarray(s['idx']),uv=np.asarray(s['uv0']),nrm=(lambda P,N:(lambda d:d/np.maximum(np.linalg.norm(d,axis=1,keepdims=True),1e-9))(fit(P+N*0.01)-fit(P)))(np.asarray(s['pos'],np.float64),np.asarray(s['nrm'])[:,:3].astype(np.float64)),
                            tex=texs[k],alpha=0,name=names[k],ji=np.asarray(s['ji']),jw=np.asarray(s['jw']),bones=g['bones'],bonepos=g['bonepos'],chunk=s.get('chunk')))
    return clear_brows(out,brows) if brows else out
