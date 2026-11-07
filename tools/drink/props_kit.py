"""Token's whiskey props as one bone-merged model: glass rigid to R_Hand, capped bottle rigid to L_Hand.
Hand placement = Cyberpunk's WeaponRight attach point from the clips (bottle: mirrored onto the left hand)."""
import sys,os,json,numpy as np
sys.path[:0]=['/home/claude/work/drink','/home/claude/work/token','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
from PIL import Image
import token_kit as K, retarget as RT, smd, garments, mats, mesh, xbm, dseq
OUT='/mnt/user-data/outputs/token_build/'; MD='models/player/token'
def tex(p):
    try: return xbm.load(garments.segs_of(p)).convert('RGBA')
    except Exception: return None
PROPS={'glass':('base\\environment\\decoration\\dining_accessories\\tableware\\glass\\glass_f_whiskey.mesh','Right'),
       'bottle':('base\\environment\\decoration\\food\\drinks\\drink_bottle\\drink_bottle_m_whiskey.mesh','Left')}
VMT={
 'glass':' "$translucent" "1"\n "$nocull" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.35 .35 .35]"\n "$phong" "1"\n "$phongexponent" "120"\n "$phongboost" "4"\n',
 'whiskey':' "$translucent" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.2 .15 .1]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "2"\n',
 'cap':' "$envmap" "env_cubemap"\n "$envmaptint" "[.5 .45 .35]"\n "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "3"\n "$phongalbedotint" "1"\n',
}
def solid(rgba,size=64): return Image.new('RGBA',(size,size),rgba)
def build():
    T={}; mats_out={}
    for key,(path,side) in PROPS.items():
        s=garments.segs_of(path); m=mesh.decode(s); b,r,mm,apps=mats.mesh_info(s); cm=apps['default']
        X=RT.D[side+'Hand']@RT.CW[side+'Hand']@RT.tov(dseq.prop_rel(side))      # prop frame in Token's bind space (inches)
        hb=RT.vn.index('ValveBiped.Bip01_%s_Hand'%side[0])
        for x in m['subs']:
            mn=cm[x['chunk']] if x['chunk']<len(cm) else cm[0]
            if 'spice' in mn or 'decal' in mn: continue
            refs=mats.material_refs(s,mn)[0]
            if 'fluid' in mn or (key=='bottle' and mn=='interior'): name,kind,im='token_%s_whiskey'%key,'whiskey',solid((120,52,10,215))
            elif key=='glass': name,kind,im='token_glass_glass','glass',solid((200,210,208,60))
            elif mn=='exterior_def':
                d=next((tex(t) for t in refs if t.endswith('_d.xbm')),None)
                if d is not None: d=d.resize((512,1024) if d.size[1]>d.size[0] else (512,512)); a=np.asarray(d).copy(); a[...,3]=np.maximum(a[...,3],70); d=Image.fromarray(a)
                name,kind,im='token_bottle_glass','glass',d if d is not None else solid((200,210,208,60))
            else: name,kind,im='token_bottle_cap','cap',solid((150,135,105,255))
            mats_out[name]=(kind,im)
            P=np.asarray(x['pos'],float); P=(RT.C@P.T).T*RT.S; P=(X[:3,:3]@P.T).T+X[:3,3]
            Nn=np.asarray(x.get('nrm') if x.get('nrm') is not None else np.tile([0,0,1.0],(len(P),1)),float)[:,:3]; Nn=(RT.C@Nn.T).T; Nn=(X[:3,:3]@Nn.T).T
            Nn/=np.maximum(np.linalg.norm(Nn,axis=1,keepdims=True),1e-9)
            T.setdefault(key,[]).extend(smd.part_tris(P,Nn,np.asarray(x['uv0']),np.asarray(x['idx']),[[(hb,1.0)]]*len(P),name))
    M='token_drinkware'
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[])
    qc=['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "%s/"'%MD,'$surfaceprop "glass"','$model "%s_bind" "%s_bind.smd"'%(M,M)]
    for key in ('glass','bottle'):
        fn='%s_%s.smd'%(M,key); smd.write(OUT+'modelsrc/'+fn,K.VN,K.VP,K.NLX,T[key]); qc.append('$bodygroup "%s"\n{\n studio "%s"\n blank\n}'%(key,fn))
    qc.append('$sequence "idle" "%s_bind.smd" fps 1'%M)
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(qc)+'\n')
    for name,(kind,im) in mats_out.items():
        w,h=im.size; p2=lambda v:1<<max(2,round(np.log2(v))); im=im.resize((p2(w),p2(h)))
        im.save(OUT+'materialsrc/%s.tga'%name); open(OUT+'materialsrc/%s.txt'%name,'w').write('nocompress 0\n')
        open(OUT+'materials/%s.vmt'%name,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s"\n%s}\n'%(MD,name,VMT[kind]))
    json.dump(dict(model=M,materials=sorted(mats_out),bodygroups={'glass':['glass','none'],'bottle':['bottle','none']},tris=sum(len(v) for v in T.values())),open(OUT+'plans/_drinkware.json','w'),indent=1)
    print(M,{k:len(v) for k,v in T.items()},sorted(mats_out))
if __name__=='__main__': build()
