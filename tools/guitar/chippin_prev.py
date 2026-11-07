"""Contact sheet of stand__2h_guitar__pick__01__kerry_chippin__01 on Token (raw clip, no hand fitting)."""
import os,sys; os.environ['FRET']='0'
sys.path.insert(0,'/home/claude/work/guitar')
import gseq, cpanim, gprev
C=cpanim.Clip(gseq._A['stand__2h_guitar__pick__01__kerry_chippin__01'])
gseq.world_at=lambda t: C.world(t)
ts=[float(x) for x in sys.argv[2].split(',')]
gprev.build(ts,sys.argv[1],gap=34.0)
print(round(C.dur,2))
