import sys; sys.path.insert(0,'/home/claude/work/drink')
import preview as PV, dseq as seq
class Clip:
    dur=seq.LOOP
    def world(s,t): return seq.world_at(t)
PV.PROP_SIDE.update(glass='Right',bottle='Left'); PV.REL.update(Right=seq.prop_rel('Right'),Left=seq.prop_rel('Left'))
times=[float(x) for x in sys.argv[2].split(',')]
PV.build(Clip(),times,sys.argv[1],props=('glass','bottle'))
print('ok')
