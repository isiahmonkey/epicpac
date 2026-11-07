"""Token's bouncer idle, hands behind the back: the q115 'ma_bouncer' clip's final pose (12.9 s), kept alive with the
   torso/head sway of the folded-hands loop (bseq) layered on top as rotation deltas. Arms stay locked behind the back."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/drink']
import bseq,xf
N=bseq.N; I=bseq.I; PAR=bseq.PAR
BACK=bseq.B.local(12.9)
def desc(root):
    out={I[root]}; ch=True
    while ch:
        ch=False
        for j,p in enumerate(PAR):
            if p in out and j not in out: out.add(j); ch=True
    return out
ARMS=desc('LeftShoulder')|desc('RightShoulder')
REF=bseq.local_at(0.0)
LOOP=bseq.LOOP
def local_at(t):
    F=bseq.local_at(t); L=[]
    for j in range(len(N)):
        if j in ARMS: L.append(BACK[j]); continue
        d=F[j][:3,:3]@REF[j][:3,:3].T           # sway relative to the loop's first frame
        M=BACK[j].copy(); M[:3,:3]=d@BACK[j][:3,:3]; L.append(M)
    return L
def world_at(t): return xf.world(PAR,local_at(t))
class _C:
    dur=LOOP
    def world(self,t): return world_at(t)
    def local(self,t): return local_at(t)
clip=_C()
