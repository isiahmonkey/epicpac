import sys,numpy as np; sys.path[:0]=['/home/claude/work/anim','/home/claude/tools/scripts']
import cpanim,xf
def q_of(M):
    R=M[:3,:3]; w=np.sqrt(max(1+R[0,0]+R[1,1]+R[2,2],1e-12))/2
    if w>1e-3: return np.array([(R[2,1]-R[1,2])/(4*w),(R[0,2]-R[2,0])/(4*w),(R[1,0]-R[0,1])/(4*w),w])
    i=np.argmax(np.diag(R)); j,k=(i+1)%3,(i+2)%3; s=np.sqrt(max(1+R[i,i]-R[j,j]-R[k,k],1e-12))*2
    q=np.zeros(4); q[i]=s/4; q[j]=(R[j,i]+R[i,j])/s; q[k]=(R[k,i]+R[i,k])/s; q[3]=(R[k,j]-R[j,k])/s; return q
def blend(La,Lb,u):
    return [xf.T(xf.q2m(cpanim.nlerp(q_of(a),q_of(b),u)),a[:3,3]*(1-u)+b[:3,3]*u) for a,b in zip(La,Lb)]
ss=lambda x: 0 if x<=0 else 1 if x>=1 else x*x*(3-2*x)
