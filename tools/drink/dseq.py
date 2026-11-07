"""Token's whiskey stance, composed in Cyberpunk space:
   right arm + body = whisky-glass clip (option C, stand_table_lean180__rh_whisky__01)
   left arm (bottle) = bottle clip (option A, stand__rh_bottle__01), MIRRORED to the left side
   A-events (check bottle, swig, yawn, neck stretch) also drive the head/neck; C-events drive everything but the left arm."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
import cpanim,xf
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~animations~npc~generic_characters~male_average~'
N=cpanim.NAMES; I={n:i for i,n in enumerate(N)}; PAR=cpanim.PAR
_C=cpanim.clips(F+'interactive_scene~generic_male_average__stand_table_lean180__rh_whisky__01.anims')
_A=cpanim.clips(F+'open_world~generic_male_average_work__stand__rh_bottle__01.anims')
C={k.replace('stand_table_lean180__rh_whisky__01','C'):cpanim.Clip(v) for k,v in _C.items()}
A={k.replace('stand__rh_bottle__01','A'):cpanim.Clip(v) for k,v in _A.items()}
from seq_util import q_of,blend,ss
def swap(n):
    for a,b in (('Left','Right'),('l_','r_'),('L_','R_')):
        if a in n: return n.replace(a,b)
        if b in n: return n.replace(b,a)
    return n
MIR=[I.get(swap(n),i) for i,n in enumerate(N)]
Rm=np.diag([-1.0,1,1,1])
_BL=[xf.T(xf.q2m(q),t) for t,q in cpanim.REST]; BW=xf.world(PAR,_BL)
KFIX=[np.linalg.inv(Rm@BW[MIR[i]]@Rm)@BW[i] for i in range(len(N))]   # each bone's own axis convention (left/right axes aren't plain reflections)
def mirror_world(W): return [Rm@W[MIR[i]]@Rm@KFIX[i] for i in range(len(W))]
def locals_of(W): return [W[j] if PAR[j]<0 else np.linalg.inv(W[PAR[j]])@W[j] for j in range(len(W))]
def desc(root):
    out={I[root]}; ch=True
    while ch:
        ch=False
        for j,p in enumerate(PAR):
            if p in out and j not in out: out.add(j); ch=True
    return out
LARM=desc('LeftShoulder')
HEAD={I[n] for n in ('Neck','Neck1','Head') if n in I}
XF=0.45
EVENTS=[(2.0,'C','C__drink__01'),(9.0,'A','A__check_bottle__01'),(15.0,'C','C__head_nod__02'),(18.0,'C','C__drink__02'),
        (25.0,'A','A__drink__01'),(32.5,'C','C__rh_flick__01'),(35.5,'C','C__drink__03'),(40.5,'A','A__yawn__01'),
        (46.5,'C','C__drink__04'),(51.5,'A','A__stretch_neck__01'),(57.5,'C','C__head_nod__03'),(61.0,'A','A__check_bottle__02'),
        (67.0,'C','C__look_down__01')]
LOOP=72.0
def _ev(t,side):
    base=C['C'] if side=='C' else A['A']; L=base.local(t%base.dur); w_ev=0.0
    for st,s,nm in EVENTS:
        if s!=side: continue
        c=(C if s=='C' else A)[nm]
        if st<=t<st+c.dur:
            u=t-st; w=min(ss(u/XF),ss((c.dur-u)/XF)); L=blend(L,c.local(u),w); w_ev=w
    return L,w_ev
def local_at(t):
    t=t%LOOP
    Lc,_=_ev(t,'C'); La_raw,wa=_ev(t,'A')
    La=locals_of(mirror_world(xf.world(PAR,La_raw)))
    L=list(Lc)
    for j in LARM: L[j]=La[j]
    if wa>0:
        for j in HEAD: L[j]=blend([Lc[j]],[La[j]],wa)[0]
    return L
def world_at(t): return xf.world(PAR,local_at(t))
# ---- props: hand-relative transforms (CP space), constant per hand
def prop_rel(side):
    """glass: WeaponRight of the whisky clip vs RightHand; bottle: the bottle clip's WeaponRight, mirrored onto the left hand"""
    acc=[]
    if side=='Right':
        c=C['C']
        for t in np.linspace(0,c.dur,8,endpoint=False):
            W=c.world(t); acc.append(np.linalg.inv(W[I['RightHand']])@W[I['WeaponRight']])
    else:
        c=A['A']
        for t in np.linspace(0,c.dur,8,endpoint=False):
            W=c.world(t); Wm=mirror_world(W); acc.append(np.linalg.inv(Wm[I['LeftHand']])@(Rm@W[I['WeaponRight']]@Rm))
    M=acc[0].copy(); M[:3,3]=np.mean([a[:3,3] for a in acc],0); return M
