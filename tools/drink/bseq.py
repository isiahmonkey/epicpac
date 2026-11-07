"""Token's bouncer idle (CP space): the q115 'ma_bouncer' clip's folded-hands hold (3.6-9.2 s) looped with a crossfade.
   Head/neck pulled toward the clip's chin-up end pose so he stands stout instead of looking at the floor."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/drink']
import cpanim,xf
from seq_util import blend,ss
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~animations~quest~main_quests~part1~q115~q115_00b_hanako~body~q115_00b_hanako__ma_bouncer.anims'
N=cpanim.NAMES; I={n:i for i,n in enumerate(N)}; PAR=cpanim.PAR
B=cpanim.Clip(list(cpanim.clips(F).values())[0])
S0,S1,XF=3.6,9.2,0.9
LOOP=S1-S0
HEADW=float(sys.argv[1]) if len(sys.argv)>1 and __name__=='__main__' else 0.8
UP=B.local(12.6)
HEAD=[I[n] for n in ('Neck','Neck1','Head') if n in I]
def local_at(t):
    t=t%LOOP; L=B.local(S0+t)
    if t>LOOP-XF: L=blend(L,B.local(S0+t-LOOP),ss((t-(LOOP-XF))/XF))   # fade the end into the start
    L=list(L)
    for j in HEAD: L[j]=blend([L[j]],[UP[j]],HEADW)[0]
    return L
def world_at(t): return xf.world(PAR,local_at(t))
class _C:   # Clip-like wrapper for preview.py
    dur=LOOP
    def world(self,t): return world_at(t)
    def local(self,t): return local_at(t)
clip=_C()
