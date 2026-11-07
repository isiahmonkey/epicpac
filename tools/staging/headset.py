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
def parts(warp):
    import garments,xbm
    out=[]; BD=_bake('bd',BD_SETUP); SP=_bake('specs',SP_SETUP)
    n01=xbm.load(garments.segs_of(D+r'citizen_casual\head\h1_033_specs__braindance\textures\h1_033_wa_specs__braindance_n01.xbm'))
    pickle.dump({'hs_bd':_mats(BD,n01),'hs_specs':_mats(SP)},open(H+'headset_mats.pkl','wb'))
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
    return out
