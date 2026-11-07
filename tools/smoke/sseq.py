"""Token's drink-and-smoke idle, composed in Cyberpunk space.
 right arm: whisky glass held at the belly (C idle) + C drink clips
 body + left arm: Cyberpunk's stand__rh_cigarette__01 set MIRRORED onto the left hand (smoke / ash / look around)
 intro: pocket -> cigarette to the lips (rests there) -> pocket -> Zippo up to the tip, light it -> pocket -> first drag."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/anim','/home/claude/work/drink','/home/claude/tools/scripts','/home/claude/work/build']
import cpanim,xf,seq as S,dseq as D
from seq_util import blend,ss
N=cpanim.NAMES; I={n:i for i,n in enumerate(N)}; PAR=cpanim.PAR
Rm=D.Rm; mirror_world=D.mirror_world; locals_of=D.locals_of; desc=D.desc
LARM=desc('LeftShoulder'); RARM=desc('RightShoulder'); HEAD={I[n] for n in ('Neck','Neck1','Head') if n in I}
CIG=S.C; IDLE=S.IDLE; GL=D.C; GLASS_IDLE=GL['C']
def mloc(clip,t): return locals_of(mirror_world(clip.world(t)))          # mirrored clip -> locals
def W_of(L): return xf.world(PAR,L)
XF=0.45
# ------------------------------------------------------------------ loop (40 s = two 20 s cycles)
LOOP=42.0     # two ~20 s cycles: drink, ash, drag | drink, ash, look around, drag
LEFT=[(7.0,'stand__rh_cigarette__01__drop_ash__01'),(13.0,'stand__rh_cigarette__01__smoke__01'),
      (26.3,'stand__rh_cigarette__01__drop_ash__03'),(31.5,'stand__rh_cigarette__01__look_around__02'),(35.5,'stand__rh_cigarette__01__smoke__02')]
RIGHT=[(1.0,'C__drink__01'),(20.5,'C__drink__02')]
def base_local(t):
    L=mloc(IDLE,t%IDLE.dur); G=GLASS_IDLE.local(t%GLASS_IDLE.dur)
    for j in RARM: L[j]=G[j]
    return L
def loop_local(t):
    t=t%LOOP; L=base_local(t)
    for st,nm in LEFT:
        c=CIG[nm]
        if st<=t<st+c.dur:
            u=t-st; w=min(ss(u/XF),ss((c.dur-u)/XF)); M=mloc(c,u)
            L=[L[j] if j in RARM else blend([L[j]],[M[j]],w)[0] for j in range(len(N))]
    for st,nm in RIGHT:
        c=GL[nm]
        if st<=t<st+c.dur:
            u=t-st; w=min(ss(u/XF),ss((c.dur-u)/XF)); G=c.local(u)
            for j in RARM|HEAD: L[j]=blend([L[j]],[G[j]],w)[0]
    return L
# ------------------------------------------------------------------ props in hand / head frames (CP space)
def _wr_mirror(W):            # the cigarette clip's WeaponRight carried onto the left hand
    return Rm@W[I['WeaponRight']]@Rm
def _avg(Ms):
    R=sum(m[:3,:3] for m in Ms); U,_,Vt=np.linalg.svd(R); M=np.eye(4); M[:3,:3]=U@Vt; M[:3,3]=np.mean([m[:3,3] for m in Ms],0); return M
def _cig_hand():
    acc=[]
    for t in np.linspace(0,IDLE.dur,10,endpoint=False):
        W=IDLE.world(t); Wm=mirror_world(W); acc.append(np.linalg.inv(Wm[I['LeftHand']])@_wr_mirror(W))
    return _avg(acc)
CIG_HAND=_cig_hand()                        # cigarette frame in the LEFT hand frame
SM2=CIG['stand__rh_cigarette__01__smoke__02']; TC=1.30   # smoke__02: filter at the lips at 1.3 s
def _cig_mouth():
    W=SM2.world(TC); Wm=mirror_world(W); return np.linalg.inv(Wm[I['Head']])@Wm[I['LeftHand']]@CIG_HAND
CIG_MOUTH=_cig_mouth()                      # the same cigarette pose, held by the lips (head frame)
ZIPPO=None                                  # set by props: Zippo frame in the LEFT hand (from npc1's light clip)
FLAME=np.array([0,0,0.032])                 # flame above the Zippo origin (item space, m), refined by props
# ------------------------------------------------------------------ intro (left-hand IK over the base pose)
def two_bone(W,target,pole_hint):
    S_,E_,H_=I['LeftArm'],I['LeftForeArm'],I['LeftHand']
    s=W[S_][:3,3]; e=W[E_][:3,3]; h=W[H_][:3,3]
    a=np.linalg.norm(e-s); b=np.linalg.norm(h-e); d=target-s; dl=np.clip(np.linalg.norm(d),1e-4,a+b-1e-4); dn=d/np.linalg.norm(d)
    ca=np.clip((a*a+dl*dl-b*b)/(2*a*dl),-1,1); pole=pole_hint-(pole_hint@dn)*dn; pole/=np.linalg.norm(pole)+1e-9
    e2=s+dn*a*ca+pole*a*np.sqrt(1-ca*ca); h2=s+dn*dl
    def rb(u,v):
        u=u/np.linalg.norm(u); v=v/np.linalg.norm(v); c=np.cross(u,v); cs=u@v
        if np.linalg.norm(c)<1e-9: return np.eye(3)
        K=np.array([[0,-c[2],c[1]],[c[2],0,-c[0]],[-c[1],c[0],0]]); return np.eye(3)+K+K@K/(1+cs)
    R1=rb(e-s,e2-s); R2=rb(R1@(h-e),h2-e2)
    return {S_:R1,E_:R2@R1},(e2,h2)
def ik_world(L,target,grip=None,gw=0.0):
    """left arm reaches `target` (CP world); hand rotation optionally blended toward `grip` (a local hand rotation)"""
    W=W_of(L)
    if target is None: return W
    rot,(e2,h2)=two_bone(W,target,np.array([-0.8,-0.2,-0.9]))
    S_,E_,H_=I['LeftArm'],I['LeftForeArm'],I['LeftHand']
    L2=list(L)
    # new arm/forearm world rotations -> locals
    Ws=xf.T(rot[S_]@W[S_][:3,:3],W[S_][:3,3]); We=xf.T(rot[E_]@W[E_][:3,:3],e2)
    L2[S_]=np.linalg.inv(W[PAR[S_]])@Ws
    # forearm twist bones etc. keep their locals; the elbow's local follows from its new world
    p=PAR[E_]; Wp=Ws
    chain=[]; j=p
    while j!=S_: chain.append(j); j=PAR[j]
    for j in reversed(chain): Wp=Wp@L2[j]
    L2[E_]=np.linalg.inv(Wp)@We
    if grip is not None and gw>0: L2[H_]=blend([L2[H_]],[grip],gw)[0]
    return W_of(L2)
def hips(W): return W[I['Hips']]
def at_hips(v): return lambda W: hips(W)[:3,3]+np.array(v)
POCKET=at_hips([-0.17,0.06,-0.06])          # left front jeans pocket (character faces +Y, his left is -X)
def tip_world(W):
    """lit end of the resting cigarette (CP world)"""
    return (W[I['Head']]@CIG_MOUTH@np.r_[CIG_TIP,1])[:3]
CIG_TIP=np.array([0,-0.075,0])              # lit end in the cigarette item frame; set by props from the mesh
def zippo_target(W,grip_w):
    """hand position so the Zippo flame sits 1 cm under the cigarette tip"""
    Wh=W[I['LeftHand']]; fl=(Wh@ZIPPO@np.r_[FLAME,1])[:3]-Wh[:3,3]
    return tip_world(W)+np.array([0,0,-0.012])-fl
LIGHT_GRIP=None
def _light_grip():
    c=S.LIGHT; return c.local(min(4.0,c.dur))[I['LeftHand']]
# key timeline: (time, target fn or 'anim', grip weight)
SEG=[]
def sseq_TC(): return TC
def build_intro():
    global INTRO,KEYS,LIGHT_GRIP,T
    LIGHT_GRIP=_light_grip()
    T=dict(pocket1=0.9, cig_show=1.05, up1=1.5)
    T['sm_in']=T['up1']                      # smoke__02 approach starts (hand at the idle carry)
    T['lips']=T['sm_in']+TC                  # filter at the lips -> cigarette swaps to the mouth
    T['away']=T['lips']+0.25
    T['pocket2']=T['away']+0.85; T['zippo_show']=T['pocket2']+0.2
    T['tipreach']=T['zippo_show']+1.0; T['open']=T['tipreach']+0.1; T['flame']=T['open']+0.12; T['lit']=T['flame']+0.7
    T['close']=T['lit']+0.55; T['down']=T['close']+0.15; T['pocket3']=T['down']+0.85; T['zippo_hide']=T['pocket3']+0.15
    T['up3']=T['zippo_hide']+0.45
    T['sm2']=T['up3']                        # smoke__02 from the start: hand to the lips, takes the cigarette (1.0-1.3 s), drag
    T['take']=T['sm2']+TC          # hand reaches the lips (lip-fixed): mouth cigarette -> hand
    INTRO=T['sm2']+SM2.dur
    return T
def intro_local(t):
    L=base_local(t)
    if T['sm_in']<=t<T['lips']+0.3:                      # carry the cigarette up to the lips (smoke__02 approach)
        u=t-T['sm_in']; w=min(ss(u/0.35),1.0); M=mloc(SM2,min(u,TC))
        L=[L[j] if j in RARM else blend([L[j]],[M[j]],w)[0] for j in range(len(N))]
    if t>=T['sm2']:                                      # first drag
        u=t-T['sm2']; w=min(ss(u/0.4),ss((SM2.dur-u)/XF)); M=mloc(SM2,min(u,SM2.dur))
        L=[L[j] if j in RARM else blend([L[j]],[M[j]],w)[0] for j in range(len(N))]
    return L
def intro_world(t):
    L=intro_local(t)
    w=0.0
    if T['sm_in']<=t<T['lips']+0.3: w=max(w,lip_weight('stand__rh_cigarette__01__smoke__02',min(t-T['sm_in'],sseq_TC())))
    if t>=T['sm2']: w=max(w,lip_weight('stand__rh_cigarette__01__smoke__02',t-T['sm2']))
    if w>1e-3: return lip_fix(L,w)
    W=W_of(L)
    keys=[(0.0,None,0),(T['pocket1']-0.15,POCKET,0),(T['cig_show']+0.15,POCKET,0),(T['up1'],None,0),
          (T['lips']+0.3,None,0),(T['pocket2'],POCKET,0),(T['zippo_show']+0.1,POCKET,0.3),(T['tipreach'],'tip',1),(T['close']+0.1,'tip',1),
          (T['pocket3'],POCKET,0.3),(T['zippo_hide']+0.05,POCKET,0),(T['up3'],None,0)]
    for (t0,a,g0),(t1,b,g1) in zip(keys,keys[1:]):
        if t0<=t<=t1: break
    else: return W
    u=ss((t-t0)/max(t1-t0,1e-6))
    def pos(f):
        if f is None: return W[I['LeftHand']][:3,3]
        if f=='tip': return zippo_target(W,1.0)
        return f(W)
    if a is None and b is None: return W
    pa,pb=pos(a),pos(b); gw=g0*(1-u)+g1*u
    tgt=pa*(1-u)+pb*u; W2=ik_world(L,tgt,LIGHT_GRIP,gw)
    if 'tip' in (a,b):          # flame -> tip: re-aim with the final hand rotation (the grip blend moves the flame)
        k=(u if b=='tip' else 1-u) if a!=b else 1.0
        for _ in range(5):        # measured on Kleiner's skeleton (Gmod), where the stance actually plays
            e=valve_flame_err(W2); tgt=tgt+e*k; W2=ik_world(L,tgt,LIGHT_GRIP,gw)
    return W2
import vanim, retarget as RT
def _bindframe(bone,rel): return RT.D[bone]@RT.CW[bone]@RT.tov(rel)
def valve_flame_err(W):
    """(cigarette tip - 1.2 cm) minus Zippo flame, on Token's Kleiner skeleton, returned in CP metres"""
    NW=vanim.full_world(vanim.valve_world_rots_W(W))
    def posed(vb,cpb,rel,p):
        i=RT.vn.index(vb); X=_bindframe(cpb,rel); return (NW[i]@np.linalg.inv(RT.NW[i])@X@np.r_[RT.C@p*RT.S,1])[:3]
    fl=posed('ValveBiped.Bip01_L_Hand','LeftHand',ZIPPO,FLAME); tp=posed('ValveBiped.Bip01_Head1','Head',CIG_MOUTH,CIG_TIP)
    err=(tp+np.array([0,0,-0.47]))-fl          # valve inches, flame 1.2 cm under the tip
    return RT.C.T@err/RT.S
GRIP_SMOKE=None; FILTER=None              # set by props
LIPS={'stand__rh_cigarette__01__drop_ash__03':(0.55,1.2,2.35),'stand__rh_cigarette__01__smoke__01':(0.75,4.2,4.75),'stand__rh_cigarette__01__smoke__02':(0.85,1.3,3.4)}   # (in, contact, out) seconds
def lips_err(W):
    """(mouth filter - hand filter) on Kleiner, in CP metres"""
    NW=vanim.full_world(vanim.valve_world_rots_W(W))
    def posed(vb,cpb,rel,p):
        i=RT.vn.index(vb); X=_bindframe(cpb,rel); return (NW[i]@np.linalg.inv(RT.NW[i])@X@np.r_[RT.C@p*RT.S,1])[:3]
    return RT.C.T@(posed('ValveBiped.Bip01_Head1','Head',CIG_MOUTH,FILTER)-posed('ValveBiped.Bip01_L_Hand','LeftHand',GRIP_SMOKE,FILTER))/RT.S
def lip_fix(L,w):
    """pull the hand so the held filter meets the lips on Token's skeleton (weight w)"""
    if w<=1e-3: return W_of(L)
    W=W_of(L); tgt=W[I['LeftHand']][:3,3].copy()
    for _ in range(3):
        W2=ik_world(L,tgt); tgt=tgt+lips_err(W2)
    return ik_world(L,W[I['LeftHand']][:3,3]*(1-w)+tgt*w)
def lip_weight(clipname,u):
    a,c,b=LIPS[clipname]; return min(ss((u-(a))/(c-a)),ss((b-u)/(b-c)))
def loop_world(t):
    t=t%LOOP; L=loop_local(t); w=0.0
    for st,nm in LEFT:
        if nm in LIPS and st<=t<st+CIG[nm].dur: w=max(w,lip_weight(nm,t-st))
    return lip_fix(L,w)
def world_at(t):
    if t<INTRO-0.6: return intro_world(t)
    if t<INTRO:
        u=ss((t-(INTRO-0.6))/0.6); return W_of(blend(locals_of(intro_world(t)),loop_local(t-INTRO),u))
    return loop_world(t-INTRO)
