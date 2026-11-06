import sys,os,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/pbr')
os.environ.setdefault('MORPH','2'); os.environ.setdefault('TONE','deep')
exec(open('/home/claude/work/staging/head1.py').read().split('parts.sort(')[0].replace('print(','(lambda *a,**k:None)('))
import glb,cr2w,xbm
from PIL import Image
G=glb.GLB()
U2='/mnt/user-data/uploads/characters/'
skin_n=glb.cp_normal(xbm.load(cr2w.load_loose(U2+'head/player_base_heads/player_man_average/h0_000_pma_c__basehead/textures/h0_000_pma_c__basehead_n01.xbm')))
cw_n=glb.cp_normal(Image.open('/home/claude/work/staging/cw_n01.png'))
S='/home/claude/work/staging/'
cw_mr=glb.mr_map(Image.open(S+'cw_rough.png').convert('L').resize((1024,1024)),Image.open(S+'cw_metal.png').convert('L').resize((1024,1024)))
cw_base=Image.open(S+'cw_albedo.png').convert('RGB').resize((2048,2048))
_e=np.asarray(EYE.convert('RGB')).astype(np.float32); _x=np.asarray(EYE_EMIT.convert('RGB')).astype(np.float32)
EYE_E2=Image.fromarray(np.clip(_e*0.30+_x,0,255).astype(np.uint8))   # eyes catch light from everywhere in CP (Blick cubemap): small self-lit floor
M={'skin':G.material('skin',base=skin.convert('RGB'),color=(0.85,0.85,0.85,1),normal=skin_n,nscale=0.8,rough=0.62,ext={'skin':1.0}),
   'eyes':G.material('eyes',base=EYE.convert('RGB'),color=(1.0,1.0,1.0,1),emis=EYE_EMIT.convert('RGB'),emis_f=(1.4,1.4,1.4),rough=0.45,ext={'clearcoat':0.3,'shmin':0.8,'selflit':0.05}),
   'eyeshadow':G.material('eyeshadow',base=SHADOW,alpha='BLEND',rough=1.0,ext={'order':0}),
   'lashes':G.material('lashes',base=LASH,alpha='MASK',cutoff=0.25,rough=1.0,double=True,ext={'nospec':1}),
   'brows':G.material('brows',base=bt,alpha='BLEND',rough=1.0,double=True,ext={'order':1}),
   'earcyber':G.material('earcyber',base=EAR_D,normal=glb.cp_normal(EAR_N),mr=glb.mr_map(EAR_R.resize((1024,1024)),EAR_M.resize((1024,1024))),alpha='MASK',cutoff=0.3),
   'hair':G.material('hair',base=HAIR_CARDS,alpha='MASK',cutoff=0.5,rough=0.55,double=True,ext={'hair':1}),
   'haircap':G.material('haircap',base=HAIR_CAP,alpha='BLEND',rough=0.8,ext={'order':0}),
   'earring':G.material('earring',base=Image.open(S+'ear06_albedo.png').convert('RGB'),mr=glb.mr_map(Image.open(S+'ear06_rough.png').convert('L'),Image.open(S+'ear06_metal.png').convert('L'))),
   'hatfur':G.material('hatfur',base=HAT_CARDS,alpha='MASK',cutoff=0.4,rough=0.6,double=True,ext={'hair':1}),
   'hatcap':G.material('hatcap',base=HAT_CAP.convert('RGB'),rough=0.9),
   'cyberware':G.material('cyberware',base=cw_base,normal=cw_n,mr=cw_mr)}
for p in parts:
    if p['name'] not in M: continue
    G.mesh(p['name'],p['pos'],p['idx'],p['uv'],M[p['name']])
print('glb bytes',G.save(sys.argv[1] if len(sys.argv)>1 else S+'stage_head.glb'))
