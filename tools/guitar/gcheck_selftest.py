"""Self-test for gcheck: known points inside/outside the guitar solid, a known fingertip placement, a known stretched triangle."""
import sys,numpy as np; sys.path.insert(0,'/home/claude/work/guitar')
import os; os.environ['FRET']='0'
import gcheck as G, gtear
ok=True
def t(name,cond,val):
    global ok; ok&=bool(cond); print(('PASS' if cond else 'FAIL'),name,val)
yc=(G.NECK_Y[0]+G.NECK_Y[1])/2; bx=G.BOARD_X
d=G.depth_of(np.array([[bx-0.0105,yc,0.65]]))[0]; t('neck centre is inside, ~10 mm deep',0.006<d<0.014,round(d*1000,1))
d=G.depth_of(np.array([[bx+0.005,yc,0.65]]))[0]; t('5 mm above the fingerboard is outside',d==0,d)
d=G.depth_of(np.array([[bx-0.030,yc,0.65]]))[0]; t('30 mm behind the board is outside (behind the neck)',d==0,d)
d=G.depth_of(np.array([[bx-0.002,G.NECK_Y[1]+0.004,0.65]]))[0]; t('4 mm beside the neck edge is outside',d==0,d)
bz=G.GT[G.GT[:,2]<0.3]; mid=np.array([(bz[:,0].min()+bz[:,0].max())/2,0.0,0.2])
d=G.depth_of(mid[None])[0]; t('middle of the body slab is inside',d>0.008,round(d*1000,1))
d=G.depth_of(np.array([[bz[:,0].max()+0.006,0.0,0.2]]))[0]; t('6 mm in front of the body is outside',d==0,d)
# tear metric: a triangle stretched 2x along one edge reads 2.0
P=np.array([[0,0,0],[1,0,0],[0,1,0.]]); Q=np.array([[0,0,0],[2,0,0],[0,1,0.]])
r=max(np.linalg.norm(Q[1]-Q[0])/np.linalg.norm(P[1]-P[0]),1); t('stretch of a 2x edge is 2.0',abs(r-2)<1e-9,r)
print('ALL PASS' if ok else 'SELF-TEST FAILED'); sys.exit(0 if ok else 1)
