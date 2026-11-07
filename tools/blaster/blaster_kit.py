"""Blade Runner Blaster (Dark) -> one Gmod model, bone-merged and rigid to the RIGHT hand.
Geometry + the mod's own blaster2 texture set; placement = Cyberpunk's handgun grip (WeaponRight vs RightHand)."""
import sys,os,json,numpy as np
sys.path[:0]=['/home/claude/work/blaster','/home/claude/work/token','/home/claude/work/pbr','/home/claude/tools/scripts','/home/claude/work/build']
from PIL import Image
import token_kit as K, retarget as RT, smd, rdar, mesh, mats, glb, grip
OUT='/mnt/user-data/outputs/token_build/'; MD='models/player/token'; M='br_blaster'
A=rdar.Archive('/home/claude/work/blaster/Blade_Runner_Gun_Dark.archive'); H={f['hash']:f for f in A.files}
BASE,RCV,RAIL=3802723034671675061,14837818261743555129,10775891820166327166
BULLETS=[15541377673161951581,3616464470009010218,13294036167860481251,248087951782834264,17529584711185602889]
CYL=np.array([0.0,0.07,0.011])
TEX='/home/claude/work/blaster/tex_%s.png'
# chunk -> material kind
KIND={(BASE,0):'body',(BASE,1):'glass',(BASE,2):'body',(BASE,3):'body',(BASE,4):'glow',(RCV,0):'body',(RCV,1):'body',(RCV,2):'sights',(RAIL,0):'rail'}
def parts():
    out=[]
    for h in (BASE,RCV,RAIL)+tuple(BULLETS):
        g=mesh.decode(A.extract(H[h]))
        for s in g['subs']:
            if s['chunk']>0 and h==RAIL: continue           # tpp duplicate of the rail
            P=np.asarray(s['pos'],float); Nn=np.asarray(s['nrm'],float)[:,:3]
            if h in BULLETS: P=P+CYL
            k='bullet' if h in BULLETS else KIND.get((h,s['chunk']),'body')
            out.append((k,P,Nn,np.asarray(s['uv0'],float),np.asarray(s['idx'])))
    return out
def build(preview=None):
    X=RT.D['RightHand']@RT.CW['RightHand']@RT.tov(grip.grip()); hb=RT.vn.index('ValveBiped.Bip01_R_Hand')
    T=[]; used=set()
    for k,P,Nn,uv,idx in parts():
        Pv=(RT.C@P.T).T*RT.S; Pv=(X[:3,:3]@Pv.T).T+X[:3,3]; Nv=(X[:3,:3]@(RT.C@Nn.T)).T; Nv/=np.maximum(np.linalg.norm(Nv,axis=1,keepdims=True),1e-9)
        mn='br_blaster_'+k; used.add(mn)
        F=np.asarray(idx).reshape(-1,3).copy(); a,b,c=Pv[F[:,0]],Pv[F[:,1]],Pv[F[:,2]]
        bad=(np.cross(b-a,c-a)*Nv[F].sum(1)).sum(1)<0; F[bad]=F[bad][:,[0,2,1]]     # each triangle faces where its normals point (Source culls back faces)
        T+=smd.part_tris(Pv,Nv,uv,F.ravel(),[[(hb,1.0)]]*len(Pv),mn)
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[]); smd.write(OUT+'modelsrc/%s_body.smd'%M,K.VN,K.VP,K.NLX,T)
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "%s/"'%MD,'$surfaceprop "metal"',
        '$model "%s_bind" "%s_bind.smd"'%(M,M),'$bodygroup "gun"\n{\n studio "%s_body.smd"\n}'%M,'$sequence "idle" "%s_bind.smd" fps 1'%M])+'\n')
    # ---- textures / materials
    d=Image.open(TEX%'d').convert('RGB'); r=np.asarray(Image.open(TEX%'r').convert('L')).astype(np.float32)/255
    n=glb.cp_normal(Image.open(TEX%'n')).convert('RGBA'); n.putalpha(Image.fromarray((np.clip((1-r)*1.25,0,1)**1.4*255).astype(np.uint8)))   # gloss in the normal alpha = phong / envmap mask
    e=Image.open(TEX%'e').convert('RGB').resize(d.size)
    bd=Image.open(TEX%'bd').convert('RGB'); bn=glb.cp_normal(Image.open(TEX%'bn')).convert('RGBA'); br=np.asarray(Image.open(TEX%'br').convert('L')).astype(np.float32)/255
    bn.putalpha(Image.fromarray((np.clip((1-br)*1.25,0,1)**1.4*255).astype(np.uint8)))
    def save(name,im,normal=False):
        im.save(OUT+'materialsrc/%s.tga'%name); open(OUT+'materialsrc/%s.txt'%name,'w').write('nocompress 0\n'+('normal 1\n' if normal else ''))
    save('br_blaster_d',d); save('br_blaster_n',n,True); save('br_blaster_e',e); save('br_blaster_bullet_d',bd); save('br_blaster_bullet_n',bn,True)
    METAL=' "$bumpmap" "{D}/{N}"\n "$phong" "1"\n "$phongexponent" "40"\n "$phongboost" "3"\n "$phongfresnelranges" "[0.4 0.7 1]"\n "$envmap" "env_cubemap"\n "$normalmapalphaenvmapmask" "1"\n "$envmaptint" "[.3 .3 .32]"\n "$envmapcontrast" "1"\n'
    VMT={'body':('br_blaster_d',METAL.replace('{N}','br_blaster_n')),
         'glow':('br_blaster_d',METAL.replace('{N}','br_blaster_n')+' "$selfillum" "1"\n "$selfillummask" "{D}/br_blaster_e"\n'),
         'sights':('br_blaster_e',' "$selfillum" "1"\n "$additive" "1"\n "$nocull" "1"\n'),
         'glass':('br_blaster_d',' "$translucent" "1"\n "$alpha" "0.55"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.4 .4 .45]"\n "$phong" "1"\n "$phongexponent" "100"\n "$phongboost" "4"\n'),
         'rail':('br_blaster_rail',' "$bumpmap" "{D}/br_blaster_rail_n"\n "$phong" "1"\n "$phongexponent" "40"\n "$phongboost" "3"\n "$phongfresnelranges" "[0.4 0.7 1]"\n "$envmap" "env_cubemap"\n "$normalmapalphaenvmapmask" "1"\n "$envmaptint" "[.3 .3 .32]"\n'),
         'bullet':('br_blaster_bullet_d',METAL.replace('{N}','br_blaster_bullet_n'))}
    for k,(base,body) in VMT.items():
        open(OUT+'materials/br_blaster_%s.vmt'%k,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s"\n%s}\n'%(MD,base,body.replace('{D}',MD)))
    if not os.path.exists(OUT+'materialsrc/br_blaster_rail.tga'):     # until the vanilla rail material arrives: the body's dark steel
        save('br_blaster_rail',Image.new('RGB',(64,64),(40,40,42))); save('br_blaster_rail_n',Image.new('RGBA',(64,64),(128,128,255,150)),True)
    mats_=sorted({'br_blaster_%s'%k for k in VMT}|{'br_blaster_d','br_blaster_n','br_blaster_e','br_blaster_bullet_d','br_blaster_bullet_n','br_blaster_rail','br_blaster_rail_n'})
    json.dump(dict(model=M,materials=mats_,bodygroups={'gun':['gun']},tris=len(T)),open(OUT+'plans/_%s.json'%M,'w'),indent=1)
    print(M,'tris',len(T),sorted(used))
if __name__=='__main__': build()
