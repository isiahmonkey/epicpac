"""Token's guitar stance -> PAC3 custom_animation JSON (additive over Kleiner's in-game idle), 72 s seamless loop."""
import sys,json
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/anim','/home/claude/work/retime','/home/claude/tools/scripts','/home/claude/work/build']
import gseq,pacgen,gbase,retime, retarget as RT
W={}
for l in open('/mnt/user-data/uploads/V_Gmod/token_pose_idle.txt'):
    n,t,a=l.strip().split('|')
    if t!='nil': W[n]=gbase.ang2m(*map(float,a.split()))
for i,n in enumerate(RT.vn):
    p=RT.vp[i]
    if p>=0 and n in W and RT.vn[p] in W: pacgen.BASE[i]=W[RT.vn[p]].T@W[n]
BLEND=0.6
J,times,keep=pacgen.build(gseq.world_at,gseq.LOOP,0.0,fps=15,blend_in=BLEND,tol=0.6)
J2,info=retime.retime(J)
out=sys.argv[1]; json.dump(J2,open(out,'w'),separators=(',',':'))
print('loop %.1f s'%gseq.LOOP,info,'frames',len(J2['FrameData']),'restart',J2['RestartFrame'],'bytes',len(open(out).read()))
