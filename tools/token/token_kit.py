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
   'arms':{'gorilla_black':['arms','ga_dec_decal_holstered_forearm_01','ga_dec_decal_tapes2','ga_dec_decal_hand_top','ga_dec_decal_cyberware_text','ga_dec_decal_under_cyberware','ga_dec_decal_holes','ga_dec_decal_betewwn_fingers']},
   'arms_cyber':{'gorilla_black':['ga_fingers','ga_glass','ga_end']},
   'arms_plates_l':{'gorilla_black':['ga_cyber@L']},
   'arms_plates_r':{'gorilla_black':['ga_cyber@R']},   # own submodel: full-res Gorilla plates exceed one submodel's 65k verts with the arm skin
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
 'token_headwear':{
   'head_acc':{'headset_black':['hs_bd','hs_specs','hs_glass']},
 },
 'token_jewelry':{
   'neck_jewelry':{'valentino_cross_silver':['vchain','vcross']},
   'wrist_left':{'nd_cross_bracelet':['nd_acc']},
 },
}
FLATTEN={'bolero_ml':0.15,'bolerocuff_ml':0.15}
LEATHER=' "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "20"\n "$phongboost" "0.35"\n "$phongfresnelranges" "[0.3 0.6 1]"\n{A}'
SILVER=' "$envmap" "env_cubemap"\n "$envmaptint" "[.45 .45 .47]"\n "$envmapcontrast" "1"\n "$envmapsaturation" "0"\n "$envmapfresnel" "0.6"\n "$phong" "1"\n "$phongexponent" "80"\n "$phongboost" "4"\n "$phongalbedotint" "1"\n "$phongfresnelranges" "[0.6 0.8 1]"\n "$rimlight" "1"\n "$rimlightexponent" "8"\n "$rimlightboost" "0.6"\n{A}'
BLACKMETAL=' "$nocull" "1"\n "$envmap" "environment maps/metal_generic_002"\n "$envmaptint" "[.07 .07 .075]"\n "$phong" "1"\n "$phongexponent" "35"\n "$phongboost" "2.5"\n "$phongfresnelranges" "[0.4 0.8 1]"\n "$halflambert" "1"\n{A}'
BLACKMETAL_N=' "$bumpmap" "{D}/{M}_n"\n'+BLACKMETAL
CARDS_DARK=' "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "10"\n "$phongboost" "0.12"\n'
EYES=' "$selfillum" "1"\n "$selfillumtint" "[2.2 2.2 2.2]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "1"\n'
HAIR=' "$bumpmap" "{D}/{M}_n"\n "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n'
PLATE=' "$bumpmap" "{D}/{M}_n"\n "$normalmapalphaenvmapmask" "1"\n "$envmap" "environment maps/metal_generic_002"\n "$envmaptint" "[1.1 1.1 1.15]"\n "$envmapcontrast" "1"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "5"\n "$phongfresnelranges" "[0.5 0.8 1]"\n "$alphatest" "1"\n "$alphatestreference" "0.5"\n'.replace('{D}',MATDIR).replace('{M}','token_{NM}')
HSPLASTIC=' "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "40"\n "$phongboost" "3"\n "$phongfresnelranges" "[0.3 0.7 1]"\n'
VMT_OVERRIDE={'hs_bd':HSPLASTIC,'hs_specs':HSPLASTIC,'hs_glass':' "$envmap" "env_cubemap"\n "$envmaptint" "[.25 .25 .27]"\n "$envmapfresnel" "1"\n "$phong" "1"\n "$phongexponent" "120"\n "$phongboost" "6"\n "$phongfresnelranges" "[0.3 0.7 1]"\n','ga_glass':' "$nocull" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.08 .08 .09]"\n "$phong" "1"\n "$phongexponent" "80"\n "$phongboost" "2"\n','eyeshadow':' "$translucent" "1"\n "$nocull" "1"\n','cyberware':BLACKMETAL,'ga_cyber':BLACKMETAL,'ga_fingers':BLACKMETAL,'ga_end':BLACKMETAL,'earcyber':BLACKMETAL,'piercing':BLACKMETAL,
 'facecw_face':BLACKMETAL_N,'facecw_nose':BLACKMETAL_N,'eyes':EYES,
 'hair':HAIR,'hatfur':HAIR,'brows':' "$bumpmap" "{D}/{M}_n"\n'+CARDS_DARK.replace('"0.12"','"0.05"'),'brows_s7':CARDS_DARK,'brows_s14':CARDS_DARK,'lashes':CARDS_DARK,
 'haircap':HAIR.replace('"0.4"','"0.12"'),'bolero_ml':LEATHER,'bolerocuff_ml':LEATHER,'chain_silver':SILVER,'earring':SILVER,'nd_acc':SILVER,'vchain':SILVER,'vcross':SILVER}
DARKEN={'jeans':0.55,'coatcap':0.5,'bolero_ml':0.38,'bolerocuff_ml':0.38,'mis_tank':0.7,'den_pants':0.7,'vinyl':0.7,'hair':0.3,'hatfur':0.32,'haircap':0.3,'brows':0.6,'brows_s7':0.6,'brows_s14':0.6,'chain_silver':0.62,'earring':1.1,'nd_acc':0.8,'vchain':1.0,'vcross':1.0}   # polished metal: dark diffuse, the shine comes from the cubemap
BODY_MODEL='token_body'; KEEP=False; KITZIP='token_kit.zip'; PACZIP='token_pac3.zip'; BATNAME='compile_token.bat'
DEFAULT_ON={'head','arms','neck_cyberware','head_hair','face_cyberware','face_piercings','face_decal','ear_left','ear_right'}   # groups without a 'blank' at index 0

# ---------------- budget: Gmod-friendly triangle counts ----------------
DECIMATE={'jeans':0.28,'cyberware':0.40,'jacketcap':0.35,'bolero_ml':0.6,'den_boots':0.45,'syn_pants':0.7,'den_hoodie':0.8,'den_pants':0.8,'mis_tank':0.8,'maine':0.35,'earcyber':0.7,}
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
RIGID_EXTRA={'earring':'token_earring'}
RIGID={'vchain':'ValveBiped.Bip01_Spine4','vcross':'ValveBiped.Bip01_Spine4','earring':'ValveBiped.Bip01_Head1','chain_silver':'ValveBiped.Bip01_Pelvis','nd_acc':'ValveBiped.Bip01_L_Forearm'}
HEADLIKE={'skin','lashes','eyeshadow','eyes','brows','brows_s7','brows_s14','hair','haircap','hatcap','hatfur','facecw_face','facecw_nose','piercing','maine','earcyber'}
def head_skin(pos,nrm):
    """head/face/hair: one rigid move (the torso/head translation the retarget uses), weights by height:
    chest -> neck -> head with smooth blends (no per-face-bone noise; Gmod has no face bones)"""
    T=RT.D['Head']; P=(RT.C@pos.T).T*RT.S; P=(T[:3,:3]@P.T).T+T[:3,3]; N=(RT.C@nrm.T).T
    z=P[:,2]; zh=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][2,3]; zn=RT.NW[RT.vn.index('ValveBiped.Bip01_Neck1')][2,3]
    iH=RT.vn.index('ValveBiped.Bip01_Head1'); iN=RT.vn.index('ValveBiped.Bip01_Neck1'); iS=RT.vn.index('ValveBiped.Bip01_Spine4')
    sm=lambda x: x*x*(3-2*x)
    # head vs neck split along the jaw line (tilted: chin bottom in front, skull base behind), so the whole face incl. jaw/chin turns with Head1
    zcut=62.0+P[:,1]*(3.0/7.0)
    wh=sm(np.clip((z-zcut+0.6)/1.2,0,1)); wn_=sm(np.clip((z-(zn-2.5))/3.0,0,1))
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
 'skin_body':' "$nocull" "1"\n "$bumpmap" "{D}/{M}_n"\n "$phong" "1"\n "$phongexponent" "14"\n "$phongboost" "0.5"\n "$phongfresnelranges" "[0.2 0.6 1.2]"\n "$halflambert" "1"\n',
 'skin_arms':' "$bumpmap" "{D}/{M}_n"\n "$phong" "1"\n "$phongexponent" "14"\n "$phongboost" "0.5"\n "$phongfresnelranges" "[0.2 0.6 1.2]"\n "$halflambert" "1"\n',
 'cards':' "$alphatest" "1"\n "$alphatestreference" "0.4"\n "$allowalphatocoverage" "1"\n "$nocull" "1"\n "$halflambert" "1"\n "$phong" "1"\n "$phongexponent" "8"\n "$phongboost" "0.4"\n "$phongfresnelranges" "[0.3 0.6 1]"\n',
 'eyes':' "$selfillum" "1"\n "$selfillumtint" "[1.6 1.6 1.6]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "3"\n',
 'glass':' "$translucent" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.06 .06 .07]"\n "$phong" "1"\n "$phongexponent" "80"\n "$phongboost" "1.5"\n',
 'glow':' "$selfillum" "1"\n "$selfillumtint" "[4 .2 .15]"\n',
 'metal':' "$envmap" "environment maps/metal_generic_002"\n "$envmaptint" "[.35 .35 .37]"\n "$envmapsaturation" "0.4"\n "$phong" "1"\n "$phongexponent" "40"\n "$phongboost" "3"\n "$phongfresnelranges" "[0.6 0.85 1]"\n "$halflambert" "1"\n{A}',
 'decal':' "$alphatest" "1"\n "$alphatestreference" "0.45"\n "$allowalphatocoverage" "1"\n "$halflambert" "1"\n',
 'cloth':' "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "12"\n "$phongboost" "1.2"\n "$phongfresnelranges" "[0.4 0.7 1]"\n{A}',
}
VMT_OVERRIDE['skin']=VMTX['skin_head']+' "$nocull" "1"\n'   # face/lids drawn from both sides: no holes where CP's lid normals face inward
TEXCAP={'hs_bd':2048,'hs_specs':2048,'skin':2048,'arms':2048,'body':1024,'mis_tank':2048,'hair':1024,'coatfur':1024,'jacketfur':1024}   # 2048 only where detail reads up close (face, tattooed arms, tank print); everything else 1024
def to_tga(im,nm):
    cap=TEXCAP.get(nm,512 if nm.startswith('ga_dec') else 1024); w,h=im.size; s=min(1.0,cap/max(w,h))
    if s<1: im=im.resize((max(4,int(w*s)),max(4,int(h*s))),Image.LANCZOS)
    return im
NORMALS={  # extra normal maps where they carry the look
 'skin':'/home/claude/work/build/../tex/base/h0_000_pma_c__basehead_n01.png',
 'body':'/home/claude/work/tex/base/t0_000_ma__c_base_n03_censored.png',
 'arms':'/home/claude/work/tex/base/a0_000_ma_base__hq_nd01.png',
 'facecw_face':'/home/claude/work/tex/base/hx_cyberware_13_m02.png','facecw_nose':'/home/claude/work/tex/base/hx_cyberware_13_d02.png'}
CAP=None
def rigid_pieces(Fi,lk):
    """each separate armour piece (connected component) gets ONE weight set = its average: plates move as solid
    metal instead of stretching across a knuckle (CP drove them with muscle helpers Source doesn't have)"""
    from scipy.sparse import coo_matrix; from scipy.sparse.csgraph import connected_components
    import collections
    n=len(lk); g=coo_matrix((np.ones(len(Fi)*3),(np.r_[Fi[:,0],Fi[:,1],Fi[:,2]],np.r_[Fi[:,1],Fi[:,2],Fi[:,0]])),shape=(n,n))
    _,lab=connected_components(g,directed=False); acc=collections.defaultdict(collections.Counter)
    for v,l in enumerate(lab):
        for b,w in lk[v]: acc[l][b]+=w
    comp={}
    for l,c in acc.items():
        top=c.most_common(2); t=sum(w for _,w in top); comp[l]=[(b,w/t) for b,w in top]
    return [comp[l] for l in lab]
def smooth_hand_links(Fi,lk,iters=10):
    """Laplacian-smooth bone weights where a vertex blends the hand with a finger root or two finger roots
    (thumb web, ring/pinky web): Kleiner's idle swings the thumb 31 deg and the pinky 45 deg, and CP's sharp
    weight borders there tore the skin. Smoothing spreads each joint's bend over the surrounding web."""
    import collections
    roots={RT.vn.index('ValveBiped.Bip01_%s_%s'%(sd,b)) for sd in 'LR' for b in ('Hand','Finger0','Finger1','Finger2','Finger3','Finger4')}
    n=len(lk); W=[dict(l) for l in lk]
    act=np.array([len(set(w)&roots)>=2 or (len(w)>=2 and set(w)<=roots) for w in W])
    if not act.any(): return lk
    nb=[set() for _ in range(n)]
    for a,b,c in Fi: nb[a]|={b,c}; nb[b]|={a,c}; nb[c]|={a,b}
    # grow the active region by 2 rings so the blend has room
    for _ in range(2):
        g=act.copy()
        for v in np.where(act)[0]: g[list(nb[v])]=True
        act=g
    act&=np.array([set(w)<=roots|{RT.vn.index('ValveBiped.Bip01_L_Forearm'),RT.vn.index('ValveBiped.Bip01_R_Forearm')} for w in W])
    idx=np.where(act)[0]
    for _ in range(iters):
        new={}
        for v in idx:
            acc=collections.Counter(W[v]); 
            for u in nb[v]:
                for b,w in W[u].items(): acc[b]+=w
            tot=sum(acc.values()); new[v]={b:w/tot for b,w in acc.items()}
        for v,w in new.items(): W[v]=w
    out=[]
    for w in W:
        top=sorted(w.items(),key=lambda x:-x[1])[:3]; t=sum(x for _,x in top); out.append([(b,x/t) for b,x in top])
    return out
HAND_UV_MASK=None
def _grade(im,rgb=(66,42,30)):
    a=np.asarray(im).astype(np.float32)/255; lin=a[...,:3]**2.2; tgt=(np.array(rgb,np.float32)/255)**2.2
    Y=lin@np.array([0.2126,0.7152,0.0722],np.float32); Ym=np.median(Y); r=np.exp(np.log(np.clip(Y/max(Ym,1e-6),1e-3,None))*0.75)
    warm=lin/np.maximum(Y[...,None],1e-6); warm=warm/np.median(warm.reshape(-1,3),0); hue=np.clip(1+(warm-1)*0.35,0.6,1.6)
    out=np.clip(tgt*r[...,None]*hue,0,1)**(1/2.2); return np.dstack([out*255,a[...,3:]*255])
def untattoo_hands(im):
    """tattoo stops at the wrist: under the Gorilla hand the skin is clean (the female VTK sleeve ran onto the hand)"""
    if HAND_UV_MASK is None: return im
    from PIL import ImageFilter
    clean=Image.fromarray(_grade(Image.open('/home/claude/work/tex/base/a0_000_ma__c_base_hq_d01.png').convert('RGBA')).astype(np.uint8),'RGBA').resize(im.size,Image.LANCZOS)
    m=HAND_UV_MASK.resize(im.size,Image.LANCZOS).filter(ImageFilter.GaussianBlur(im.size[0]/256))
    m=np.asarray(m).astype(np.float32)[...,None]/255; a=np.asarray(im.convert('RGBA')).astype(np.float32); c=np.asarray(clean).astype(np.float32)
    a[...,:3]=a[...,:3]*(1-m)+c[...,:3]*m; return Image.fromarray(a.astype(np.uint8),'RGBA')
OCC_PARAM={'arms':(0.14,0.0,True)}
SINK={'arms':0.05}   # name -> (reach in, edge margin in, two-sided)
CUT_ABOVE={'den_boots':(6.5,'jeans')}   # part -> (height in inches, only when this covering garment is in the same model)
OCCLUDE={'arms':['ga_fingers'],'mis_tank':['bolero_ml','bolerocuff_ml'],'mis_print':['bolero_ml'],'mis_stitch':['bolero_ml','bolerocuff_ml']}   # inner layer -> outer layers that cover it
OUTER={}   # outer part name -> (points, normals) in bind space, filled per model
def covered(vp,vn,outer_names,reach=1.4,margin=2.4,both=False):
    """vertex is hidden if an outer garment surface lies within `reach` inches on its outward side"""
    from scipy.spatial import cKDTree
    pts=[OUTER[o][0] for o in outer_names if o in OUTER]
    if not pts: return np.zeros(len(vp),bool)
    P=np.concatenate(pts); tree=cKDTree(P); hid=np.zeros(len(vp),bool)
    for k,nb in enumerate(tree.query_ball_point(vp,reach)):
        if nb: hid[k]=True if both else ((P[nb]-vp[k])@vn[k]>-0.15).any()
    vis=~hid
    if margin>0 and vis.any() and hid.any():   # keep a margin under the jacket's edges so no gap opens at the opening
        d,_=cKDTree(vp[vis]).query(vp[hid]); h=np.where(hid)[0]; hid[h[d<margin]]=False
    return hid
METAL_MASKED={'vinyl','den_pants','hs_bd','hs_specs'}   # garments with metal hardware (boot chains, buckles, zips): metal areas reflect, stay bright
def metal_of(nm,size):
    mr=STAGED_MATS.get(nm,{}).get('mr')
    if mr is None: return None
    return np.asarray(mr.convert('RGB').resize(size,Image.LANCZOS)).astype(np.float32)[...,2]/255
EYE_LID_SIGN=1
LOCK_FINGERS=True
REFIT_HAND=False
if LOCK_FINGERS:   # fingers ride the hand: keep CP's own finger shape (no per-finger fit onto Kleiner's bones = no twisted thumb)
    for _n in list(RT.D):
        for _sd in ('Left','Right'):
            if _n.startswith(_sd+'Hand') and _n!=_sd+'Hand': RT.D[_n]=RT.D[_sd+'Hand'].copy()   # keep the CP artist finger weights (retarget already lands each CP finger joint on the Kleiner knuckle)   # citizen player models don't hand their finger bones to merged models (male_05 check): fingers ride the hand bone, pre-curled
FCURL=None
def _finger_curl_mats(deg=0):
    """world-space transforms (bind -> relaxed-curl pose) for every finger bone"""
    def axrot(a,ang):
        a=a/np.linalg.norm(a); K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]]); return np.eye(3)+np.sin(ang)*K+(1-np.cos(ang))*K@K
    names=RT.vn; par=RT.vp; NW=[np.array(m) for m in RT.NW]; P=[m.copy() for m in NW]; idx={n:i for i,n in enumerate(names)}
    kids=lambda i:[c for c in range(len(names)) if par[c]==i]
    def sub(i):
        out=[i]; [out.extend(sub(c)) for c in kids(i)]; return out
    for sd in 'LR':
        f1=NW[idx['ValveBiped.Bip01_%s_Finger1'%sd]][:3,3]; f3=NW[idx['ValveBiped.Bip01_%s_Finger3'%sd]][:3,3]
        for f in range(1,5):
            for seg in ('%d'%f,'%d1'%f,'%d2'%f):
                i=idx['ValveBiped.Bip01_%s_Finger%s'%(sd,seg)]; pv=P[i][:3,3].copy(); ch=kids(i)
                fdir=(P[ch[0]][:3,3]-pv) if ch else P[i][:3,:3][:,0]
                R=axrot(np.cross(f3-f1,fdir),np.radians(deg*(0.8 if seg==str(f) else 1.0)))
                for j in sub(i): P[j][:3,:3]=R@P[j][:3,:3]; P[j][:3,3]=R@(P[j][:3,3]-pv)+pv
    return {i:P[i]@np.linalg.inv(NW[i]) for i,n in enumerate(names) if 'Finger' in n}
def lock_fingers(vp,vn,lk):
    global FCURL
    if FCURL is None: FCURL=_finger_curl_mats()
    hand={sd:RT.vn.index('ValveBiped.Bip01_%s_Hand'%sd) for sd in 'LR'}
    vp=vp.copy(); vn=vn.copy(); out=[]
    for k,links in enumerate(lk):
        fw=[(b,w) for b,w in links if b in FCURL]
        if not fw: out.append(links); continue
        p4=np.append(vp[k],1.0); acc=np.zeros(3); accn=np.zeros(3); tw=0
        for b,w in links:
            M=FCURL.get(b,np.eye(4)); acc+=w*(M@p4)[:3]; accn+=w*(M[:3,:3]@vn[k]); tw+=w
        vp[k]=acc/tw; vn[k]=accn/max(np.linalg.norm(accn),1e-9)
        h=hand['L' if vp[k][0]>0 else 'R']; nl={}
        for b,w in links: bb=h if b in FCURL else b; nl[bb]=nl.get(bb,0)+w
        out.append(list(nl.items()))
    return vp,vn,out
def _hand_segments(side):
    nw=lambda n: RT.NW[RT.vn.index('ValveBiped.Bip01_%s_%s'%(side,n))][:3,3]
    segs=[]
    for f in range(5):
        ch=['Finger%d'%f,'Finger%d1'%f,'Finger%d2'%f]; P=[nw(c) for c in ch]
        tip=P[2]+(P[2]-P[1])*0.9; ends=[P[1],P[2],tip]
        for k,(c,a,b) in enumerate(zip(ch,P,ends)): segs.append((RT.vn.index('ValveBiped.Bip01_%s_%s'%(side,c)),a,b,k==0))
    h=nw('Hand'); segs.append((RT.vn.index('ValveBiped.Bip01_%s_Hand'%side),h,nw('Finger2'),False))
    return segs
HANDSEG=None
def refit_hand(vp,lk):
    """Keep which finger each vertex belongs to (from CP's own weights), but re-split it along the Valve finger's three
    segments so it bends exactly at the citizen's knuckles; palm stays on the hand bone."""
    global HANDSEG
    if HANDSEG is None: HANDSEG={sd:_hand_segments(sd) for sd in ('L','R')}
    fid={}
    for sd,segs in HANDSEG.items():
        for k,(b,a,c,base) in enumerate(segs[:15]): fid[b]=(sd,k//3)
    out=[]
    for v,links in zip(vp,lk):
        fw={}
        for b,w in links:
            if b in fid: fw[fid[b]]=fw.get(fid[b],0)+w
        if not fw: out.append(links); continue
        key,wf=max(fw.items(),key=lambda x:x[1])
        if wf<0.5: out.append(links); continue
        sd,f=key; segs=HANDSEG[sd][3*f:3*f+3]; d=[]
        for b,a,c,base in segs:
            ab=c-a; L2=max(np.dot(ab,ab),1e-9); tr=np.dot(v-a,ab)/L2; t=np.clip(tr,0,1); d.append((np.linalg.norm(v-(a+t*ab)),b,tr))
        # position along the finger decides the segment; blend across each joint over ~0.25 in
        b0,b1,b2=[x[1] for x in d]; L0=np.linalg.norm(segs[0][2]-segs[0][1]); L1=np.linalg.norm(segs[1][2]-segs[1][1])
        s_=d[0][2]*L0                       # distance along finger from knuckle
        hand=[(b,w) for b,w in links if b not in fid]
        bw=0.25
        def blend(x,lo,hi):                 # weight of 'hi' side around joint at x=0
            return float(np.clip(0.5+x/(2*bw),0,1))
        if s_<0.0:   wk=blend(s_,None,None); nl=[(b0,wk)]+[(b,w*(1-wk)/max(sum(w for _,w in hand),1e-6)) for b,w in hand] if hand else [(b0,1.0)]
        elif s_<L0:  w1=blend(s_-L0,None,None); nl=[(b0,1-w1),(b1,w1)]
        else:
            s2=s_-L0; w2=blend(s2-L1,None,None); nl=[(b1,1-w2),(b2,w2)]
        nl=[(b,w) for b,w in nl if w>1e-3]; tot=sum(w for _,w in nl); nl=[(b,w/tot) for b,w in nl]
        out.append(nl)
    return out
BASE_FROM_STAGING={'ga_cyber','ga_end','ga_fingers','chain_silver','vcross'}
UPRIGHT=np.array([[0,1.0,0],[-1.0,0,0],[0,0,1.0]])   # columns: forward (0,-1,0), left (1,0,0), up (0,0,1) in the bind skeleton's world
LOCAL_PIVOT={}   # model -> (bone, pivot world): PAC-attached props (not bonemerged); verts stored in that bone's local frame, origin at the pivot
VN=list(RT.vn); VP=list(RT.vp); NLX=list(RT.NL); JIGGLE={}   # extra procedural bones (jigglebones) appended after the Valve skeleton
def add_jiggle_bone(name,parent,pivot,length):
    W=RT.NW[RT.vn.index(parent)]
    E=W.copy(); E[:3,3]=pivot   # same orientation as the head bone: rest pose is exactly the head's, whatever its axes are in game
    VN.append(name); VP.append(RT.vn.index(parent)); NLX.append(np.linalg.inv(W)@E); JIGGLE[name]=length
    return len(VN)-1
STAGED_MATS=pickle.load(open('/home/claude/work/token/staged_mats.pkl','rb')) if os.path.exists('/home/claude/work/token/staged_mats.pkl') else {}
if os.path.exists('/home/claude/work/headset/headset_mats.pkl'): STAGED_MATS.update(pickle.load(open('/home/claude/work/headset/headset_mats.pkl','rb')))
DERIVED_NORMAL={'hair':12.0,'hatfur':6.0,'haircap':8.0}
# name -> [(offset mm, alphatest ref or None = same material)]
SHELLS={'facecw_face':[(0.2*k,None) for k in range(1,13)],'facecw_nose':[(0.2*k,None) for k in range(1,13)],
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
    NDONE=set(); texdone_n=lambda nm: nm in NDONE
    global CAP, HAND_UV_MASK
    if 'arms' in byname:
        from PIL import ImageDraw
        M=Image.new('L',(2048,2048),0); dr=ImageDraw.Draw(M)
        wx=abs(RT.NW[RT.vn.index('ValveBiped.Bip01_L_Hand')][0,3])-0.6   # just before the wrist joint
        for p in byname['arms']:
            nr=p.get('nrm'); nr=p.get('src_nrm') if nr is None else nr
            q=RT.retarget(p['pos'].astype(np.float64),np.asarray(nr)[:,:3].astype(np.float64),np.asarray(p['ji']),np.asarray(p['jw']),p['bones'],p['bonepos'])[0]
            F=p['idx'].reshape(-1,3); uv=np.asarray(p['uv'])
            for t in F[(np.abs(q[F][:,:,0])>wx).all(1)]:
                dr.polygon([(uv[k,0]*2048,uv[k,1]*2048) for k in t],fill=255)
        HAND_UV_MASK=M; print('   hand UV mask px',int((np.asarray(M)>0).sum()))
    if 'earring' in byname: LOCAL_PIVOT.setdefault('token_earring',None)
    if 'earring' in byname and 'token_earring' not in VN:
        p=byname['earring'][0]; q=head_skin(p['pos'].astype(np.float64),np.tile([0,0,1.0],(len(p['pos']),1)))[0]
        q=q[np.unique(p['idx'])]; top=q[q[:,2]>=np.percentile(q[:,2],97)].mean(0); L=float(top[2]-q[:,2].min())
        add_jiggle_bone('token_earring','ValveBiped.Bip01_Head1',top,L); print('   earring jigglebone pivot',top.round(2),'length %.2f in'%L)
    if 'haircap' in byname:
        CAP=np.concatenate([head_skin(p['pos'].astype(np.float64),np.tile([0,0,1.0],(len(p['pos']),1)))[0] for p in byname['haircap']])
    NL=RT.NL
    def emit_mat(nm,p):
        if nm in texdone: return
        texdone.add(nm); c=cls(nm); tex=p.get('tex')
        im=tex if tex is not None else Image.new('RGBA',(8,8),(128,128,128,255))
        if nm in BASE_FROM_STAGING and STAGED_MATS.get(nm,{}).get('base') is not None: im=STAGED_MATS[nm]['base']   # the staging material's own colour (the part's raw tex is the arm skin for Gorilla plates)
        if nm=='ga_glass': im=Image.new('RGBA',(256,256),(10,10,12,255))   # tinted cyber-glass (the part carried the arm skin texture)
        if nm=='arms': im=untattoo_hands(im)
        im=to_tga(im.convert('RGBA'),nm)
        _p2=lambda v:1<<max(2,round(np.log2(v)))
        if im.size!=(_p2(im.size[0]),_p2(im.size[1])): im=im.resize((_p2(im.size[0]),_p2(im.size[1])),Image.LANCZOS)
        if nm in FLATTEN:    # baked wear/scuff layers read as grey paint in Gmod's albedo-only shading: pull them back toward the base colour
            a=np.asarray(im).astype(np.float32); base=np.median(a[...,:3].reshape(-1,3),0)
            a[...,:3]=base+(a[...,:3]-base)*FLATTEN[nm]; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8),im.mode)
        if nm in ('cyberware','ga_cyber','earcyber','ga_fingers','ga_end'):
            a=np.asarray(im).astype(np.float32); rgb=a[...,:3]; sat=(rgb.max(2)-rgb.min(2))/np.maximum(rgb.max(2),1)
            k=np.where(sat<0.35,0.35,1.0)[...,None]; a[...,:3]=rgb*k; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8),im.mode)
        if nm in DARKEN:
            a=np.asarray(im).astype(np.float32); k=DARKEN[nm]
            mt=metal_of(nm,im.size) if nm in METAL_MASKED else None
            if mt is not None: k=(k*(1-mt)+1.25*mt)[...,None]
            a[...,:3]*=k; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8),im.mode)
        if nm in ('facecw_face','facecw_nose'):   # Emmerich plates: crisp metal plate (alphatest) + chrome bevels from the normal map + soft incision rim (translucent)
            a=np.asarray(im.convert('RGBA')).astype(np.float32); al=a[...,3]/255
            plate=(al>0.6).astype(np.float32); rim=np.where(al<=0.6,al,0)
            pl=np.dstack([np.full(al.shape,14.0),np.full(al.shape,14.0),np.full(al.shape,16.0),plate*255]).astype(np.uint8)
            Image.fromarray(pl,'RGBA').save(KIT+'materialsrc/%s_%s.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s.txt'%(NAME,nm),'w').write('nocompress 0\n')
            rm=np.dstack([np.full(al.shape,34.0),np.full(al.shape,21.0),np.full(al.shape,15.0),rim*255]).astype(np.uint8)
            Image.fromarray(rm,'RGBA').save(KIT+'materialsrc/%s_%s_rim.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_rim.txt'%(NAME,nm),'w').write('nocompress 0\n')
            n=nrm_rgb(NORMALS[nm]); na=np.asarray(n).astype(np.float32)/255*2-1; tilt=1-np.clip(na[...,2],0,1)
            em=np.clip(0.18+tilt*6,0,1); n=n.convert('RGBA'); n.putalpha(Image.fromarray((em*255).astype(np.uint8)))
            n.resize((1024,1024),Image.LANCZOS).save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n')
            open(KIT+'materials/%s_%s.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,PLATE.replace('{NM}',nm)))
            open(KIT+'materials/%s_%s_rim.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s_rim"\n "$translucent" "1"\n "$halflambert" "1"\n}\n'%(MATDIR,NAME,nm))
            return
        if nm=='eyes':
            a=np.asarray(im.convert('RGBA')).astype(np.float32); H,W=a.shape[:2]; yy,xx=np.mgrid[0:H,0:W]
            r=np.hypot(xx/W-0.5,yy/H-0.46); rgb=a[...,:3]; sat=(rgb.max(2)-rgb.min(2))/np.maximum(rgb.max(2),1); lum=rgb.mean(2)/255
            m=((r<0.205)*np.clip((lum-0.35)*2.5,0,1)+(r<0.32)*(r>0.205)*(sat>0.45)*(lum>0.35)*0.8)
            lid=np.clip((yy/H-0.46)/0.22*(-1)*EYE_LID_SIGN,0,1)   # 0 at the iris centre -> 1 toward the upper lid
            shade=np.where(r>0.215,0.55,1.0)*(1-0.75*lid**0.8)
            a[...,:3]*=shade[...,None]   # sclera + upper-lid shadow (Source has no eye AO, so the eye white read as a hole in the lid)
            a[...,3]=np.clip(m,0,1)*255; im=Image.fromarray(a.astype(np.uint8),'RGBA')
            im.save(KIT+'materialsrc/%s_%s.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s.txt'%(NAME,nm),'w').write('nocompress 0\n')
            open(KIT+'materials/%s_%s.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,EYES)); return
        has_a=np.asarray(im)[...,3].min()<250
        if c not in ('cards','decal','glass') and not has_a: im=im.convert('RGB')
        im.save(KIT+'materialsrc/%s_%s.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s.txt'%(NAME,nm),'w').write('nocompress 0\n')
        A=''; HASN=False
        if nm in DERIVED_NORMAL:   # strand-level relief from the albedo itself (breaks the smooth 'plastic' look of hair geometry)
            g=np.asarray(im.convert('L').resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255*DERIVED_NORMAL[nm]
            gx=np.roll(g,-1,1)-np.roll(g,1,1); gy=np.roll(g,-1,0)-np.roll(g,1,0); n=np.dstack([-gx,-gy,np.ones_like(g)]); n/=np.linalg.norm(n,axis=2,keepdims=True)
            Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n')
        elif nm in STAGED_MATS and STAGED_MATS[nm].get('normal') is not None and nm not in DERIVED_NORMAL and nm not in ('facecw_face','facecw_nose'):
            # the staging material's own normal map (CP garment normal + layer detail), gloss mask in alpha = Source phong mask
            sm=STAGED_MATS[nm]; n=sm['normal'].convert('RGB').resize((2048,2048) if nm in ('skin','hs_bd','hs_specs') else (1024,1024),Image.LANCZOS)
            if sm.get('mr') is not None: rough=np.asarray(sm['mr'].convert('RGB').resize(n.size,Image.LANCZOS)).astype(np.float32)[...,1]/255
            else: rough=np.full(n.size[::-1],float(sm.get('rough') or 0.6),np.float32)
            gloss=np.clip((1-rough)*1.3,0,1)**1.5
            if nm in METAL_MASKED and sm.get('mr') is not None:
                mt=np.asarray(sm['mr'].convert('RGB').resize(n.size,Image.LANCZOS)).astype(np.float32)[...,2]/255; gloss=np.clip(mt*(mt>0.6),0,1) if not nm.startswith('hs_') else np.clip(mt+0.35*gloss,0,1)   # only real metal reflects (headset: glossy plastic gets a little too)
            n=n.convert('RGBA'); n.putalpha(Image.fromarray((gloss*255).astype(np.uint8)))
            n.save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n'); NDONE.add(nm)
        elif nm in NORMALS and os.path.exists(NORMALS[nm]):
            nrm_rgb(NORMALS[nm],size=(1024,1024)).save(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)); open(KIT+'materialsrc/%s_%s_n.txt'%(NAME,nm),'w').write('nocompress 0\nnormal 1\n')
        elif c in ('skin_head','skin_body','skin_arms'): c='cloth'
        if c in ('metal','cloth') and has_a: A=' "$alphatest" "1"\n "$alphatestreference" "0.45"\n'
        body=VMT_OVERRIDE.get(nm,VMTX[c])
        if os.path.exists(KIT+'materialsrc/%s_%s_n.tga'%(NAME,nm)) and '$bumpmap' not in body and texdone_n(nm): body=' "$bumpmap" "{D}/{M}_n"\n'+body
        if nm in METAL_MASKED: body+=' "$envmap" "env_cubemap"\n "$normalmapalphaenvmapmask" "1"\n "$envmaptint" "[.35 .35 .36]"\n "$envmapcontrast" "1"\n "$envmapsaturation" "0"\n'
        body=body.replace('{A}',A).replace('{D}',MATDIR).replace('{M}','%s_%s'%(NAME,nm))
        open(KIT+'materials/%s_%s.vmt'%(NAME,nm),'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,body))
    def tris_of(names,chunks=None):
        T=[]
        for nm in names:
            side=None
            if '@' in nm: nm,side=nm.split('@')   # 'part@L' / 'part@R': one side only (keeps a submodel under 65k verts)
            for p in byname.get(nm,[]):
                if chunks is not None and p.get('chunk') not in chunks: continue
                F=reduce(p)
                if side: cx=p['pos'][F].mean(1)[:,0]; F=F[(cx>0) if side=='L' else (cx<=0)]
                report[nm]=report.get(nm,0)+len(F)
                pos=p['pos'].astype(np.float64); nrm=p.get('nrm'); nrm=p.get('src_nrm') if nrm is None else nrm
                if nrm is None:
                    nrm=np.zeros_like(pos); fn=np.cross(pos[F[:,1]]-pos[F[:,0]],pos[F[:,2]]-pos[F[:,0]])
                    for k in range(3): np.add.at(nrm,F[:,k],fn)
                nrm=np.asarray(nrm)[:,:3].astype(np.float64); nrm/=np.maximum(np.linalg.norm(nrm,axis=1,keepdims=True),1e-9)
                used=np.unique(F); remap=-np.ones(len(pos),int); remap[used]=np.arange(len(used))
                if nm in HEADLIKE or nm=='earring': vp,vn_,lk=head_skin(pos[used],nrm[used])   # earring: one rigid move with the head (no per-vertex bone mixing)
                else: vp,vn_,lk=RT.retarget(pos[used],nrm[used],np.asarray(p['ji'])[used],np.asarray(p['jw'])[used],p['bones'],p['bonepos'])
                if nm in ('arms',) or nm.startswith('ga_'):
                    if REFIT_HAND: lk=refit_hand(vp,lk)
                    lk=lk if LOCK_FINGERS else smooth_hand_links(remap[F],lk)
                    if LOCK_FINGERS: vp,vn_,lk=lock_fingers(vp,vn_,lk)
                if LOCK_FINGERS and nm not in ('arms',) and not nm.startswith('ga_'):   # any other piece touching a finger (cuffs, sleeves) rides the hand too
                    fids={i for i,n in enumerate(RT.vn) if 'Finger' in n}; hL=RT.vn.index('ValveBiped.Bip01_L_Hand'); hR=RT.vn.index('ValveBiped.Bip01_R_Hand')
                    def _rm(links,x):
                        d={}
                        for b,w in links: bb=((hL if x>0 else hR) if b in fids else b); d[bb]=d.get(bb,0)+w
                        return list(d.items())
                    lk=[_rm(l,v[0]) for l,v in zip(lk,vp)]
                if nm in RIGID: lk=[[(RT.vn.index(RIGID[nm]),1.0)]]*len(vp)      # jewelry moves as one piece
                if nm in RIGID_EXTRA and RIGID_EXTRA[nm] in VN: lk=[[(VN.index(RIGID_EXTRA[nm]),1.0)]]*len(vp)   # dangles from its jigglebone
                if nm in HEADLIKE and cls(nm)!='cards':   # some CP head-family meshes carry inward normals: make them face out of the skull
                    hc=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([1.5,0,3.5])
                    if ((vp-hc)*vn_).sum(1).mean()<0: vn_=-vn_
                if nm=='cyberware' and CAP is not None: vp=tuck_under_cap(vp)
                if nm=='eyes': vp=vp+np.array([0,0.03,0])   # seat the eyeballs ~0.75 mm deeper (+y = backward in the bind skeleton) so the lids close over them
                Fi=remap[F].copy()
                if nm in OCCLUDE and any(o in OUTER for o in OCCLUDE[nm]):   # drop inner-layer faces fully under the jacket: they poke through when the citizen animations bend the torso
                    r_,m_,b_=OCC_PARAM.get(nm,(1.4,2.4,False)); hid=covered(vp,vn_,OCCLUDE[nm],r_,m_,b_)
                    if nm in SINK: vp=vp-vn_*SINK[nm]*hid[:,None]; hid[:]=False   # tuck under the shell instead of cutting (cutting left holes at the finger roots)
                    keep=~hid[Fi].all(1); print('   %s: %d/%d faces hidden under %s'%(nm,(~keep).sum(),len(Fi),OCCLUDE[nm])); Fi=Fi[keep]
                if nm in CUT_ABOVE and CUT_ABOVE[nm][1] in OUTER:   # boot shaft hidden inside long pants: delete it so it can't poke through the jeans
                    keep=~(vp[Fi][:,:,2]>CUT_ABOVE[nm][0]).all(1); print('   %s: %d/%d faces cut above z=%.1f'%(nm,(~keep).sum(),len(Fi),CUT_ABOVE[nm][0])); Fi=Fi[keep]
                a,b,c=vp[Fi[:,0]],vp[Fi[:,1]],vp[Fi[:,2]]
                bad=(np.cross(b-a,c-a)*vn_[Fi].sum(1)).sum(1)<0; Fi[bad]=Fi[bad][:,[0,2,1]]; flip=False   # each triangle faces the way its normals point (Source culls back faces)
                emit_mat(nm,p)
                T+=smd.part_tris(vp,vn_,p['uv'][used],Fi.ravel(),lk,'%s_%s'%(NAME,nm),flip=flip)
                if nm in ('facecw_face','facecw_nose'):
                    hc0=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([1.5,0,3.5]); u0=vp-hc0; u0/=np.linalg.norm(u0,axis=1,keepdims=True)
                    T+=smd.part_tris(vp+u0*0.08/25.4,vn_,p['uv'][used],Fi.ravel(),lk,'%s_%s_rim'%(NAME,nm),flip=flip)
                if nm in SHELLS:   # stacked offset shells: real thickness for flat plates / brow hair (fur-shell technique)
                    hc=RT.NW[RT.vn.index('ValveBiped.Bip01_Head1')][:3,3]+np.array([1.5,0,3.5])
                    up=vp-hc; up/=np.linalg.norm(up,axis=1,keepdims=True)
                    for k,(off_mm,ref) in enumerate(SHELLS[nm]):
                        mat='%s_%s'%(NAME,nm) if ref is None else '%s_%s_L%d'%(NAME,nm,k)
                        if ref is not None and mat not in texdone:
                            texdone.add(mat)
                            open(KIT+'materials/%s.vmt'%mat,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s_%s"\n%s}\n'%(MATDIR,NAME,nm,VMT_OVERRIDE[nm].replace('"0.4"','"%.2f"'%ref).replace('{D}',MATDIR).replace('{M}','%s_%s'%(NAME,nm)).replace('{A}','')))
                        T+=smd.part_tris(vp+up*off_mm/25.4,vn_,p['uv'][used],Fi.ravel(),lk,mat,flip=flip)
        return T
    for model,groups in LAYOUT.items():
        qc=['$modelname "player/%s/%s.mdl"'%(NAME,model),'$cdmaterials "%s/"'%MATDIR,'$surfaceprop "flesh"','$model "%s_bind" "%s_bind.smd"'%(model,model)]
        allt=[]; mats=set(); groupsout={}
        OUTER.clear()
        allparts={x for opts in groups.values() for ps in opts.values() for x in ps}
        for o in {x for v in OCCLUDE.values() for x in v}|{c for _,c in CUT_ABOVE.values()}:
            if o in allparts:
                pts=[]; nrs=[]
                for p in byname.get(o,[]):
                    u=np.unique(p['idx']); nr=p.get('nrm'); nr=p.get('src_nrm') if nr is None else nr
                    q,qn=RT.retarget(p['pos'][u].astype(np.float64),np.asarray(nr)[u,:3].astype(np.float64),np.asarray(p['ji'])[u],np.asarray(p['jw'])[u],p['bones'],p['bonepos'])[:2]
                    pts.append(q)
                if pts: OUTER[o]=(np.concatenate(pts),None)
        LOC=LOCAL_PIVOT.get(model)
        if LOC:
            Ji=UPRIGHT.T; piv=np.asarray(LOC[1])   # verts in an upright head-aligned frame (x fwd, y left, z up) at the pivot: keeps PAC's euler jiggle away from gimbal lock
            def localize(T): return [(m,[(Ji@(np.asarray(pp)-piv), Ji@np.asarray(nn), uv,[(0,1.0)]) for (pp,nn,uv,lk) in vs]) for m,vs in T]
            SK=(['root'],[-1],[np.eye(4)])
        else: localize=lambda T:T; SK=(VN,VP,NLX)
        smd.write(KIT+'modelsrc/%s_bind.smd'%model,*SK,[])
        if model==BODY_MODEL:   # body skin regions: each its own toggle (hide skin under clothes)
            for r,ch in BODY_REGIONS.items():
                T=tris_of(['body'],chunks=ch); fn='%s_skin_%s.smd'%(model,r); smd.write(KIT+'modelsrc/'+fn,VN,VP,NLX,T); allt+=T; mats.update(m for m,_ in T)
                qc.append('$bodygroup "skin_%s"\n{\n studio "%s"\n blank\n}'%(r,fn)); groupsout['skin_'+r]=['on','off']
        for g,opts in groups.items():
            lines=[]; names=[]
            if g not in DEFAULT_ON: lines.append(' blank'); names.append('none')
            for o,parts in opts.items():
                T=tris_of(parts); allt+=T
                T=localize(T); fn='%s_%s_%s.smd'%(model,g,o); smd.write(KIT+'modelsrc/'+fn,*SK,T)
                lines.append(' studio "%s"'%fn); names.append(o)
                for m,_ in T: mats.add(m)
            if g in DEFAULT_ON: lines.append(' blank'); names.append('none')
            qc.append('$bodygroup "%s"\n{\n%s\n}'%(g,'\n'.join(lines))); groupsout[g]=names
        if model==BODY_MODEL:
            smd.write(KIT+'modelsrc/%s_phys.smd'%model,VN,VP,NLX,phys_tris([t for t in allt if t[0].endswith(('_body','_skin','_arms'))]))
        for jb,L in JIGGLE.items():
            if any('earring' in str(o) for o in groups.values()):
                qc.append('$jigglebone "%s"\n{\n is_flexible\n {\n  length %.2f\n  tip_mass 0\n  pitch_stiffness 40\n  pitch_damping 3\n  yaw_stiffness 40\n  yaw_damping 3\n  angle_constraint 40\n }\n}'%(jb,max(L,0.5)))
        # flag every Valve bone for bone merging: without this the player only computes the bones IT needs, and the citizen
        # models leave finger bones out of that set -> Token's fingers stayed in bind pose (the stretched-hand bug on male_*)
        usedb={b for _,vs in allt for (_,_,_,lk) in vs for b,_ in lk}
        qc+=['$bonemerge "%s"'%VN[b] for b in sorted(usedb) if b<len(RT.vn) and any(k in VN[b] for k in ('Finger','Hand','Forearm'))]
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
