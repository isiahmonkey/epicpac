"""Render frames of the smoking timeline on Token (outfit2) with the props visible at each moment."""
import sys,os,re,numpy as np
sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/pbr']
import prev2 as P, sseq, sprops, stimes, glb
from PIL import Image
K=P.K
PROPS={m:P.load(K+'modelsrc/%s_body.smd'%m) for m in ('token_sm_glass','token_sm_cig','token_sm_cig_smoke','token_sm_cig_mouth','token_sm_zippo','token_sm_zippo_open')}
class Clip:
    def world(self,t): return sseq.world_at(t)
def visible(t):
    import stimes; return stimes.props_at(t)
def build(times,out,gap=36.0,hide_hat=True):
    G=glb.GLB(); MAT={}; c=Clip()
    meshes=dict((k,v) for k,v in P.MESH.items() if not (hide_hat and 'hat' in k))
    for fi,t in enumerate(times):
        M=P.pose_mats(c,t); show=visible(t)
        allm=list(meshes.items())+[(m,v) for pm in show for m,v in PROPS[pm].items()]
        for m,(Pp,N,UV,B,W) in allm:
            if m not in MAT:
                base=re.sub(r'_L\d+$','',m); tp=K+'materialsrc/%s.tga'%base; im=Image.open(tp).convert('RGBA') if os.path.exists(tp) else None
                vm=open(K+'materials/%s.vmt'%m).read() if os.path.exists(K+'materials/%s.vmt'%m) else ''
                a='BLEND' if '$translucent' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
                MAT[m]=G.material(m,base=im,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=0.3 if 'envmap' in vm else 0.7,metal=0.6 if 'envmap' in vm else 0)
            p,n=P.skinned(M,Pp,N,B,W); p=p+np.array([gap*fi,0,0])
            p=np.stack([-p[:,1],p[:,0],p[:,2]],1)/39.37; n=np.stack([-n[:,1],n[:,0],n[:,2]],1)
            G.mesh('%s_%d'%(m,fi),p,np.arange(len(p)),UV,MAT[m],normals=n)
    G.save(out)
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[2].split(',')]; build(ts,sys.argv[1])
