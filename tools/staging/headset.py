"""Modular Male Headset (black): braindance frame (SLOT1 black) + tactical specs visor (SLOT2 black), rigged to Head.
Geometry comes from the mod archives; colours are baked from the vanilla mlsetups the mod points at."""
import sys,os,pickle,numpy as np
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build']
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
def parts(warp):
    out=[]; BD=_bake('bd',BD_SETUP); SP=_bake('specs',SP_SETUP)
    glass=Image.new('RGBA',(8,8),(8,8,10,255))
    for arch,names,texs in [('basegame_net_head_male_SLOT1_BDance_black.archive',['hs_bd']*4,[_img(BD)]*4),
                            ('basegame_net_head_male_SLOT2_Specs_black.archive',['hs_specs','hs_glass'],[_img(SP),glass])]:
        g=mesh.decode(rdar.Archive(H+arch).extract(rdar.Archive(H+arch).files[0])) if 'BDance' in arch else _mesh(arch)
        for k,s in enumerate(g['subs']):
            if k>=len(names) or len(s['pos'])<10: continue      # skip the empty decal chunks
            out.append(dict(pos=warp(np.asarray(s['pos'],np.float64)).astype(np.float32),idx=np.asarray(s['idx']),uv=np.asarray(s['uv0']),nrm=s.get('nrm'),
                            tex=texs[k],alpha=0,name=names[k],ji=np.asarray(s['ji']),jw=np.asarray(s['jw']),bones=g['bones'],bonepos=g['bonepos'],chunk=s.get('chunk')))
    return out
