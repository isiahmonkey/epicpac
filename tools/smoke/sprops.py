"""Token's smoking props as small bone-merged models (each one its own model so PAC can show/hide it on cue):
 token_sm_glass      whisky glass, rigid to R_Hand (same grip as the whiskey idle)
 token_sm_cig        cigarette in the LEFT hand, resting grip (cigarette clip's idle, mirrored)
 token_sm_cig_smoke  cigarette in the LEFT hand, smoking grip (filter turned to the lips; CP rotates the item ~70 deg)
 token_sm_cig_mouth  cigarette resting in the lips, rigid to Head1
 token_sm_zippo / token_sm_zippo_open   Zippo in the LEFT hand (npc1's lighter grip from smoke_together)
Also writes anchors.json: tip / flame / mouth points in PAC bone-local inches for the particle, sprite and light parts."""
import sys,os,json,math,numpy as np
sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/token','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
from PIL import Image
import token_kit as K, retarget as RT, smd, garments, mats, mesh, xbm, cr2w, xf, sseq, dseq
OUT='/mnt/user-data/outputs/token_build/'; MD='models/player/token'
I=sseq.I; Rm=sseq.Rm
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~'
def avg(Ms):
    R=sum(m[:3,:3] for m in Ms); U,_,Vt=np.linalg.svd(R); M=np.eye(4); M[:3,:3]=U@Vt; M[:3,3]=np.mean([m[:3,3] for m in Ms],0); return M
def mrel(c,ts,hand='LeftHand',item='WeaponRight'):
    """item frame relative to the (mirrored) left hand, averaged over ts"""
    out=[]
    for t in ts:
        W=c.world(t); Wm=sseq.mirror_world(W); out.append(np.linalg.inv(Wm[I[hand]])@(Rm@W[I[item]]@Rm))
    return avg(out)
SM={nm:sseq.CIG[nm] for nm in sseq.CIG}
GRIP_IDLE=mrel(sseq.IDLE,np.linspace(0,sseq.IDLE.dur,10,endpoint=False))
GRIP_SMOKE=mrel(SM['stand__rh_cigarette__01__smoke__02'],np.linspace(1.4,2.9,8))
def zippo_rel():
    c=sseq.S.LIGHT; out=[]
    for t in np.arange(3.6,4.6,0.1):
        W=c.world(t); out.append(np.linalg.inv(W[I['LeftHand']])@W[I['WeaponLeft']])
    return avg(out)
GRIP_ZIPPO=zippo_rel()
# cigarette mesh (item space, m): filter at y-min, lit end at y-max
CIGSUB=mesh.decode(cr2w.load_loose(F+'items~interactive~recreation~int_recreation_001__cigarette_i_stick~int_recreation_001__cigarette_i_stick.mesh'))['subs'][0]
CP_=np.asarray(CIGSUB['pos'],float); FILTER=np.array([0,CP_[:,1].min(),0]); TIP=np.array([0,CP_[:,1].max(),0])
def mouth_rest():
    """resting cigarette: smoking-grip pose at the lips (smoke__02 contact), drooped 18 deg about the filter"""
    W=SM['stand__rh_cigarette__01__smoke__02'].world(sseq.TC); Wm=sseq.mirror_world(W)
    M=np.linalg.inv(Wm[I['Head']])@Wm[I['LeftHand']]@GRIP_SMOKE
    # droop: rotate about the head's lateral axis (z in the CP head frame) through the filter point
    f=(M@np.r_[FILTER,1])[:3]; a=math.radians(-18); R=xf.T(np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]]),np.zeros(3))
    Tm=xf.T(np.eye(3),f)@R@xf.T(np.eye(3),-f)
    LIP=np.array([0.0045,0.0095,0.0060])   # Token's lips sit ~1 cm higher / nearer the centre than CP's man_base (seen in the render)
    return xf.T(np.eye(3),LIP)@Tm@M
GRIP_MOUTH=mouth_rest()
sseq.CIG_MOUTH=GRIP_MOUTH; sseq.CIG_TIP=TIP; sseq.ZIPPO=GRIP_ZIPPO; sseq.GRIP_SMOKE=GRIP_SMOKE; sseq.FILTER=FILTER
# ---------------- Zippo geometry (procedural, item space m; same build as Emmerich's)
class G:
    def __init__(s): s.v=[];s.n=[];s.uv=[];s.i=[]
    def quad(s,p0,p1,p2,p3,uv):
        n=np.cross(np.subtract(p1,p0),np.subtract(p3,p0)); n=n/(np.linalg.norm(n)+1e-12); b=len(s.v); u0,v0,u1,v1=uv
        s.v+=[p0,p1,p2,p3]; s.n+=[n]*4; s.uv+=[(u0,v1),(u1,v1),(u1,v0),(u0,v0)]; s.i+=[b,b+1,b+2,b,b+2,b+3]
    def box(s,c,size,uv,R=np.eye(3),pivot=None):
        hx,hy,hz=np.array(size)/2; c=np.array(c,float); pv=c if pivot is None else np.array(pivot,float)
        P=lambda x,y,z:(R@(c+np.array([x,y,z])-pv))+pv
        for q in ([P(-hx,hy,-hz),P(hx,hy,-hz),P(hx,hy,hz),P(-hx,hy,hz)],[P(hx,-hy,-hz),P(-hx,-hy,-hz),P(-hx,-hy,hz),P(hx,-hy,hz)],
                  [P(hx,hy,-hz),P(hx,-hy,-hz),P(hx,-hy,hz),P(hx,hy,hz)],[P(-hx,-hy,-hz),P(-hx,hy,-hz),P(-hx,hy,hz),P(-hx,-hy,hz)],
                  [P(-hx,hy,hz),P(hx,hy,hz),P(hx,-hy,hz),P(-hx,-hy,hz)],[P(-hx,-hy,-hz),P(hx,-hy,-hz),P(hx,hy,-hz),P(-hx,hy,-hz)]): s.quad(*q,uv)
    def cyl(s,c0,c1,r,uv,seg=8):
        c0=np.array(c0,float); c1=np.array(c1,float); ax=(c1-c0)/np.linalg.norm(c1-c0); t=np.cross(ax,[1,0,0]); t/=np.linalg.norm(t); bt=np.cross(ax,t)
        for k in range(seg):
            a0=2*np.pi*k/seg; a1=2*np.pi*(k+1)/seg; d0=t*np.cos(a0)+bt*np.sin(a0); d1=t*np.cos(a1)+bt*np.sin(a1); b=len(s.v)
            s.v+=[c0+d0*r,c0+d1*r,c1+d1*r,c1+d0*r]; s.n+=[d0,d1,d1,d0]; s.uv+=[uv[:2]]*4; s.i+=[b,b+1,b+2,b,b+2,b+3]
    def arr(s): return np.array(s.v,float),np.array(s.n,float),np.array(s.uv,float),np.array(s.i)
WZ,DZ,HB,HL,ZB=0.038,0.013,0.039,0.016,-0.0275
FLAME=np.array([-0.003,0,ZB+HB+0.016])
sseq.FLAME=FLAME
def zippo(state):
    g=G(); full=(0,0,1,1); g.box((0,0,ZB+HB/2),(WZ,DZ,HB),full)
    if state=='closed': g.box((0,0,ZB+HB+HL/2),(WZ,DZ,HL),full)
    else:
        a=math.radians(-130); Rh=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
        g.box((0,0,ZB+HB+HL/2),(WZ,DZ,HL),full,R=Rh,pivot=(WZ/2,0,ZB+HB))
        g.box((-0.003,0,ZB+HB+0.007),(0.019,0.011,0.014),(0,0,0.15,0.15))
        g.cyl((-0.003,0,ZB+HB+0.009),(-0.003,0,ZB+HB+0.0135),0.0016,(0.9,0.9,1,1),6)
    return g.arr()
# ---------------- placement into Token's bind (Valve inches)
def frame(bone,rel):
    return RT.D[bone]@RT.CW[bone]@RT.tov(rel)
def bake(P,Nn,X):
    P=(RT.C@P.T).T*RT.S; P=(X[:3,:3]@P.T).T+X[:3,3]
    Nn=(RT.C@Nn.T).T; Nn=(X[:3,:3]@Nn.T).T; Nn/=np.maximum(np.linalg.norm(Nn,axis=1,keepdims=True),1e-9); return P,Nn
VB={'LeftHand':'ValveBiped.Bip01_L_Hand','RightHand':'ValveBiped.Bip01_R_Hand','Head':'ValveBiped.Bip01_Head1'}
def model(M,parts):
    """parts: list of (P,N,UV,idx,material,cp_bone,rel)"""
    T=[]
    for P,Nn,uv,idx,mat,bone,rel in parts:
        X=frame(bone,rel); Pv,Nv=bake(np.asarray(P,float),np.asarray(Nn,float)[:,:3],X); b=RT.vn.index(VB[bone])
        T+=smd.part_tris(Pv,Nv,np.asarray(uv),np.asarray(idx),[[(b,1.0)]]*len(Pv),mat)
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[]); smd.write(OUT+'modelsrc/%s_body.smd'%M,K.VN,K.VP,K.NLX,T)
    qc=['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "%s/"'%MD,'$surfaceprop "plastic"','$model "%s_bind" "%s_bind.smd"'%(M,M),
        '$bodygroup "prop"\n{\n studio "%s_body.smd"\n}'%M,'$sequence "idle" "%s_bind.smd" fps 1'%M]
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(qc)+'\n')
    mats_=sorted({p[4] for p in parts}); json.dump(dict(model=M,materials=mats_,bodygroups={'prop':['prop']},tris=len(T)),open(OUT+'plans/_%s.json'%M,'w'),indent=1)
    return len(T)
def mat(name,im,vmt):
    w,h=im.size; p2=lambda v:1<<max(2,round(np.log2(v))); im=im.resize((p2(w),p2(h)))
    im.save(OUT+'materialsrc/%s.tga'%name); open(OUT+'materialsrc/%s.txt'%name,'w').write('nocompress 0\n'+('normal 1\n' if name.endswith('_n') else ''))
    if vmt: open(OUT+'materials/%s.vmt'%name,'w',newline='\r\n').write('"VertexLitGeneric"\n{\n "$basetexture" "%s/%s"\n%s}\n'%(MD,name,vmt))
def build():
    # cigarette
    atlas=xbm.load(garments.segs_of('base\\environment\\decoration\\recreation\\smoking\\textures\\cigarette_01_d.xbm')).convert('RGB').resize((512,512))
    mat('token_sm_cig',atlas,' "$halflambert" "1"\n')
    cig=(CP_,np.asarray(CIGSUB.get('nrm',np.tile([0,0,1.0],(len(CP_),1))),float)[:,:3],CIGSUB['uv0'],CIGSUB['idx'],'token_sm_cig')
    n={}
    n['token_sm_cig']=model('token_sm_cig',[cig+('LeftHand',GRIP_IDLE)])
    n['token_sm_cig_smoke']=model('token_sm_cig_smoke',[cig+('LeftHand',GRIP_SMOKE)])
    n['token_sm_cig_mouth']=model('token_sm_cig_mouth',[cig+('Head',GRIP_MOUTH)])
    # Zippo
    met=xbm.load(garments.segs_of('base\\surfaces\\materials\\metal\\metal_generic\\metal_generic_bare_01_300_d.xbm')).convert('RGB').resize((256,256))
    met=Image.fromarray(np.clip(np.asarray(met).astype(np.float32)*0.35+150,0,255).astype(np.uint8))
    mat('token_sm_zippo',met,' "$phong" "1"\n "$phongexponent" "60"\n "$phongboost" "4"\n "$phongfresnelranges" "[0.6 0.85 1]"\n "$envmap" "env_cubemap"\n "$envmaptint" "[.7 .7 .72]"\n "$halflambert" "1"\n')
    for st,M in (('closed','token_sm_zippo'),('open','token_sm_zippo_open')):
        v,nn,u,i=zippo(st); n[M]=model(M,[(v,nn,u,i,'token_sm_zippo','LeftHand',GRIP_ZIPPO)])
    # glass (whiskey idle grip, right hand)
    path='base\\environment\\decoration\\dining_accessories\\tableware\\glass\\glass_f_whiskey.mesh'; s=garments.segs_of(path); m=mesh.decode(s); b,r,mm,apps=mats.mesh_info(s); cm=apps['default']
    gp=[]
    for x in m['subs']:
        mn=cm[x['chunk']] if x['chunk']<len(cm) else cm[0]
        if 'spice' in mn or 'decal' in mn: continue
        name='token_glass_whiskey' if 'fluid' in mn else 'token_glass_glass'
        gp.append((x['pos'],np.asarray(x.get('nrm') if x.get('nrm') is not None else np.tile([0,0,1.0],(len(x['pos']),1)),float)[:,:3],x['uv0'],x['idx'],name,'RightHand',dseq.prop_rel('Right')))
    n['token_sm_glass']=model('token_sm_glass',gp)    # materials token_glass_* already exist (drinkware)
    # ---------------- anchors (PAC bone-local inches): bone matrix of the Valve bind
    def local(bone,p_cp_item,rel):
        X=frame(bone,rel); pv=(X@np.r_[RT.C@p_cp_item*RT.S,1])[:3]; B=RT.NW[RT.vn.index(VB[bone])]; return (np.linalg.inv(B)@np.r_[pv,1])[:3].round(3).tolist()
    A=dict(tip_hand=local('LeftHand',TIP,GRIP_IDLE),tip_smoke=local('LeftHand',TIP,GRIP_SMOKE),tip_mouth=local('Head',TIP,GRIP_MOUTH),
           filter_mouth=local('Head',FILTER,GRIP_MOUTH),flame=local('LeftHand',FLAME,GRIP_ZIPPO))
    json.dump(A,open('/home/claude/work/smoke/anchors.json','w'),indent=1)
    print(n); print(A)
if __name__=='__main__': build()
