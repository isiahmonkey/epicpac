"""Step 1 of the hand reset: a bare-hand test.
 token_testhands.mdl   Cyberpunk's base male hands (hand sub-mesh only, CP artist weights, joints from the hand's own bind),
                       on Token's arm skin texture. Bone-merges onto Kleiner like every Token piece.
 token_fingertest.json PAC stance: both hands raised in front of the chest, palms to the camera; each finger curls and opens
                       in turn (thumb .. pinky), then a full fist, then open. 11 s loop.
 reference renders     the same hands posed on Cyberpunk's OWN rig with the same joint angles (what correct looks like),
                       and my simulation of the game, so the in-game screenshot can be compared to both."""
import sys,os,json,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/token','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
import retarget as RT, smd, xf, gbase, basehand as BH
OUT='/mnt/user-data/outputs/token_build/'; VB='ValveBiped.Bip01_'
VIX={n:i for i,n in enumerate(RT.vn)}
# ------------------------------------------------------------------ model
import os as _os
VARIANT=_os.environ.get('VARIANT','')
def build_model():
    import handfit
    if 'nothumbfit' in VARIANT: handfit.THUMB_FIT=False
    BH.THENAR='thenar' in VARIANT or 'nothumbfit' in VARIANT
    import token_kit as K
    T=[]
    for s in 'lr':
        for p in (BH.hand_smoothed(s,8,cut=False) if 'smooth' in VARIANT else BH.hand(s)):
            # the whole Cyberpunk base arm (hand + forearm + upper arm), one continuous mesh: no wrist seam. Replaces the
            # Gorilla arm skin in the test (its hidden hand stub was the swollen blob seen in game).
            # orient every triangle the way its normals point and write as-is (Source culls back faces; the raw Cyberpunk
            # winding left parts of the hand invisible from some angles in game)
            Fi=p['idx'].copy(); a,b,c=p['pos'][Fi[:,0]],p['pos'][Fi[:,1]],p['pos'][Fi[:,2]]
            bad=(np.cross(b-a,c-a)*p['nrm'][Fi].sum(1)).sum(1)<0; Fi[bad]=Fi[bad][:,[0,2,1]]
            T+=smd.part_tris(p['pos'],p['nrm'],p['uv'],Fi.ravel(),p['lk'],'token_arms',flip=False)
    M='token_testhands'+(_os.environ.get('SUFFIX',''))
    smd.write(OUT+'modelsrc/%s_bind.smd'%M,K.VN,K.VP,K.NLX,[]); smd.write(OUT+'modelsrc/%s_body.smd'%M,K.VN,K.VP,K.NLX,T)
    used=sorted({b for _,vs in T for v in vs for b,_ in v[3]})
    qc=['$modelname "player/token/%s.mdl"'%M,'$cdmaterials "models/player/token/"','$surfaceprop "flesh"','$model "%s_bind" "%s_bind.smd"'%(M,M),
        '$bodygroup "hands"\n{\n studio "%s_body.smd"\n}'%M,'$sequence "idle" "%s_bind.smd" fps 1'%M]
    qc+=['$bonemerge "%s"'%RT.vn[b] for b in used]
    open(OUT+'modelsrc/%s.qc'%M,'w',newline='\r\n').write('\n'.join(qc)+'\n')
    json.dump(dict(model=M,materials=['token_arms'],bodygroups={'hands':['hands']},tris=len(T)),open(OUT+'plans/_%s.json'%M,'w'),indent=1)
    print(M,len(T),'tris, bones',len(used))
# ------------------------------------------------------------------ pose
GW={}
for l in open('/mnt/user-data/uploads/V_Gmod/token_pose_idle.txt'):
    n,t,a=l.strip().split('|')
    if t!='nil': GW[n]=gbase.ang2m(*map(float,a.split()))
BASE={}
for n in GW:
    p=RT.vp[VIX[n]] if n in VIX else -1
    if p>=0 and RT.vn[p] in GW: BASE[n]=GW[RT.vn[p]].T@GW[n]
CH='%sSpine4'%VB; MB=GW[CH]@RT.NW[VIX[CH]][:3,:3].T            # bind-world directions -> game-world (upper body)
def _rb(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); c=a@b
    if np.linalg.norm(v)<1e-9: return np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]); return np.eye(3)+K+K@K/(1+c)
def _aim(bone,d_bind):
    """world rotation (bind frame) for a bone so its child offset points along d_bind, minimal twist from the bind"""
    Rb=RT.NW[VIX[bone]][:3,:3]; ax=Rb@np.array([1.0,0,0]); return _rb(ax,d_bind)@Rb
def Rz(a): c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
CURL=np.radians([55,80,60])          # knuckle / middle / end joint at a full curl
THUMB=np.radians([25,35,40])
def arm_world(side):
    """bind-frame world rotations: hand raised in front of the chest, fingers up, palm toward the camera (+X)"""
    sg=1 if side=='L' else -1
    up=_aim(VB+side+'_UpperArm',np.array([0.25,0.30*sg,-1.0]))
    fo=_aim(VB+side+'_Forearm',np.array([0.55,0.05*sg,1.0]))
    x=np.array([0.10,-0.08*sg,1.0]); x/=np.linalg.norm(x); pal=np.array([1.0,0,0])      # palm normal = camera direction
    y=-(pal-(pal@x)*x); y/=np.linalg.norm(y); z=np.cross(x,y)                          # fingers curl toward -y = the palm
    H=np.c_[x,y,z]
    if side=='R': H=np.c_[x,y,-z] if np.linalg.det(np.c_[x,y,-z])>0 else H
    return {VB+side+'_UpperArm':up,VB+side+'_Forearm':fo,VB+side+'_Hand':H}
def curls(t):
    """per finger 0..1 curl at time t (s): 0.5 s blend, then thumb..pinky 1.4 s each, then fist 1.6 s, open; loop 11 s"""
    t=t%11.0; c=np.zeros(5)
    for f in range(5):
        a=0.5+1.4*f; u=t-a
        if 0<=u<1.4: c[f]=np.sin(np.pi*min(u/1.2,1.0))**2 if u<1.2 else 0
    u=t-7.5
    if 0<=u<2.5: c[:]=np.clip(min(u/0.8,1.0,(2.5-u)/0.8),0,1)
    return c
def rots_bind(t):
    """bind-frame world rotations for arms, hands, fingers"""
    R={}; c=curls(t)
    for side in 'LR':
        H=MB.T@GW[VB+side+'_Hand']; Hb=RT.NW[VIX[VB+side+'_Hand']][:3,:3]      # arms stay in the idle: only the fingers move (fewest assumptions)
        for f in range(5):
            par=H; parb=Hb; ang=(THUMB if f==0 else CURL)*c[f]
            for k,suf in enumerate(('','1','2')):
                n=VB+'%s_Finger%d%s'%(side,f,suf); Lb=BASE[n]   # rest = Kleiner's relaxed in-game finger pose (the bind pose splays the thumb straight out)
                sgn=-1 if side=='L' else -1
                W=par@Lb@Rz(sgn*ang[k]); R[n]=W; par=W
    return R
def bone_info(t):
    R=rots_bind(t); out={}
    for n,Wb in R.items():
        p=RT.vn[RT.vp[VIX[n]]]
        Pw=MB@R[p] if p in R else GW[p]; Lw=Pw.T@(MB@Wb)
        if n.endswith('_Hand'): continue
        d=BASE[n].T@Lw; x,y,z=np.degrees(xf.m2euler(d)); out[n]={'RR':round(float(y),2),'RU':round(float(z),2),'RF':round(float(x),2)}
    return out
def build_anim(path,fps=20):
    ts=np.arange(0,11.0,1/fps); FD=[{'FrameRate':2.0,'BoneInfo':bone_info(0.0)}]
    FD+=[{'FrameRate':fps,'BoneInfo':bone_info(t)} for t in ts[1:]]+[{'FrameRate':fps,'BoneInfo':bone_info(0.0)}]
    J={'Type':'stance','Interpolation':'linear','RestartFrame':2,'FrameData':FD}
    json.dump(J,open(path,'w'),separators=(',',':')); print('anim',path,len(FD),'frames',os.path.getsize(path),'bytes')
def sim_NW(t):
    """what the game should show: Token's in-game idle with this stance applied (simgmod's additive model)"""
    import simgmod; return simgmod.apply(bone_info(t))
if __name__=='__main__':
    if 'model' in sys.argv: build_model()
    if 'anim' in sys.argv: build_anim('/home/claude/epicpac/anim/token_fingertest.json')
# ------------------------------------------------------------------ renders (sim of the game + Cyberpunk-rig reference)
def pose_bind(t):
    """skin matrices in the bind frame for the simulated in-game pose"""
    R=rots_bind(t); NW=[None]*len(RT.vn)
    for i,n in enumerate(RT.vn):
        Rw=R[n] if n in R else (MB.T@GW[n] if n in GW else RT.NW[i][:3,:3])
        p=RT.vp[i]
        pos=RT.NW[i][:3,3] if p<0 else NW[p][:3,3]+NW[p][:3,:3]@RT.NL[i][:3,3]
        NW[i]=xf.T(Rw,pos)
    return [NW[i]@np.linalg.inv(RT.NW[i]) for i in range(len(RT.vn))]
def cp_reference(t,side):
    """the bare hand deformed on Cyberpunk's own rig: same curl angles about each CP joint, CP artist weights"""
    import cr2w,mesh
    g=mesh.decode(cr2w.load_loose(BH.A%side.lower())); s=g['subs'][2]; B=list(g['bones']); bp=dict(zip(B,np.asarray(g['bonepos'],float)))
    S='Left' if side=='L' else 'Right'; P=np.asarray(s['pos'],float); c=curls(t)
    M={b:np.eye(4) for b in B}
    pal=np.cross(bp[S+'HandIndex1']-bp[S+'HandPinky1'],bp[S+'HandMiddle1']-bp[S+'Hand']); pal/=np.linalg.norm(pal)
    for f,nm in enumerate(('Thumb','Index','Middle','Ring','Pinky')):
        js=[S+'Hand%s%d'%(nm,k) for k in (1,2,3) if S+'Hand%s%d'%(nm,k) in bp]; ang=(THUMB if f==0 else CURL)*c[f]; acc=np.eye(4)
        for k,j in enumerate(js):
            nxt=bp[js[k+1]] if k+1<len(js) else bp[j]+(bp[j]-bp[js[k-1]])
            d=nxt-bp[j]; h=np.cross(d,pal); h/=np.linalg.norm(h)
            a=ang[k] if f else ang[k]
            Rk=np.eye(4); c_,s_=np.cos(a),np.sin(a); K=np.array([[0,-h[2],h[1]],[h[2],0,-h[0]],[-h[1],h[0],0]]); Rk[:3,:3]=np.eye(3)+s_*K+(1-c_)*K@K
            piv=(acc@np.r_[bp[j],1])[:3]; T1=xf.T(np.eye(3),piv); T0=xf.T(np.eye(3),-piv)
            acc=T1@(np.eye(4)+0)@T0@acc if False else T1@Rk@T0@acc; M[j]=acc.copy()
    ji=np.asarray(s['ji']); jw=np.asarray(s['jw'],float); h=np.c_[P,np.ones(len(P))]; out=np.zeros((len(P),3))
    for k in range(ji.shape[1]):
        Ms=np.stack([M[B[j]] for j in ji[:,k]]); out+=jw[:,k,None]*np.einsum('nij,nj->ni',Ms[:,:3,:],h)
    return out/np.maximum(jw.sum(1,keepdims=True),1e-9), np.asarray(s['idx']).reshape(-1,3), pal
