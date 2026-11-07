"""Token whiskey stance -> PAC3 custom_animation JSON (additive over Kleiner's in-game idle)."""
import sys,json,numpy as np
sys.path[:0]=['/home/claude/work/drink','/home/claude/work/anim','/home/claude/work/retime','/home/claude/tools/scripts','/home/claude/work/build']
import pacgen,gbase,dseq,retime, retarget as RT
# base = Kleiner's own idle, dumped in game (token_pose_idle.txt: bone|pos|angles in player space)
W={}
for l in open('/mnt/user-data/uploads/V_Gmod/token_pose_idle.txt'):
    n,t,a=l.strip().split('|')
    if t!='nil': W[n]=gbase.ang2m(*map(float,a.split()))
nb=0
for i,n in enumerate(RT.vn):
    p=RT.vp[i]
    if p>=0 and n in W and RT.vn[p] in W: pacgen.BASE[i]=W[RT.vn[p]].T@W[n]; nb+=1
print('base bones from Kleiner idle:',nb)
J,times,keep=pacgen.build(dseq.world_at,dseq.LOOP,0.0,fps=15,blend_in=0.6,tol=0.6)
J2,info=retime.retime(J)
out=sys.argv[1]; json.dump(J2,open(out,'w'),separators=(',',':'))
print('frames',info,'bytes',len(open(out).read()))
