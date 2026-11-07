"""Render the finger test: (top) simulated game pose on Token with token_testhands; (bottom) Cyberpunk-rig reference."""
import sys,os,re,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/drink','/home/claude/work/pbr']
import prev2 as P, fingertest as FT, glb, retarget as RT
from PIL import Image
K=P.K
for k in [k for k in P.MESH if 'ga_' in k or 'hat' in k]: P.MESH.pop(k)
# mirror the PAC test outfit exactly: base arms / Gorilla shell / plates hidden, test arms + test hands added (no ad-hoc trimming:
# trimming in the preview is what hid the Gorilla hand stub that showed up in game)
for k in [k for k in list(P.MESH) if 'ga_' in k]: P.MESH.pop(k)
P.MESH={k:v for k,v in P.MESH.items() if k!='token_arms'}   # base arms hidden; the test model carries the whole arm

for m,v in P.load(K+'modelsrc/%s_body.smd'%os.environ.get('HANDS','token_testhands')).items(): P.MESH['test_'+m]=v
def build(times,out,gap=30.0):
    G=glb.GLB(); MAT={}
    for fi,t in enumerate(times):
        M=np.stack(FT.pose_bind(t))
        for m,(Pp,N,UV,B,W) in P.MESH.items():
            base=re.sub(r'^(test_|testarms_)','',re.sub(r'_L\d+$','',m))
            if m not in MAT:
                tp=K+'materialsrc/%s.tga'%base; im=Image.open(tp).convert('RGBA') if os.path.exists(tp) else None
                vm=open(K+'materials/%s.vmt'%base).read() if os.path.exists(K+'materials/%s.vmt'%base) else ''
                a='BLEND' if '$translucent' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
                np_=K+'materialsrc/%s_n.tga'%base
                MAT[m]=G.material(m,base=im,normal=Image.open(np_).convert('RGB') if os.path.exists(np_) else None,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=0.7,metal=0)
            p,n=P.skinned(M,Pp,N,B,W); p=p+np.array([0,gap*fi,0])
            p=np.stack([-p[:,1],p[:,0],p[:,2]],1)/39.37; n=np.stack([-n[:,1],n[:,0],n[:,2]],1)
            G.mesh('%s_%d'%(m,fi),p,np.arange(len(p)),UV,MAT[m],normals=n)
    G.save(out)
if __name__=='__main__': build([float(x) for x in sys.argv[2].split(',')],sys.argv[1])
