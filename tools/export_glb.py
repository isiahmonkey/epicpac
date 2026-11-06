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
   'brows':G.material('brows',base=bt,normal=glb.cp_normal(BROW_N),nscale=1.5,alpha='BLEND',rough=0.9,double=True,ext={'order':1}),
   'brows_s7':G.material('brows_s7',base=BROW_STRANDS[0.85],alpha='BLEND',rough=0.5,double=True,ext={'order':3,'hair':1}),
   'brows_s14':G.material('brows_s14',base=BROW_STRANDS[0.6],alpha='BLEND',rough=0.5,double=True,ext={'order':4,'hair':1}),
   'earcyber':G.material('earcyber',base=EAR_D,normal=glb.cp_normal(EAR_N),mr=glb.mr_map(EAR_R.resize((1024,1024)),EAR_M.resize((1024,1024))),alpha='MASK',cutoff=0.3),
   'hair':G.material('hair',base=HAIR_CARDS,alpha='MASK',cutoff=0.5,rough=0.55,double=True,ext={'hair':1}),
   'haircap':G.material('haircap',base=HAIR_CAP,alpha='BLEND',rough=0.8,ext={'order':0}),
   'earring':G.material('earring',base=Image.open(S+'ear06_albedo.png').convert('RGB'),mr=glb.mr_map(Image.open(S+'ear06_rough.png').convert('L'),Image.open(S+'ear06_metal.png').convert('L'))),
   'hatfur':G.material('hatfur',base=HAT_CARDS,alpha='MASK',cutoff=0.4,rough=0.6,double=True,ext={'hair':1}),
   'jacketfur':G.material('jacketfur',base=JACKET_CARDS,alpha='MASK',cutoff=0.4,rough=0.9,double=True,ext={'hair':3}),
   'jacketfrizz':G.material('jacketfrizz',base=JACKET_CARDS,alpha='MASK',cutoff=0.5,rough=0.9,double=True,ext={'hair':3}),
   'jacketcap':G.material('jacketcap',base=(JACKET_CAP or HAT_CAP).convert('RGB'),rough=0.95,ext={'nospec':1}),
   'hatcap':G.material('hatcap',base=HAT_CAP.convert('RGB'),rough=0.9),
   'piercing':G.material('piercing',color=(0.012,0.012,0.014,1),rough=0.18,metal=0.0,ext={'clearcoat':0.6}),
   'cyberware':G.material('cyberware',base=cw_base,normal=cw_n,mr=cw_mr)}
if FACE_CW:
    for _k,v in FACECW.items(): M['facecw_'+_k]=G.material('facecw_'+_k,base=v['base'],normal=glb.cp_normal(v['normal']),mr=glb.mr_map(v['rough'],v['metal']),alpha='BLEND',ext={'order':2})
if MAINE: M['maine']=G.material('maine',base=MAINE_D,alpha='BLEND',rough=0.35,metal=0.3,ext={'order':0})
if BODY:
    M['body']=G.material('body',base=BODY_D.convert('RGB'),normal=glb.cp_normal(BODY_N),nscale=0.8,color=(0.85,0.85,0.85,1),rough=0.62,ext={'skin':1.0})
    M['arms']=G.material('arms',base=ARMS_D.convert('RGB'),normal=glb.cp_normal(ARMS_N),nscale=0.8,color=(0.85,0.85,0.85,1),rough=0.62,ext={'skin':1.0})
    if GORILLA:
        import xbm as _x
        def _gm(t,nrm):
            g=lambda k: Image.open(S+'ga_%s_%s_%s.png'%(t,GORILLA,k))
            return G.material('ga_'+t,base=g('a').convert('RGB'),normal=glb.cp_normal(_x.load(cr2w.load_loose('/mnt/user-data/uploads/characters/cyberware/player/a0_005__strongarms/entities/meshes/textures/'+nrm))) if nrm else None,mr=glb.mr_map(g('r').convert('L'),g('m').convert('L')))
        M['ga_fingers']=_gm('fingers','a0_005_ma__strongarms_smooth_n01.xbm'); M['ga_end']=_gm('end','a0_005_ma__strongarms_end_n01.xbm'); M['ga_cyber']=_gm('cyber','a0_005_wa__strongarms_cyberware_n01.xbm')
        for _k,_v in GA_DEC.items(): M['ga_dec_'+_k]=G.material('ga_dec_'+_k,base=_v,alpha='BLEND',rough=0.5,ext={'order':1})
        M['ga_glass']=G.material('ga_glass',color=(0.02,0.02,0.025,1),rough=0.05,ext={'clearcoat':1.0})
    M['nails']=G.material('nails',color=(0.07,0.045,0.035,1),rough=0.3)
if 'OUTFIT' in globals() and OUTFIT:
    _dmr=glb.mr_map(DEN['r01'].convert('L').resize((2048,2048)),DEN['m01'].convert('L').resize((2048,2048)))
    _dbase=DEN['d01'].convert('RGB').resize((2048,2048)); _dn_=glb.cp_normal(DEN['n01'].resize((2048,2048)))
    _de=DEN['e01'].convert('RGB')
    for it in OUTFIT:
        if it=='platform':
            for t in ('boots','metal'):
                _r=PLAT.get(t+'_r'); _m=PLAT.get(t+'_m'); _sz=(_r or _m or PLAT[t+'_d']).size
                M['plat_'+t]=G.material('plat_'+t,base=PLAT[t+'_d'].convert('RGB'),normal=glb.cp_normal(PLAT[t+'_n']) if t+'_n' in PLAT else None,mr=glb.mr_map((_r.convert('L') if _r else Image.new('L',_sz,140)),(_m.convert('L').resize(_sz) if _m else Image.new('L',_sz,255 if t=='metal' else 0))))
        elif it=='synthpants':
            _nx=SYN['nxy']; _gn=np.zeros_like(_nx) if SYN['n01'] is None else np.asarray(SYN['n01'].convert('RGB').resize(_nx.shape[1::-1],Image.BICUBIC)).astype(np.float32)[...,:2]/127.5-1
            _xy=np.clip(_gn+_nx,-0.95,0.95)       # CP multilayered: garment normal (panels/seams) + per-layer detail normal (cotton weave) blended
            _nimg=Image.fromarray(((np.dstack([_xy,np.zeros(_xy.shape[:2])])+1)*127.5).clip(0,255).astype(np.uint8))
            M['syn_pants']=G.material('syn_pants',base=Image.fromarray((SYN['albedo']*255).astype(np.uint8)),normal=glb.cp_normal(_nimg),mr=glb.mr_map(Image.fromarray((SYN['rough']*255).astype(np.uint8)),Image.fromarray((SYN['metal']*255).astype(np.uint8))),ext={'cull':1})
            M['syn_zip']=G.material('syn_zip',base=SYN['zip'],normal=glb.cp_normal(SYN['dec_n']),alpha='BLEND',rough=0.35,metal=0.9,ext={'order':1})
            M['syn_stitch']=G.material('syn_stitch',base=SYN['stitch'],alpha='BLEND',rough=0.8,ext={'order':1})
        elif it=='walletchain':
            _cl=np.asarray(DEN['d01'].convert('L').resize((2048,2048))).astype(np.float32); _cl=np.clip(150+(_cl-_cl.mean())*0.5,90,215).astype(np.uint8)
            M['chain_silver']=G.material('chain_silver',base=Image.fromarray(np.dstack([_cl,_cl,(_cl*1.02).clip(0,255).astype(np.uint8)])),normal=_dn_,rough=0.22,metal=1.0)
        else: M['den_'+it]=G.material('den_'+it,base=_dbase,normal=_dn_,mr=_dmr,emis=_de,emis_f=(1,1,1),ext={'cull':1})   # cloth has an inner shell: cull back faces
if 'ACC' in globals() and ACC:
    _sz=NDT['d_'+ACC_COLOR].size
    M['nd_acc']=G.material('nd_acc',base=NDT['d_'+ACC_COLOR].convert('RGB'),normal=glb.cp_normal(NDT['n']),mr=glb.mr_map(NDT['r'].convert('L').resize(_sz),NDT['m'].convert('L').resize(_sz)))
for p in parts:
    if p['name'] not in M: continue
    _n=p.get('nrm'); _n=None if _n is None else _n[:,:3]/np.maximum(np.linalg.norm(_n[:,:3],axis=1,keepdims=True),1e-9)
    G.mesh(p['name'],p['pos'],p['idx'],p['uv'],M[p['name']],normals=_n)   # authored normals where the source has them
print('glb bytes',G.save(sys.argv[1] if len(sys.argv)>1 else S+'stage_head.glb'))
