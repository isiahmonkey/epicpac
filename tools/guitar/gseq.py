"""Token's guitar stance (outfit 2): Cyberpunk's stand__2h_guitar__pick__01 songs 01 -> 02 -> 03, which chain seamlessly
(72 s loop). The guitar hangs rigid on the chest (CP WeaponLeft averaged in the Spine3 frame); both arms are re-aimed on
Token's Kleiner skeleton so each hand keeps CP's position on the guitar (fret hand on the neck, pick hand over the strings)."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/anim','/home/claude/work/drink','/home/claude/tools/scripts','/home/claude/work/build']
import cpanim,xf,vanim, retarget as RT
from seq_util import blend,ss
N=cpanim.NAMES; I={n:i for i,n in enumerate(N)}; PAR=cpanim.PAR
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~'
_A=cpanim.clips(F+'animations~npc~generic_characters~male_average~interactive_scene~generic_male_average__stand__2h_guitar__pick__01.anims')
SONGS=[cpanim.Clip(_A['stand__2h_guitar__pick__01__play_song__%02d'%k]) for k in (1,2,3)]
IDLE=cpanim.Clip(_A['stand__2h_guitar__pick__01'])
STARTS=np.cumsum([0]+[c.dur for c in SONGS])[:-1]; LOOP=float(sum(c.dur for c in SONGS))
SEAM=0.35
def W_of(L): return xf.world(PAR,L)
def locals_of(W): return [W[j] if PAR[j]<0 else np.linalg.inv(W[PAR[j]])@W[j] for j in range(len(W))]
def cp_local(t):
    t=t%LOOP; k=int(np.searchsorted(STARTS,t,side='right')-1); c=SONGS[k]; u=t-STARTS[k]
    L=c.local(min(u,c.dur))
    if u>c.dur-SEAM:            # ease the 1-3 deg seam into the next song
        n=SONGS[(k+1)%3]; w=ss((u-(c.dur-SEAM))/SEAM)*0.5; L=blend(L,n.local(0),w)
    elif u<SEAM:
        p=SONGS[(k-1)%3]; w=(1-ss(u/SEAM))*0.5; L=blend(L,p.local(p.dur),w)
    return L
def _avg(Ms):
    R=sum(m[:3,:3] for m in Ms); U,_,Vt=np.linalg.svd(R); M=np.eye(4); M[:3,:3]=U@Vt; M[:3,3]=np.mean([m[:3,3] for m in Ms],0); return M
def _guitar_rel():
    acc=[]
    for c in SONGS:
        for t in np.linspace(0,c.dur,40,endpoint=False):
            W=c.world(t); acc.append(np.linalg.inv(W[I['Spine3']])@W[I['WeaponLeft']])
    return _avg(acc)
G_REL=_guitar_rel()                       # guitar (item space) in the CP chest frame
# ---------------------------------------------------------------- Kleiner-side measurement
def bindframe(bone,rel): return RT.D[bone]@RT.CW[bone]@RT.tov(rel)
VCH=RT.vn.index('ValveBiped.Bip01_Spine4')
G_HAND=bindframe('Spine3',G_REL)          # CP's guitar frame in Token's bind: hands are fitted relative to this
# The clip was authored for a guitar whose neck rises ~25 mm higher toward the fretting hand than this mesh's (CP fingertips
# float ~28 mm over this fingerboard while the strumming arm already rests on the body). Tilt the guitar about the body
# (pivot at the pickups, z=0.2 m) so the neck comes up to the fingers and the body stays under the forearm.
TILT_PIVOT=0.20; TILT=np.arcsin(0.025/(0.72-TILT_PIVOT))
def _tilt():
    c,s=np.cos(TILT),np.sin(TILT); R=np.array([[c,0,s],[0,1,0],[-s,0,c]]); p=np.array([0,0,TILT_PIVOT])
    return xf.T(R,p-R@p)
XT=_tilt()                                 # new guitar item space -> CP guitar (WeaponLeft) space
G_BIND=bindframe('Spine3',G_REL@XT)        # guitar as drawn on Token (Valve inches)
def cp_to_item(p): return (np.linalg.inv(XT)@np.r_[p,1])[:3]
VH={'Left':RT.vn.index('ValveBiped.Bip01_L_Hand'),'Right':RT.vn.index('ValveBiped.Bip01_R_Hand')}
def hand_pts(side):
    """palm points of the CP hand (bind, Valve inches): hand origin + middle knuckle"""
    return [RT.D[side+'Hand']@RT.CW[side+'Hand'],RT.D[side+'HandMiddle1']@RT.CW[side+'HandMiddle1']]
def valve_NW(W): return vanim.full_world(vanim.valve_world_rots_W(W))
def hand_in_chest_valve(W,side):
    """CP-skinned hand point in the posed Kleiner chest frame (inches)"""
    NW=valve_NW(W); i=VH[side]; X=hand_pts(side)[0]
    p=(NW[i]@np.linalg.inv(RT.NW[i])@X)[:3,3]; Ch=NW[VCH]@np.linalg.inv(RT.NW[VCH])
    return (np.linalg.inv(Ch)@np.r_[p,1])[:3],Ch
def desired_in_chest_valve(W,side):
    """where CP has that hand relative to the guitar, carried onto the guitar as it hangs on Token"""
    Wg=W[I['Spine3']]@G_REL; rel=np.linalg.inv(W[I['WeaponLeft']])@W[I[side+'Hand']]
    # the hand relative to the *moving* CP guitar, re-attached to the rigid one
    return (G_HAND@RT.tov(rel))[:3,3]
# ---------------------------------------------------------------- two-bone IK in CP space
def two_bone(W,side,target,pole_hint):
    S_,E_,H_=I[side+'Arm'],I[side+'ForeArm'],I[side+'Hand']
    s=W[S_][:3,3]; e=W[E_][:3,3]; h=W[H_][:3,3]
    a=np.linalg.norm(e-s); b=np.linalg.norm(h-e); d=target-s; dl=np.clip(np.linalg.norm(d),1e-4,a+b-1e-4); dn=d/np.linalg.norm(d)
    ca=np.clip((a*a+dl*dl-b*b)/(2*a*dl),-1,1)
    # keep the current elbow side: pole from the present elbow offset
    pole=(e-s)-((e-s)@dn)*dn; pole=pole if np.linalg.norm(pole)>1e-4 else pole_hint-(pole_hint@dn)*dn; pole/=np.linalg.norm(pole)+1e-9
    e2=s+dn*a*ca+pole*a*np.sqrt(1-ca*ca); h2=s+dn*dl
    def rb(u,v):
        u=u/np.linalg.norm(u); v=v/np.linalg.norm(v); c=np.cross(u,v); cs=u@v
        if np.linalg.norm(c)<1e-9: return np.eye(3)
        K=np.array([[0,-c[2],c[1]],[c[2],0,-c[0]],[-c[1],c[0],0]]); return np.eye(3)+K+K@K/(1+cs)
    R1=rb(e-s,e2-s); R2=rb(R1@(h-e),h2-e2)
    return R1,R2@R1,e2
def ik(L,side,target):
    W=W_of(L); S_,E_,H_=I[side+'Arm'],I[side+'ForeArm'],I[side+'Hand']
    R1,R2,e2=two_bone(W,side,target,np.array([0,-1.0,-0.5]))
    L2=list(L); Ws=xf.T(R1@W[S_][:3,:3],W[S_][:3,3]); We=xf.T(R2@W[E_][:3,:3],e2)
    # keep the hand's world orientation (so it stays on the strings/neck at CP's angle)
    Wh=W[H_].copy()
    L2[S_]=np.linalg.inv(W[PAR[S_]])@Ws
    chain=[]; j=PAR[E_]
    while j!=S_: chain.append(j); j=PAR[j]
    Wp=Ws
    for j in reversed(chain): Wp=Wp@L2[j]
    L2[E_]=np.linalg.inv(Wp)@We
    W2=W_of(L2); pe=PAR[H_]; R=np.linalg.inv(W2[pe][:3,:3])@Wh[:3,:3]; L2[H_]=xf.T(R,L2[H_][:3,3])
    return L2
_HM=None
def _heightmap(cell=0.005):
    import gprops
    P=gprops.GP; P=P[P[:,2]<0.53]; ij=np.floor(P[:,1:]/cell).astype(int); H={}
    for (j,k),x in zip(map(tuple,ij),P[:,0]): H[(j,k)]=max(H.get((j,k),-1),x)
    return H,cell
FINGER_R=0.011                                  # Gorilla glove finger half-thickness (m)
def right_lift(W):
    """how far (m, along the guitar's string normal) the strumming hand must rise so its fingers clear the body"""
    global _HM
    if _HM is None: _HM=_heightmap()
    H,cell=_HM; R=_ORIG_ROTS(W); NW=vanim.full_world(R); Gp=NW[VCH]@np.linalg.inv(RT.NW[VCH])@G_BIND; Gi=np.linalg.inv(Gp)
    pts=[NW[VIX[VB+'R_Hand']][:3,3]]
    for f in range(5):
        ch=[VB+'R_Finger%d%s'%(f,k) for k in ('','1','2')]
        for c in ch: pts.append(NW[VIX[c]][:3,3])
        pts.append((NW[VIX[ch[2]]]@np.r_[0.95*np.linalg.norm(RT.NL[VIX[ch[2]]][:3,3]),0,0,1])[:3])
    need=0.0
    for p in pts:
        q=(Gi@np.r_[p,1])[:3]; q=RT.C.T@q/RT.S; key=tuple(np.floor(q[1:]/cell).astype(int))
        if key in H: need=max(need,H[key]+FINGER_R-q[0])
    return need
def tips_bind(W):
    """Token's fretting fingertips (Valve FK, unfretted) in chest-bind coordinates"""
    R=_ORIG_ROTS(W); NW=vanim.full_world(R); Ch=NW[VCH]@np.linalg.inv(RT.NW[VCH]); out={}
    for f,ch in FING.items():
        p=NW[VIX[ch[0]]][:3,3]
        for k,c in enumerate(ch[1:]+[None]):
            o=RT.NL[VIX[c]][:3,3] if c else TIPOFF[f]; p=p+R[ch[k]]@o
        out[f]=(np.linalg.inv(Ch)@np.r_[p,1])[:3]
    return out
def fit(L,iters=3,outer=1):
    W=W_of(L); AX=G_BIND[:3,:3]@RT.C@np.array([1.0,0,0])        # guitar string-facing axis (bind)
    for side in ('Left','Right'):
        want=desired_in_chest_valve(W,side); tgt=W[I[side+'Hand']][:3,3].copy(); L2=L
        for o in range(outer if side=='Left' else 1):
            for _ in range(iters):
                have,Ch=hand_in_chest_valve(W_of(L2),side)
                err=Ch[:3,:3]@(want-have)                 # Valve world inches
                tgt=tgt+RT.C.T@err/RT.S; L2=ik(L,side,tgt)
            if side=='Right':
                # strumming hand: lift it along the string normal until no finger joint / tip is inside the body
                for _ in range(3):
                    lift=right_lift(W_of(L2))
                    if lift<=0.0005: break
                    want=want+AX*lift*RT.S
                    for _ in range(iters):
                        have,Ch=hand_in_chest_valve(W_of(L2),side); err=Ch[:3,:3]@(want-have); tgt=tgt+RT.C.T@err/RT.S; L2=ik(L,side,tgt)
            if side=='Left':
                # slide the fretting hand along / across the neck so Token's own fingertips sit over Cyberpunk's frets
                T=fret_targets(W); tb=tips_bind(W_of(L2))
                d=np.mean([(G_BIND@np.r_[RT.C@T[f]*RT.S,1])[:3]-tb[f] for f in T],0); d=d-(d@AX)*AX*0.6
                want=want+d
        L=L2
    return W_of(L)
def world_at(t): return fit(cp_local(t))
# ---------------------------------------------------------------- fretting hand (Valve side, after the rotation transfer)
# The clip's guitar neck sat ~25 mm higher off the hand than this mesh's fingerboard, so gprops moves the guitar that much
# along its string-facing axis (OFFSET_X). Each fretting finger is then bent (CCD, hinge joints, anatomical limits) so its
# tip lands where Cyberpunk's does along the neck and across the strings: on the fingerboard when Cyberpunk presses
# (tip within PRESS of the board), lifted by Cyberpunk's own height when it doesn't.
OFFSET_X=0.0          # superseded by TILT (a straight 25 mm lift pushed the body into the strumming forearm)
BOARD=0.01122+OFFSET_X; NECK_Z=(0.53,0.80); NECK_YR=(-0.0239,0.0180); PAD=0.0075; PRESS=0.012
_ORIG_ROTS=vanim.valve_world_rots_W
VB='ValveBiped.Bip01_'; VIX={n:i for i,n in enumerate(RT.vn)}
FING={f:[VB+'L_Finger%d%s'%(f,k) for k in ('','1','2')] for f in range(1,5)}
CPF={1:'Index',2:'Middle',3:'Ring',4:'Pinky'}
TIPOFF={f:np.array([0.95*np.linalg.norm(RT.NL[VIX[FING[f][2]]][:3,3]),0,0]) for f in FING}
def cp_tip_item(W,nm,side='Left'):
    a,b=W[I[side+'Hand%s2'%nm]][:3,3],W[I[side+'Hand%s3'%nm]][:3,3]; tip=b+(b-a)*0.7
    return cp_to_item((np.linalg.inv(W[I['WeaponLeft']])@np.r_[tip,1])[:3])
def fret_targets(W):
    out={}
    for f,nm in CPF.items():
        p=cp_tip_item(W,nm); h=p[0]-BOARD
        x=BOARD+PAD if h<PRESS else BOARD+PAD+(h-PRESS)
        out[f]=np.array([x,np.clip(p[1],NECK_YR[0]+0.004,NECK_YR[1]-0.004),np.clip(p[2],NECK_Z[0]+0.01,NECK_Z[1]-0.004)])
    return out
def _axrot(a,ang):
    a=a/np.linalg.norm(a); K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]]); return np.eye(3)+np.sin(ang)*K+(1-np.cos(ang))*K@K
def _curl(Rp,Rc):
    """signed curl of a child relative to its parent about the parent's z (fingers curl toward -y: negative)"""
    x=Rp.T@Rc[:,0]; return np.arctan2(x[1],x[0])
LIM={0:(-1.25,0.35),1:(-1.85,0.15),2:(-1.6,0.15)}          # knuckle / middle / end joint (rad)
def fret_fix(W,R,iters=10):
    NW=vanim.full_world(R)
    Gp=NW[VCH]@np.linalg.inv(RT.NW[VCH])@G_BIND
    hand=R[VB+'L_Hand']
    for f,T_item in fret_targets(W).items():
        T=(Gp@np.r_[RT.C@T_item*RT.S,1])[:3]; ch=FING[f]
        if any(c not in R for c in ch): continue
        p0=NW[VIX[ch[0]]][:3,3]; off=[RT.NL[VIX[ch[1]]][:3,3],RT.NL[VIX[ch[2]]][:3,3],TIPOFF[f]]
        Rs=[R[c].copy() for c in ch]
        def fk(Rs):
            P=[p0]; 
            for k in range(3): P.append(P[-1]+Rs[k]@off[k])
            return P
        for _ in range(iters):
            for j in (2,1,0):
                P=fk(Rs); e=P[3]-P[j]; d=T-P[j]
                if j>0:
                    h=Rs[j][:,2]; e2=e-(e@h)*h; d2=d-(d@h)*h
                    if np.linalg.norm(e2)<1e-6 or np.linalg.norm(d2)<1e-6: continue
                    ang=np.arctan2(np.cross(e2,d2)@h,e2@d2); Q=_axrot(h,ang)
                else:
                    c=np.cross(e,d); s=np.linalg.norm(c)
                    if s<1e-9: continue
                    ang=np.arctan2(s,e@d)*0.6; Q=_axrot(c,ang)
                new=[Q@Rs[k] if k>=j else Rs[k] for k in range(3)]
                par=hand if j==0 else new[j-1]
                lo,hi=LIM[j]; cu=_curl(par,new[j])
                if lo<=cu<=hi or (j==0): Rs=new
            if np.linalg.norm(fk(Rs)[3]-T)<0.02: break
        for c,r in zip(ch,Rs): R[c]=r
    return R
def rots_fretted(W): return fret_fix(W,_ORIG_ROTS(W))
def install_fretting():
    vanim.valve_world_rots_W=rots_fretted
    vanim.valve_world_rots=lambda clip,t: rots_fretted(clip.world(t))
def valve_NW(W): return vanim.full_world(_ORIG_ROTS(W))
