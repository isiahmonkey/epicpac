"""Read Token's kit SMDs back (Valve space, inches) and render a bind-pose preview -> proves retarget + UVs + materials."""
import sys,os,numpy as np; sys.path[:0]=['/home/claude/work/pbr']
import glb
from PIL import Image
K='/mnt/user-data/outputs/token_kit/'
def read_smd(p):
    L=open(p).read().split('\n'); i=L.index('triangles') if 'triangles' in L else None; out={}
    if i is None: return out
    j=i+1
    while j<len(L) and L[j]!='end':
        m=L[j]; vs=[L[j+1+k].split() for k in range(3)]; j+=4
        d=out.setdefault(m,[[],[],[]])
        for v in vs: d[0].append([float(v[1]),float(v[2]),float(v[3])]); d[1].append([float(v[7]),1-float(v[8])]); d[2].append([float(v[4]),float(v[5]),float(v[6])])
    return out
def build(files,out):
    G=glb.GLB(); M={}
    for f in files:
        for m,(P,U,N) in read_smd(K+'modelsrc/'+f).items():
            P=np.array(P)/39.37; P=np.stack([-P[:,1],P[:,0],P[:,2]],1); U=np.array(U); N=np.array(N); N=np.stack([-N[:,1],N[:,0],N[:,2]],1)   # Valve (x fwd, y left, z up, inches) -> CP-like (x right, y fwd, z up, m); glb writer maps to glTF
            if m not in M:
                t=K+'materialsrc/%s.tga'%m; im=Image.open(t).convert('RGBA') if os.path.exists(t) else None
                vm=open(K+'materials/%s.vmt'%m).read() if os.path.exists(K+'materials/%s.vmt'%m) else ''
                a='BLEND' if '$translucent' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
                M[m]=G.material(m,base=im,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=0.3 if 'envmap' in vm else 0.7,metal=0.8 if 'envmap' in vm else 0)
            idx=np.arange(len(P))
            G.mesh(m,P,idx,U,M[m],normals=N)
    G.save(out)
if __name__=='__main__': build(sys.argv[2:],sys.argv[1])
