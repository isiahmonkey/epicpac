"""Token's guitar (outfit 2): Cyberpunk electric_guitar_a with the body paint (ml layer 0, the anodised base coat) recoloured black, hung rigid on the
chest (Spine4) where CP's guitar clips carry it, plus a procedural black leather strap over the left shoulder.
Writes token_guitar.qc/.smd + materials into token_build."""
import sys,os,json,pickle,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/token','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
from PIL import Image,ImageFilter
import token_kit as K, retarget as RT, smd, cr2w, mesh, ml, gseq
OUT='/mnt/user-data/outputs/token_build/'; MD='models/player/token'
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~'
GM=mesh.decode(cr2w.load_loose(F+'environment~decoration~misc~music~electric_guitar~electric_guitar_a.mesh'))['subs'][0]   # sub 1 = back decal, skipped
GP=np.asarray(GM['pos'],float)+np.array([gseq.OFFSET_X,0,0])   # see gseq.OFFSET_X: the clip's neck sat this much higher off the hand
VCH=RT.vn.index('ValveBiped.Bip01_Spine4')
def to_bind(P,Nn=None):
    """guitar item space (m) -> Token bind (Valve inches)"""
    X=gseq.G_BIND; P=(RT.C@np.asarray(P,float).T).T*RT.S; P=(X[:3,:3]@P.T).T+X[:3,3]
    if Nn is None: return P
    Nn=(RT.C@np.asarray(Nn,float)[:,:3].T).T; Nn=(X[:3,:3]@Nn.T).T; return P,Nn/np.maximum(np.linalg.norm(Nn,axis=1,keepdims=True),1e-9)
END_PIN=np.array([gseq.OFFSET_X,0.017,0.0])                                   # tail of the body (item space)
_h=GP[GP[:,1]<-0.06]; HORN=_h[np.argmax(_h[:,2])]*np.array([0,1,1])+np.array([gseq.OFFSET_X-0.002,0.006,-0.008])   # tip of the long (bass-side) horn
def textures():
    D='base\\environment\\decoration\\misc\\music\\electric_guitar\\textures\\'
    cache='/home/claude/work/guitar/bake_black.pkl'
    if os.path.exists(cache): o=pickle.load(open(cache,'rb'))
    else:
        ml.COLOR_OVERRIDE.clear(); ml.COLOR_OVERRIDE.update({k:(0.010,0.010,0.011) for k in (0,4,9,14)})   # 0 anodised base coat, 4 blue trim, 9 foil graphic, 14 red/tan plastic panels
        o=ml.bake(D+'ml_electric_guitar.mlsetup',D+'ml_electric_guitar_masksset.mlmask',R=2048); pickle.dump(o,open(cache,'wb'))
    alb=Image.fromarray((np.clip(o['albedo'],0,1)*255).astype(np.uint8)).resize((1024,1024),Image.LANCZOS)
    n=np.clip(o['nxy'],-1,1); z=np.sqrt(np.clip(1-(n**2).sum(-1),0,1))
    gloss=(1-np.clip(o['rough'],0,1))*(0.35+0.65*np.clip(o['metal'],0,1))           # envmap mask: glossy paint / chrome
    nm=np.dstack([(n[...,0]*0.5+0.5),(n[...,1]*0.5+0.5),z*0.5+0.5,gloss])
    nim=Image.fromarray((nm*255).astype(np.uint8),'RGBA').resize((1024,1024),Image.LANCZOS)
    return alb,nim
def mat(name,im,vmt,normal=False):
    im.save(OUT+'materialsrc/%s.tga'%name); open(OUT+'materialsrc/%s.txt'%name,'w').write('nocompress 0\n'+('normal 1\n' if normal else ''))
    if vmt: open(OUT+'materials/%s.vmt'%name,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s"\n%s}\n'%(MD,name,vmt))
GUITAR_VMT=(' "$bumpmap" "%s/token_guitar_n"\n "$normalmapalphaenvmapmask" "1"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.18 .18 .19]"\n'
            ' "$envmapfresnel" "1"\n "$phong" "1"\n "$phongexponent" "48"\n "$phongboost" "2.2"\n "$phongfresnelranges" "[0.25 0.6 1]"\n "$halflambert" "1"\n')%MD
STRAP_VMT=' "$bumpmap" "%s/token_guitar_strap_n"\n "$phong" "1"\n "$phongexponent" "16"\n "$phongboost" "0.5"\n "$phongfresnelranges" "[0.3 0.6 1]"\n "$nocull" "1"\n'%MD
def strap_tex():
    """black leather: grain noise + a stitched edge each side (u across the strap, v along it)"""
    rng=np.random.default_rng(7); W,H=128,1024
    g=rng.normal(0,1,(H//4,W//4)); g=np.asarray(Image.fromarray(((g*0.5+0.5).clip(0,1)*255).astype(np.uint8)).resize((W,H),Image.BICUBIC),float)/255
    fine=rng.normal(0,1,(H,W))*0.04
    base=0.055+0.025*g+fine
    u=np.linspace(0,1,W)[None,:]; v=np.arange(H)[:,None]
    edge=((np.abs(u-0.09)<0.012)|(np.abs(u-0.91)<0.012))&((v%14)<9)
    col=np.dstack([base,base*0.97,base*0.95]); col[np.broadcast_to(edge,(H,W))]=[0.20,0.19,0.18]
    alb=Image.fromarray((np.clip(col,0,1)**(1/2.2)*255).astype(np.uint8))
    h=g*0.6+fine*3+edge*0.8; gy,gx=np.gradient(h); nn=np.dstack([-gx*2,-gy*2,np.ones_like(h)]); nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
    nim=Image.fromarray(((nn*0.5+0.5)*255).astype(np.uint8))
    return alb,nim
# ------------------------------------------------------------------ strap path (Token bind, inches)
def body_cloud():
    pts=[]
    for f in ('token_outfit2_torso_outer_long_fur_coat.smd','token_base_skin_torso.smd','token_base_skin_collar.smd','token_base_neck_cyberware_takemura_black_red.smd'):
        T=open(OUT+'modelsrc/'+f).read().split('triangles\n')[1].split('\n')
        for i in range(0,len(T)-3,4):
            if T[i].strip()=='end': break
            for k in (1,2,3): pts.append(list(map(float,T[i+k].split()[1:4])))
    return np.unique(np.round(np.array(pts),2),axis=0)
def wrap(guides,anchors,cloud,clear=0.45,rad=0.9):
    """push each guide point out along (anchor -> guide) to just outside the body/coat surface"""
    out=[]
    for g,a in zip(guides,anchors):
        d=g-a; d/=np.linalg.norm(d); rel=cloud-a; t=rel@d; perp=np.linalg.norm(rel-np.outer(t,d),axis=1)
        m=(perp<rad)&(t>0); r=t[m].max() if m.any() else np.linalg.norm(g-a)
        out.append(a+d*(r+clear))
    return np.array(out)
def smooth(P,k=3,it=3,keep_ends=True):
    P=P.copy()
    for _ in range(it):
        Q=P.copy()
        for i in range(1,len(P)-1): Q[i]=P[max(0,i-k):i+k+1].mean(0)
        P=Q
    return P
def strap_path():
    V=lambda n: RT.NW[RT.vn.index('ValveBiped.Bip01_'+n)][:3,3]
    horn=to_bind([HORN])[0]; pin=to_bind([END_PIN])[0]
    sp4=V('Spine4'); sp2=V('Spine2'); pel=V('Pelvis'); lcl=V('L_Clavicle'); lua=V('L_UpperArm'); neck=V('Neck1')
    up=np.array([0,0,1.0]); fwd=np.array([1.0,0,0])
    shoulder=lcl*0.45+lua*0.55                     # strap rides between the neck and the shoulder joint
    # guide polyline: horn -> up the chest -> over the left shoulder -> diagonally down the back -> right hip -> end pin
    G=[horn+fwd*1.0, (horn*0.55+shoulder*0.45)+fwd*6, shoulder+fwd*4+up*1.5, shoulder+up*4, shoulder-fwd*4+up*1.5,
       sp4-fwd*8+np.array([0,1.0,0]), sp2-fwd*8+np.array([0,-2.5,0]), pel*0.5+sp2*0.5-fwd*7+np.array([0,-6.5,0]),
       pin+np.array([-3,-3.5,0]), pin]
    G=np.array(G); P=[]
    for a,b in zip(G,G[1:]):
        n=max(2,int(np.linalg.norm(b-a)/0.8))
        P+= [a+(b-a)*u for u in np.linspace(0,1,n,endpoint=False)]
    P=np.array(P+[G[-1]]); P=smooth(P,k=2,it=4)
    # anchors: nearest point on the inner bone line (pelvis - spine - chest - clavicle - shoulder)
    line=np.array([pel,sp2,sp4,lcl,shoulder])
    def near(p):
        best=None
        for a,b in zip(line,line[1:]):
            u=np.clip((p-a)@(b-a)/((b-a)@(b-a)),0,1); q=a+(b-a)*u
            if best is None or np.linalg.norm(p-q)<np.linalg.norm(p-best): best=q
        return best
    cloud=body_cloud(); A=np.array([near(p) for p in P])
    W=wrap(P,A,cloud); W=smooth(W,k=2,it=3)
    W=wrap(W,A,cloud); W=smooth(W,k=1,it=2)
    # the ends meet the guitar's buttons
    n=len(W); f=np.clip(np.r_[np.linspace(1,0,6),np.zeros(n-12),np.linspace(0,1,6)],0,1)[:,None]
    ends=np.where(np.arange(n)[:,None]<n/2,horn,pin); W=W*(1-f)+ends*f
    return W,cloud
def strap_mesh(path,width=2.0,thick=0.12):
    """flat band along the path; its face normal points away from the body (anchor side)"""
    V=lambda n: RT.NW[RT.vn.index('ValveBiped.Bip01_'+n)][:3,3]
    c=(V('Spine2')+V('Spine4'))/2
    T=np.gradient(path,axis=0); T/=np.linalg.norm(T,axis=1,keepdims=True)
    out_=path-c; out_-= (out_*T).sum(1)[:,None]*T; out_/=np.linalg.norm(out_,axis=1,keepdims=True)
    B=np.cross(T,out_); B/=np.linalg.norm(B,axis=1,keepdims=True)
    L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
    verts=[];norms=[];uvs=[];idx=[]
    for side,(off,nrm) in enumerate(((thick/2,1),(-thick/2,-1))):
        b0=len(verts)
        for i,p in enumerate(path):
            for s in (-1,1):
                verts.append(p+B[i]*s*width/2+out_[i]*off); norms.append(out_[i]*nrm); uvs.append(((s+1)/2,L[i]/(width*8)))
        for i in range(len(path)-1):
            a=b0+2*i; q=[a,a+2,a+1,a+1,a+2,a+3] if nrm>0 else [a,a+1,a+2,a+1,a+3,a+2]; idx+=q
    return np.array(verts),np.array(norms),np.array(uvs),np.array(idx)
def build():
    alb,nim=textures()
    mat('token_guitar',alb,GUITAR_VMT); mat('token_guitar_n',nim,None,normal=True)
    sa,sn=strap_tex(); mat('token_guitar_strap',sa,STRAP_VMT); mat('token_guitar_strap_n',sn,None,normal=True)
    Pv,Nv=to_bind(GP,np.asarray(GM.get('nrm'),float))
    tris=smd.part_tris(Pv,Nv,np.asarray(GM['uv0']),np.asarray(GM['idx']),[[(VCH,1.0)]]*len(Pv),'token_guitar')
    path,_=strap_path(); sv,sn_,su,si=strap_mesh(path)
    tris+=smd.part_tris(sv,sn_,su,si,[[(VCH,1.0)]]*len(sv),'token_guitar_strap')
    M='token_guitar'
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[]); smd.write(OUT+'modelsrc/%s_body.smd'%M,K.VN,K.VP,K.NLX,tris)
    qc=['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "%s/"'%MD,'$surfaceprop "wood"','$model "%s_bind" "%s_bind.smd"'%(M,M),
        '$bodygroup "prop"\n{\n studio "%s_body.smd"\n}'%M,'$sequence "idle" "%s_bind.smd" fps 1'%M]
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(qc)+'\n')
    json.dump(dict(model=M,materials=['token_guitar','token_guitar_strap'],bodygroups={'prop':['prop']},tris=len(tris)),open(OUT+'plans/_%s.json'%M,'w'),indent=1)
    print(M,len(tris),'tris; strap points',len(path))
if __name__=='__main__': build()
