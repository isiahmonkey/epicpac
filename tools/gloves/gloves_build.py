"""Build the glove test: Judy tuner gloves ('black', Street Kid sticker on the left) on Token's approved hand D.
 token_gloves.mdl        both gloves + the sticker, skinned like the D hand underneath (gloves.fitted)
 token_handsd.mdl        hand D (the whole Cyberpunk base arm) with the skin hidden under the glove removed, so it
                         cannot poke through the glove when the fingers bend
Materials: black multilayer baked (ml.bake), Judy's glove normal + layer detail, decals with alpha, sticker, screen.
python3 gloves_build.py [model] [mats] [check]"""
import sys,os,json,pickle,numpy as np
sys.path[:0]=['/home/claude/work/gloves','/home/claude/work/guitar','/home/claude/work/token','/home/claude/tools/scripts','/home/claude/work/build']
from PIL import Image
import garch,garments
_orig=garments.segs_of
garments.segs_of=lambda p: garch.segs(p) or _orig(p)
import ml, gloves as G, basehand as BH, retarget as RT, smd
from scipy.spatial import cKDTree
OUT='/mnt/user-data/outputs/token_build/'
# material per glove sub-mesh (LOD0 order of the mesh's chunkMaterials for the 'black' appearance)
CHUNK_MAT={0:'glove_black',1:'glove_screen',3:'glove_kng',4:'glove_mlt',5:'glove_mtx'}   # 6 (stc decal): texture not in the game files staged; left out
DEC={'glove_kng':'decals_kangtao','glove_mlt':'decals_militech','glove_mtx':'decals_max_tac'}
D='base\\characters\\common\\textures\\decals\\'
COVER=0.18      # in: skin closer than this to the glove body (and behind it) is hidden
def save(name,im,vmt,normal=False):
    im.save(OUT+'materialsrc/token_%s.tga'%name); open(OUT+'materialsrc/token_%s.txt'%name,'w').write('nocompress 0\n'+('normal 1\n' if normal else ''))
    if vmt is not None: open(OUT+'materials/token_%s.vmt'%name,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n'+vmt.replace('{M}','models/player/token/token_'+name)+'}\n')
def mats():
    o=pickle.load(open('/home/claude/work/gloves/glove_black_bake.pkl','rb'))
    alb=Image.fromarray((np.clip(o['albedo'],0,1)*255).astype(np.uint8)).resize((1024,1024),Image.LANCZOS)
    b=ml.tex('base\\characters\\main_npc\\judy\\textures\\g1_001_wa_glove__judy_n01.xbm')[...,:2]*2-1          # glove shape normal (seams, padding)
    bi=np.stack([np.asarray(Image.fromarray(((b[...,k]*0.5+0.5)*255).astype(np.uint8)).resize((1024,1024),Image.BICUBIC)).astype(np.float32)/255*2-1 for k in (0,1)],-1)
    d=np.stack([np.asarray(Image.fromarray(((np.clip(o['nxy'][...,k],-1,1)*0.5+0.5)*255).astype(np.uint8)).resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255*2-1 for k in (0,1)],-1)
    n=bi+d*0.6; z=np.sqrt(np.clip(1-(n**2).sum(-1),0.05,1)); L=np.sqrt((n**2).sum(-1)+z**2); n/=L[...,None]; z/=L
    rough=np.asarray(Image.fromarray((np.clip(o['rough'],0,1)*255).astype(np.uint8)).resize((1024,1024),Image.LANCZOS)).astype(np.float32)/255
    gloss=np.clip((1-rough)*1.3,0,1)**1.5
    nm=np.dstack([n[...,0]*0.5+0.5,n[...,1]*0.5+0.5,z*0.5+0.5,gloss])
    save('glove_black_n',Image.fromarray((nm*255).astype(np.uint8),'RGBA'),None,normal=True)
    save('glove_black',alb.convert('RGB'),' "$basetexture" "{M}"\n "$bumpmap" "{M}_n"\n "$nocull" "1"\n "$phong" "1"\n "$phongexponent" "16"\n "$phongboost" "1.2"\n "$phongfresnelranges" "[0.3 0.6 1]"\n "$halflambert" "1"\n')
    # the wrist screen: a dim blue-green readout (the game's animated screen texture is not used)
    sc=np.zeros((64,64,3),np.uint8); sc[...]=(18,70,80); sc[8:56:8,6:58]=(60,190,200)
    save('glove_screen',Image.fromarray(sc),' "$basetexture" "{M}"\n "$selfillum" "1"\n "$selfillumtint" "[1.4 1.4 1.4]"\n')
    for nm_,f in DEC.items():
        t=ml.tex(D+f+'_d01.xbm'); im=Image.fromarray((np.clip(t,0,1)*255).astype(np.uint8),'RGBA').resize((512,512),Image.LANCZOS)
        save(nm_,im,' "$basetexture" "{M}"\n "$alphatest" "1"\n "$alphatestreference" "0.45"\n "$allowalphatocoverage" "1"\n "$halflambert" "1"\n')
    t=ml.tex('base\\tq\\textures\\streetkid_d.xbm'); im=Image.fromarray((np.clip(t,0,1)*255).astype(np.uint8),'RGBA').resize((1024,1024),Image.LANCZOS)
    save('glove_sticker',im,' "$basetexture" "{M}"\n "$alphatest" "1"\n "$alphatestreference" "0.45"\n "$allowalphatocoverage" "1"\n "$halflambert" "1"\n "$phong" "1"\n "$phongexponent" "30"\n "$phongboost" "0.8"\n "$phongfresnelranges" "[0.3 0.6 1]"\n')
    print('materials written; missing:',sorted(ml.MISSING))
def _tris(parts,matof):
    T=[]
    for p in parts:
        m=matof(p)
        if m is None: continue
        Fi=p['idx'].copy(); a,b,c=p['pos'][Fi[:,0]],p['pos'][Fi[:,1]],p['pos'][Fi[:,2]]
        bad=(np.cross(b-a,c-a)*p['nrm'][Fi].sum(1)).sum(1)<0; Fi[bad]=Fi[bad][:,[0,2,1]]
        T+=smd.part_tris(p['pos'],p['nrm'],p['uv'],Fi.ravel(),p['lk'],'token_'+m,flip=False)
    return T
def covered_faces(hp,hn,gp,gn,F):
    """hand triangles whose 3 corners all sit under the glove body: within COVER of it and on the inside of its surface"""
    t=cKDTree(gp); d,i=t.query(hp); inside=((hp-gp[i])*gn[i]).sum(1)<0.02
    cov=(d<COVER)&inside
    return cov[F].all(1)
def glove_parts():
    out={}
    for s in 'lr':
        g=[p for p in G.glove(s) if p['chunk'] in CHUNK_MAT]
        for p in g: p['mat']=CHUNK_MAT[p['chunk']]
        if s==G.STICKER_SIDE:
            for p in G.sticker(s): p['mat']='glove_sticker'; g.append(p)
        out[s]=g
    return out
def write(M,T,mats_):
    import token_kit as K
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[]); smd.write(OUT+'modelsrc/%s_body.smd'%M,K.VN,K.VP,K.NLX,T)
    used=sorted({b for _,vs in T for v in vs for b,_ in v[3]})
    qc=['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "models/player/token/"','$surfaceprop "flesh"','$model "%s_bind" "%s_bind.smd"'%(M,M),
        '$bodygroup "main"\n{\n studio "%s_body.smd"\n}'%M,'$sequence "idle" "%s_bind.smd" fps 1'%M]+['$bonemerge "%s"'%RT.vn[b] for b in used]
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(qc)+'\n')
    json.dump(dict(model=M,materials=sorted(mats_),bodygroups={'main':['main']},tris=len(T)),open(OUT+'plans/_%s.json'%M,'w'),indent=1)
    print(M,len(T),'tris, bones',len(used))
def models():
    GP=glove_parts(); TG=[]; TH=[]; hidden=0
    for s in 'lr':
        TG+=_tris(GP[s],lambda p:p['mat'])
        body=[p for p in GP[s] if p['mat']=='glove_black']
        gp=np.vstack([p['pos'] for p in body]); gn=np.vstack([p['nrm'] for p in body])
        H=G.hand_D(s)
        for p in H:
            cf=covered_faces(p['pos'],p['nrm'],gp,gn,p['idx']); hidden+=int(cf.sum()); p['idx']=p['idx'][~cf]
        TH+=_tris(H,lambda p:'arms')
    print('hand triangles hidden under the gloves:',hidden)
    write('token_gloves',TG,{t[0] for t in TG}); write('token_handsd',TH,{'token_arms'})
if __name__=='__main__':
    if 'mats' in sys.argv: mats()
    if 'model' in sys.argv: models()
    if 'check' in sys.argv:
        import fingertest as FT
        print({s:G.check([FT.pose_bind(t) for t in np.arange(0,11,0.5)],s) for s in 'lr'})
