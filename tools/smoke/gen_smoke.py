"""Token's drink-and-smoke stance -> PAC3 custom_animation JSON (additive over Kleiner's in-game idle).
Plays the intro once, then loops the 42 s drink / ash / drag cycle (RestartFrame = loop start)."""
import sys,json,numpy as np
sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/anim','/home/claude/work/retime','/home/claude/tools/scripts','/home/claude/work/build']
import sprops,stimes,sseq,pacgen,gbase,retime, retarget as RT
W={}
for l in open('/mnt/user-data/uploads/V_Gmod/token_pose_idle.txt'):
    n,t,a=l.strip().split('|')
    if t!='nil': W[n]=gbase.ang2m(*map(float,a.split()))
for i,n in enumerate(RT.vn):
    p=RT.vp[i]
    if p>=0 and n in W and RT.vn[p] in W: pacgen.BASE[i]=W[RT.vn[p]].T@W[n]
J,times,keep=pacgen.build(sseq.world_at,sseq.INTRO+sseq.LOOP,sseq.INTRO,fps=15,blend_in=stimes.BLEND,tol=0.6)
J2,info=retime.retime(J)
out=sys.argv[1]; json.dump(J2,open(out,'w'),separators=(',',':'))
print('intro %.2f loop %.1f frames'%(sseq.INTRO,sseq.LOOP),info,'bytes',len(open(out).read()))
