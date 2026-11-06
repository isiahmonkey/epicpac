"""Token -> Garry's Mod / PAC3 kit.
Every clothing / accessory piece is a BODYGROUP option. Pieces are split over a few .mdl files
(each kept under Source's per-model limits) that all bone-merge onto the ValveBiped:
  token_body     : head, skin regions, arms (Gorilla), hair, hat, face + neck cyberware, ears, face decals
  token_tops     : torso_inner / torso_outer
  token_bottoms  : legs / legs_acc / feet
  token_jewelry  : neck_jewelry / wrist_left
Output: /mnt/user-data/outputs/token_kit/  (modelsrc/*.smd *.qc, materialsrc/*.tga, materials/*.vmt, compile_token.bat)"""
import sys,os,json,pickle,shutil,numpy as np
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build','/home/claude/tools/decimate']
from PIL import Image
import retarget as RT, smd, qem, xbm, garments
from kit import nrm_rgb, phys_tris
NAME='token'; MATDIR='models/player/'+NAME
KIT='/mnt/user-data/outputs/token_kit/'
P=pickle.load(open(os.environ.get('STAGED','/home/claude/work/token/staged_parts.pkl'),'rb'))

# ---------------- what goes where ----------------
BODY_REGIONS={'torso':[0,2],'collar':[1],'pelvis':[3],'thighs':[4],'calves':[5,6],'feet':[7]}
# model -> bodygroup -> option -> [part names]
LAYOUT={
 'token_body':{
   'head':{'head':['skin','lashes','eyeshadow','eyes','brows','brows_s7','brows_s14']},
   'arms':{'gorilla_black':['arms','ga_fingers','ga_glass','ga_end','ga_cyber','ga_dec_decal_holstered_forearm_01','ga_dec_decal_tapes2','ga_dec_decal_hand_top','ga_dec_decal_cyberware_text','ga_dec_decal_under_cyberware','ga_dec_decal_holes','ga_dec_decal_betewwn_fingers']},
   'neck_cyberware':{'takemura_black_red':['cyberware']},
   'head_hair':{'keelan_locs':['hair','haircap']},
   'hat':{'fur_hat':['hatcap','hatfur']},
   'face_cyberware':{'emmerich_black':['facecw_face','facecw_nose']},
   'face_piercings':{'emmerich':['piercing']},
   'face_decal':{'maine_black_red':['maine']},
   'ear_left':{'cross_earring':['earring']},
   'ear_right':{'anrui_black':['earcyber']},
 },
 'token_tops':{
   'torso_inner':{'misfits_tank':['mis_tank','mis_print','mis_stitch'],'denim_hoodie':['den_hoodie']},
   'torso_outer':{'long_fur_coat':['coatcap','coatfur','coatfrizz'],'fur_jacket':['jacketcap','jacketfur','jacketfrizz'],'bolero_black':['bolero_ml','bolero_dec','bolerocuff_ml']},
 },
 'token_bottoms':{
   'legs':{'baggy_jeans_black':['jeans'],'synth_pants_black':['syn_pants','syn_zip','syn_stitch'],'denim_pants':['den_pants']},
   'legs_acc':{'wallet_chain_silver':['chain_silver']},
   'feet':{'vinyl_platform_black':['vinyl'],'tron_red':['tron_ml','tron_dec','tron_glow'],'edgerunner_boots':['den_boots']},
 },
 'token_jewelry':{
   'neck_jewelry':{'valentino_cross_silver':['vchain','vcross']},
   'wrist_left':{'nd_cross_bracelet':['nd_acc']},
 },
}
FLATTEN={'bolero_ml':0.15,'bolerocuff_ml':0.15}
LEATHER=' "$halflambert" "1"\n "$phong" "1"\n "$phongexponent" "28"\n "$phongboost" "1.6"\n "$phongfresnelranges" "[0.3 0.6 1]"\n{A}'
SILVER=' "$envmap" "env_cubemap"\n "$envmaptint" "[.85 .85 .88]"\n "$envmapcontrast" "1"\n "$phong" "1"\n "$phongexponent" "70"\n "$phongboost" "6"\n "$phongalbedotint" "1"\n "$phongfresnelranges" "[1 1 1]"\n "$halflambert" "1"\n{A}'
BLACKMETAL=' "$envmap" "env_cubemap"\n "$envmaptint" "[.07 .07 .075]"\n "$phong" "1"\n "$phongexponent" "35"\n "$phongboost" "2.5"\n "$phongfresnelranges" "[0.4 0.8 1]"\n "$halflambert" "1"\n{A}'
BLACKMETAL_N=' "$bumpmap" "{D}/{M}_n"\n'+BLACKMETAL
CARDS_DARK=' "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "10"\n "$phongboost" "0.12"\n'
EYES=' "$selfillum" "1"\n "$selfillumtint" "[2.2 2.2 2.2]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "1"\n'
HAIR=' "$bumpmap" "{D}/{M}_n"\n "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n'
VMT_OVERRIDE={'cyberware':BLACKMETAL,'ga_cyber':BLACKMETAL,'ga_fingers':BLACKMETAL,'ga_end':BLACKMETAL,'earcyber':BLACKMETAL,'piercing':BLACKMETAL,
 'facecw_face':BLACKMETAL_N,'facecw_nose':BLACKMETAL_N,'eyes':EYES,
 'hair':HAIR,'hatfur':HAIR,'brows':CARDS_DARK,'brows_s7':CARDS_DARK,'brows_s14':CARDS_DARK,'lashes':CARDS_DARK,
 'haircap':CARDS_DARK.replace('"0.4"','"0.12"'),'bolero_ml':LEATHER,'bolerocuff_ml':LEATHER,'chain_silver':SILVER,'earring':SILVER,'nd_acc':SILVER,'vchain':SILVER,'vcross':SILVER}
DARKEN={'hair':0.55,'hatfur':0.5,'haircap':0.6,'brows':0.6,'brows_s7':0.6,'brows_s14':0.6,'chain_silver':0.38,'earring':0.38,'nd_acc':0.38,'vchain':0.38,'vcross':0.38}   # polished metal: dark diffuse, the shine comes from the cubemap
BODY_MODEL='token_body'; KEEP=False; KITZIP='token_kit.zip'; PACZIP='token_pac3.zip'; BATNAME='compile_token.bat'
DEFAULT_ON={'head','arms','neck_cyberware','head_hair','face_cyberware','face_piercings','face_decal','ear_left','ear_right'}   # groups without a 'blank' at index 0

# ---------------- budget: Gmod-friendly triangle counts ----------------
DECIMATE={'ga_cyber':0.24,'jeans':0.28,'cyberware':0.40,'jacketcap':0.35,'coatcap':0.35,'bolero_ml':0.6,'den_boots':0.45,'syn_pants':0.7,'den_hoodie':0.8,'den_pants':0.8,'mis_tank':0.8,'maine':0.35,'earcyber':0.7,'ga_fingers':0.6}
CARDS={'hatfur':1.0,'jacketfur':0.45,'coatfur':0.38,'jacketfrizz':0.3,'coatfrizz':0.3,'hair':1.0}
NOLOCK={'cyberware','maine','ga_cyber'}   # hard-surface / decal: open edges are panel borders, not UV seams that matter   # keep this fraction of whole hair/fur cards
def boundary_lock(F,n):
    from collections import Counter
    E=Counter();
    for a,b in ((0,1),(1,2),(2,0)):
        for e in map(tuple,np.sort(F[:,[a,b]],1)): E[e]+=1
    lock=np.zeros(n,np.uint8)
    for (a,b),c in E.items():
        if c==1: lock[a]=lock[b]=1
    return lock
def reduce(p):
    F=p['idx'].reshape(-1,3).astype(np.int64); nm=p['name']
    if nm in CARDS and CARDS[nm]<1:
        from scipy.sparse import coo_matrix; from scipy.sparse.csgraph import connected_components
        n=len(p['pos']); g=coo_matrix((np.ones(len(F)*2),(np.r_[F[:,0],F[:,1]],np.r_[F[:,1],F[:,2]])),shape=(n,n))
        _,lab=connected_components(g,directed=False); rng=np.random.default_rng(5); keep=rng.random(lab.max()+1)<CARDS[nm]
        F=F[keep[lab[F[:,0]]]]
    elif nm in DECIMATE and len(F)>3000:
        F=qem.decimate(p['pos'],F,int(len(F)*DECIMATE[nm]),lock=None if nm in NOLOCK else boundary_lock(F,len(p['pos'])))
    return F
RIGID={'vchain':'ValveBiped.Bip01_Spine4','vcross':'ValveBiped.Bip01_Spine4','earring':'ValveBiped.Bip01_Head1','chain_silver':'ValveBiped.Bip01_Pelvis','nd_acc':'ValveBiped.Bip01_L_Forearm'}
HEADLIKE={'skin','lashes','eyeshadow','eyes','brows','brows_s7','brows_s14','hair','haircap','hatcap','hatfur','facecw_face','facecw_nose','piercing','maine','earcyber'}
def head_skin(pos,nrm):
    """head/face/hair: one rigid move (the torso/head translation the retarget uses), weights by height:
    chest -> neck -> head with smooth blends (no per-face-bone noise; Gmod has no face bones)"""
    T=RT.D['Head']; P=(RT.C@pos.T).T*RT.S; P=(T[:3,:3]@P.T).T+T[:3,3]; N=(RT.C@nrm.T).T
    z=P[:,2]; zh=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][2,3]; zn=RT.NW[RT.vn.index('ValveBiped.Bip01_Neck1')][2,3]
    iH=RT.vn.index('ValveBiped.Bip01_Head1'); iN=RT.vn.index('ValveBiped.Bip01_Neck1'); iS=RT.vn.index('ValveBiped.Bip01_Spine4')
    sm=lambda x: x*x*(3-2*x)
    wh=sm(np.clip((z-(zh-1.5))/3.0,0,1)); wn_=sm(np.clip((z-(zn-2.5))/3.0,0,1))
    lk=[]
    for a,b in zip(wh,wn_):
        h=a; n=(1-a)*b; c=(1-a)*(1-b); L=[(i,w) for i,w in ((iH,h),(iN,n),(iS,c)) if w>0.01]; t=sum(w for _,w in L); lk.append([(i,w/t) for i,w in L])
    return P,N,lk
# ---------------- materials ----------------
def cls(nm):
    if nm in ('skin',): return 'skin_head'
    if nm=='body': return 'skin_body'
    if nm=='arms': return 'skin_arms'
    if nm in ('lashes','brows','brows_s7','brows_s14','eyeshadow','hair','haircap','hatfur','jacketfur','coatfur','jacketfrizz','coatfrizz'): return 'cards'
    if nm=='eyes': return 'eyes'
    if nm=='ga_glass': return 'glass'
    if nm=='tron_glow': return 'glow'
    if nm in ('cyberware','ga_cyber','ga_fingers','ga_end','chain_silver','vchain','vcross','nd_acc','earring','earcyber','piercing','facecw_face','facecw_nose'): return 'metal'
    if nm.startswith('ga_dec') or nm.endswith(('_dec','_stitch','_print','_zip')) or nm=='maine': return 'decal'
    return 'cloth'
VMTX={
 'skin_head':' "$bumpmap" "{D}/{M}_n"\n "$phong" "1"\n "$phongexponent" "14"\n "$phongboost" "0.9"\n "$phongfresnelranges" "[0.12 0.55 1.0]"\n "$rimlight" "1"\n "$rimlightexponent" "4"\n "$rimlightboost" "0.25"\n "$halflambert" "1"\n',
 'skin_body':' "$bumpmap" "{D}/{M}_n"\n "$phong" "1"\n "$phongexponent" "14"\n "$phongboost" "0.5"\n "$phongfresnelranges" "[0.2 0.6 1.2]"\n "$halflambert" "1"\n',
 'skin_arms':' "$bumpmap" "{D}/{M}_n"\n "$phong" "1"\n "$phongexponent" "14"\n "$phongboost" "0.5"\n "$phongfresnelranges" "[0.2 0.6 1.2]"\n "$halflambert" "1"\n',
 'cards':' "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n "$halflambert" "1"\n "$phong" "1"\n "$phongexponent" "8"\n "$phongboost" "0.4"\n "$phongfresnelranges" "[0.3 0.6 1]"\n',
 'eyes':' "$selfillum" "1"\n "$selfillumtint" "[1.6 1.6 1.6]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "3"\n',
 'glass':' "$translucent" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.5 .5 .52]"\n "$phong" "1"\n "$phongexponent" "80"\n "$phongboost" "6"\n',
 'glow':' "$selfillum" "1"\n "$selfillumtint" "[4 .2 .15]"\n',
 'metal':' "$envmap" "env_cubemap"\n "$envmaptint" "[.35 .35 .37]"\n "$envmapsaturation" "0.4"\n "$phong" "1"\n "$phongexponent" "40"\n "$phongboost" "3"\n "$phongfresnelranges" "[0.6 0.85 1]"\n "$halflambert" "1"\n{A}',
 'decal':' "$alphatest" "1"\n "$alphatestreference" "0.45"\n "$allowalphatocoverage" "1"\n "$halflambert" "1"\n',
 'cloth':' "$halflambert" "1"\n "$phong" "1"\n "$phongexponent" "6"\n "$phongboost" "0.25"\n "$phongfresnelranges" "[0.4 0.7 1]"\n{A}',
}
TEXCAP={'bolero_ml':2048,'bolerocuff_ml':2048,'den_pants':2048,'vinyl':2048,'den_hoodie':2048,'syn_pants':2048,'skin':2048,'jeans':2048,'mis_tank':2048,'body':2048,'arms':2048,'hair':1024,'coatfur':1024,'jacketfur':1024,'cyberware':2048,'ga_cyber':2048}
def to_tga(im,nm):
    cap=TEXCAP.get(nm,1024); w,h=im.size; s=min(1.0,cap/max(w,h))
    if s<1: im=im.resize((max(4,int(w*s)),max(4,int(h*s))),Image.LANCZOS)
    return im
NORMALS={  # extra normal maps where they carry the look
 'skin':'/home/claude/work/build/../tex/base/h0_000_pma_c__basehead_n01.png',
 'body':'/home/claude/work/tex/base/t0_000_ma__c_base_n03_censored.png',
 'arms':'/home/claude/work/tex/base/a0_000_ma_base__hq_nd01.png',
 'facecw_face':'/home/claude/work/tex/base/hx_cyberware_13_m02.png','facecw_nose':'/home/claude/work/tex/base/hx_cyberware_13_d02.png'}
CAP=None
DERIVED_NORMAL={'hair':6.0,'hatfur':4.0}
# name -> [(offset mm, alphatest ref or None = same material)]
SHELLS={'facecw_face':[(0.4*k,None) for k in range(1,7)],'facecw_nose':[(0.4*k,None) for k in range(1,7)],
        'brows':[(0.3,0.36),(0.6,0.44),(0.9,0.52),(1.2,0.6),(1.5,0.68)]}
def tuck_under_cap(vp,inset=0.2):
    """neck cyberware pieces that rise onto the back of the skull: pull them just under the hair cap so the locs lie over them"""
    from scipy.spatial import cKDTree
    hc=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([0.0,0,2.5])
    cd=CAP-hc; cr=np.linalg.norm(cd,axis=1); cu=cd/cr[:,None]; tree=cKDTree(cu)
    d=vp-hc; r=np.linalg.norm(d,axis=1); u=d/np.maximum(r,1e-6)[:,None]
    dist,j=tree.query(u); inside=dist<0.06; lim=cr[j]-inset; m=inside&(r>lim)
    out=vp.copy(); out[m]=hc+u[m]*lim[m][:,None]; print('   cyberware verts tucked under hair cap:',int(m.sum())); return out
def main():
    if os.path.exists(KIT) and not KEEP: shutil.rmtree(KIT)
    for d in ('modelsrc','materialsrc','materials'): os.makedirs(KIT+d,exist_ok=True)
    byname={}
    for p in P: byname.setdefault(p['name'],[]).append(p)
    texdone=set(); report={}; plan={}
    global CAP
    if 'haircap' in byname:
        CAP=np.concatenate([head_skin(p['pos'].astype(np.float64),np.tile([0,0,1.0],(len(p['pos']),1)))[0] for p in byname['haircap']])
    NL=RT.NL
    def emit_mat(nm,p):
        if nm in texdone: return
        texdone.add(nm); c=cls(nm); tex=p.get('tex')
        im=tex if tex is not None else Image.new('RGBA',(8,8),(128,128,128,255))
        im=to_tga(im.convert('RGBA'),nm)
        _p2=lambda v:1<<max(2,round(np.log2(v)))
        if im.size!=(_p2(im.size[0]),_p2(im.size[1])): im=im.resize((_p2(im.size[0]),_p2(im.size[1])),Image.LANCZOS)
        if nm in FLATTEN:    # baked wear/scuff layers read as grey paint in Gmod's albedo-only shading: pull them back toward the base colour
            a=np.asarray(im).astype(np.float32); base=np.median(a[...,:3].reshape(-1,3),0)
            a[...,:3]=base+(a[...,:3]-base)*FLATTEN[nm]; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8),im.mode)
        if nm in DARKEN:
            a=np.asarray(im).astype(np.float32); a[...,:3]*=DARKEN[nm]; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8),im.mode)
        if nm=='eyes':
            a=np.asarray(im.convert('RGBA')).astype(np.float32); H,W=a.shape[:2]; yy,xx=np.mgrid[0:H,0:W]
            r=np.hypot(xx/W-0.5,yy/H-0.46); rgb=a[...,:3]; sat=(rgb.max(2)-rgb.min(2))/np.maximum(rgb.max(2),1); lum=rgb.mean(2)/255
            m=((r<0.205)*np.clip((lum-0.35)*2.5,0,1)+(r<0.32)*(r>0.205)*(sat>0.45)*(lum>0.35)*0.8)
            a[...,3]=np.clip(m,0,1)*255; im=Image.fromarray(a.astype(np.uint8),'RGBA')
            im.save(KIT+'materialsrc/%s_%s.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s.txt'%(NAME,nm),'w').write('nocompress 0\n')
            open(KIT+'materials/%s_%s.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,EYES)); return
        has_a=np.asarray(im)[...,3].min()<250
        if c not in ('cards','decal','glass') and not has_a: im=im.convert('RGB')
        im.save(KIT+'materialsrc/%s_%s.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s.txt'%(NAME,nm),'w').write('nocompress 0\n')
        A=''
        if nm in DERIVED_NORMAL:   # strand-level relief from the albedo itself (breaks the smooth 'plastic' look of hair geometry)
            g=np.asarray(im.convert('L').resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255*DERIVED_NORMAL[nm]
            gx=np.roll(g,-1,1)-np.roll(g,1,1); gy=np.roll(g,-1,0)-np.roll(g,1,0); n=np.dstack([-gx,-gy,np.ones_like(g)]); n/=np.linalg.norm(n,axis=2,keepdims=True)
            Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n')
        elif nm in NORMALS and os.path.exists(NORMALS[nm]):
            nrm_rgb(NORMALS[nm],size=(1024,1024)).save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n')
        elif c in ('skin_head','skin_body','skin_arms'): c='cloth'
        if c in ('metal','cloth') and has_a: A=' "$alphatest" "1"\n "$alphatestreference" "0.45"\n'
        body=VMT_OVERRIDE.get(nm,VMTX[c]).replace('{A}',A).replace('{D}',MATDIR).replace('{M}','%s_%s'%(NAME,nm))
        open(KIT+'materials/%s_%s.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,body))
    def tris_of(names,chunks=None):
        T=[]
        for nm in names:
            for p in byname.get(nm,[]):
                if chunks is not None and p.get('chunk') not in chunks: continue
                F=reduce(p); report[nm]=report.get(nm,0)+len(F)
                pos=p['pos'].astype(np.float64); nrm=p.get('nrm'); nrm=p.get('src_nrm') if nrm is None else nrm
                if nrm is None:
                    nrm=np.zeros_like(pos); fn=np.cross(pos[F[:,1]]-pos[F[:,0]],pos[F[:,2]]-pos[F[:,0]])
                    for k in range(3): np.add.at(nrm,F[:,k],fn)
                nrm=np.asarray(nrm)[:,:3].astype(np.float64); nrm/=np.maximum(np.linalg.norm(nrm,axis=1,keepdims=True),1e-9)
                used=np.unique(F); remap=-np.ones(len(pos),int); remap[used]=np.arange(len(used))
                if nm in HEADLIKE: vp,vn_,lk=head_skin(pos[used],nrm[used])
                else: vp,vn_,lk=RT.retarget(pos[used],nrm[used],np.asarray(p['ji'])[used],np.asarray(p['jw'])[used],p['bones'],p['bonepos'])
                if nm in RIGID: lk=[[(RT.vn.index(RIGID[nm]),1.0)]]*len(vp)      # jewelry moves as one piece
                if nm in HEADLIKE and cls(nm)!='cards':   # some CP head-family meshes carry inward normals: make them face out of the skull
                    hc=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([1.5,0,3.5])
                    if ((vp-hc)*vn_).sum(1).mean()<0: vn_=-vn_
                if nm=='cyberware' and CAP is not None: vp=tuck_under_cap(vp)
                Fi=remap[F].copy(); a,b,c=vp[Fi[:,0]],vp[Fi[:,1]],vp[Fi[:,2]]
                bad=(np.cross(b-a,c-a)*vn_[Fi].sum(1)).sum(1)<0; Fi[bad]=Fi[bad][:,[0,2,1]]; flip=False   # each triangle faces the way its normals point (Source culls back faces)
                emit_mat(nm,p)
                T+=smd.part_tris(vp,vn_,p['uv'][used],Fi.ravel(),lk,'%s_%s'%(NAME,nm),flip=flip)
                if nm in SHELLS:   # stacked offset shells: real thickness for flat plates / brow hair (fur-shell technique)
                    hc=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([1.5,0,3.5])
                    up=vp-hc; up/=np.linalg.norm(up,axis=1,keepdims=True)
                    for k,(off_mm,ref) in enumerate(SHELLS[nm]):
                        mat='%s_%s'%(NAME,nm) if ref is None else '%s_%s_L%d'%(NAME,nm,k)
                        if ref is not None and mat not in texdone:
                            texdone.add(mat)
                            open(KIT+'materials/%s.vmt'%mat,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,VMT_OVERRIDE[nm].replace('"0.4"','"%.2f"'%ref)))
                        T+=smd.part_tris(vp+up*off_mm/25.4,vn_,p['uv'][used],Fi.ravel(),lk,mat,flip=flip)
        return T
    for model,groups in LAYOUT.items():
        qc=['$modelname "player/%s/%s.mdl"'%(NAME,model),'$cdmaterials "%s/"'%MATDIR,'$surfaceprop "flesh"','$model "%s_bind" "%s_bind.smd"'%(model,model)]
        allt=[]; mats=set(); groupsout={}
        smd.write(KIT+'modelsrc/%s_bind.smd'%model,RT.vn,RT.vp,NL,[])
        if model==BODY_MODEL:   # body skin regions: each its own toggle (hide skin under clothes)
            for r,ch in BODY_REGIONS.items():
                T=tris_of(['body'],chunks=ch); fn='%s_skin_%s.smd'%(model,r); smd.write(KIT+'modelsrc/'+fn,RT.vn,RT.vp,NL,T); allt+=T; mats.update(m for m,_ in T)
                qc.append('$bodygroup "skin_%s"\n{\n studio "%s"\n blank\n}'%(r,fn)); groupsout['skin_'+r]=['on','off']
        for g,opts in groups.items():
            lines=[]; names=[]
            if g not in DEFAULT_ON: lines.append(' blank'); names.append('none')
            for o,parts in opts.items():
                T=tris_of(parts); allt+=T
                fn='%s_%s_%s.smd'%(model,g,o); smd.write(KIT+'modelsrc/'+fn,RT.vn,RT.vp,NL,T)
                lines.append(' studio "%s"'%fn); names.append(o)
                for m,_ in T: mats.add(m)
            if g in DEFAULT_ON: lines.append(' blank'); names.append('none')
            qc.append('$bodygroup "%s"\n{\n%s\n}'%(g,'\n'.join(lines))); groupsout[g]=names
        if model==BODY_MODEL:
            smd.write(KIT+'modelsrc/%s_phys.smd'%model,RT.vn,RT.vp,NL,phys_tris([t for t in allt if t[0].endswith(('_body','_skin','_arms'))]))
        qc.append('$sequence "idle" "%s_bind.smd" fps 1'%model)
        open(KIT+'modelsrc/%s.qc'%model,'w',newline='\r\n').write('\n'.join(qc)+'\n')
        plan[model]=dict(bodygroups=groupsout,materials=sorted(mats),tris=len(allt))
        print(model,'tris',len(allt),'materials',len(mats))
    if BATNAME:
        json.dump(dict(plan=plan,tris_per_piece=report),open(KIT+'token_plan.json','w'),indent=1)
        open(KIT+BATNAME,'w',newline='\r\n').write(bat(plan))
    return plan
def bat(plan):
    s=(r'''@echo off
setlocal
rem ==== Token -> GMod one-click compile (bodygroup models for PAC3) ====
set GMOD=C:\Program Files (x86)\Steam\steamapps\common\GarrysMod
set KIT=%~dp0
set GAME=%GMOD%\garrysmod
set MD=%GAME%\materials\models\player\token
set MO=%GAME%\models\player\token
if exist "%KIT%token_kit.zip" (
 echo [0/4] Unpacking kit...
 powershell -NoProfile -Command "Expand-Archive -Force -LiteralPath '%KIT%token_kit.zip' -DestinationPath '%KIT%.'"
 del "%KIT%token_kit.zip"
)
echo [1/4] Converting textures with vtex...
if not exist "%GAME%\materialsrc\models\player\token" mkdir "%GAME%\materialsrc\models\player\token"
xcopy /y /q "%KIT%materialsrc\*" "%GAME%\materialsrc\models\player\token\" >nul
for %%f in ("%GAME%\materialsrc\models\player\token\*.tga") do "%GMOD%\bin\vtex.exe" -nopause -quiet -game "%GAME%" "%%f"
echo [2/4] Copying materials...
if not exist "%MD%" mkdir "%MD%"
xcopy /y /q "%KIT%materials\*.vmt" "%MD%\" >nul
echo [3/4] Compiling models...
if exist "%KIT%studiomdl_log.txt" del "%KIT%studiomdl_log.txt"
''').replace('token_kit.zip',KITZIP)
    for m in plan: s+='echo    %s\n"%%GMOD%%\\bin\\studiomdl.exe" -nop4 -game "%%GAME%%" "%%KIT%%modelsrc\\%s.qc" >> "%%KIT%%studiomdl_log.txt" 2>&1\n'%(m,m)
    s+='findstr /i /c:"ERROR" /c:"too many" "%KIT%studiomdl_log.txt"\necho [4/4] Collecting PAC3 files...\nset OUT=%KIT%pac3\nif exist "%OUT%" rmdir /s /q "%OUT%"\nmkdir "%OUT%"\n'
    for m,info in plan.items():
        s+='mkdir "%%OUT%%\\%s"\n'%m
        for ext in ('mdl','vvd','dx90.vtx','phy'): s+='if exist "%%MO%%\\%s.%s" copy /y "%%MO%%\\%s.%s" "%%OUT%%\\%s\\" >nul\n'%(m,ext,m,ext,m)
        for mt in info['materials']:
            s+='copy /y "%%MD%%\\%s.vmt" "%%OUT%%\\%s\\" >nul\nif exist "%%MD%%\\%s.vtf" copy /y "%%MD%%\\%s.vtf" "%%OUT%%\\%s\\" >nul\nif exist "%%MD%%\\%s_n.vtf" copy /y "%%MD%%\\%s_n.vtf" "%%OUT%%\\%s\\" >nul\n'%(mt,m,mt,mt,m,mt,mt,m)
    s+=('if exist "%KIT%token_pac3.zip" del "%KIT%token_pac3.zip"\npowershell -NoProfile -Command "Compress-Archive -Path \'%OUT%\\*\' -DestinationPath \'%KIT%token_pac3.zip\'"\n').replace('token_pac3.zip',PACZIP)+'echo Done. Log: %KIT%studiomdl_log.txt  -  tell Claude when finished.\npause\n'
    return s
if __name__=='__main__': main()
