"""Token (outfit1) + blaster posed by an in-game bone dump -> glb"""
import sys,os,re,numpy as np
sys.path[:0]=['/home/claude/work/drink','/home/claude/work/pbr']
import prev2 as P, glb
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build']
import retarget as RT
from PIL import Image
def a2m(p,y,r):
    p,y,r=np.radians([p,y,r]);sp,cp,sy,cy,sr,cr=np.sin(p),np.cos(p),np.sin(y),np.cos(y),np.sin(r),np.cos(r)
    return np.array([[cp*cy,sr*sp*cy-cr*sy,cr*sp*cy+sr*sy],[cp*sy,sr*sp*sy+cr*cy,cr*sp*sy-sr*cy],[-sp,sr*cp,cr*cp]])
C=np.array([[0,1,0],[-1,0,0],[0,0,1.]])
def pose(f):
    PM={}
    for l in open(f):
        n,t,a=l.strip().split('|')
        if t=='nil': continue
        M=np.eye(4); M[:3,:3]=C@a2m(*map(float,a.split())); M[:3,3]=C@np.array(list(map(float,t.split()))); PM[n]=M
    M=np.zeros((max(P.nodes)+1,4,4))
    for b,n in P.nodes.items(): M[b]=PM[n]@np.linalg.inv(RT.NW[RT.vn.index(n)]) if (n in PM and n in RT.vn) else np.eye(4)
    return M
K=P.K
def build(posefile,out,extra=('br_blaster',)):
    M=pose(posefile); G=glb.GLB(); MAT={}
    meshes=list(P.MESH.items())
    for m in extra: meshes+=list(P.load(K+'modelsrc/%s_body.smd'%m).items())
    for m,(Pp,N,UV,B,W) in meshes:
        if 'hat' in m: continue
        vm=open(K+'materials/%s.vmt'%m).read() if os.path.exists(K+'materials/%s.vmt'%m) else ''
        bt=re.search(r'basetexture" "[^"]*/([^"]+)"',vm); base=bt.group(1) if bt else re.sub(r'_L\d+$','',m)
        tp=K+'materialsrc/%s.tga'%base; im=Image.open(tp).convert('RGBA') if os.path.exists(tp) else None
        a='BLEND' if '$translucent' in vm or '$additive' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
        nb=re.search(r'bumpmap" "[^"]*/([^"]+)"',vm); npth=K+'materialsrc/%s.tga'%nb.group(1) if nb else None
        mat=G.material(m,base=im,normal=Image.open(npth).convert('RGB') if npth and os.path.exists(npth) else None,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=0.35 if 'envmap' in vm else 0.7,metal=0.6 if 'envmap' in vm else 0)
        p,n=P.skinned(M,Pp,N,B,W); p=np.stack([-p[:,1],p[:,0],p[:,2]],1)/39.37; n=np.stack([-n[:,1],n[:,0],n[:,2]],1)
        G.mesh(m,p,np.arange(len(p)),UV,mat,normals=n)
    G.save(out)
if __name__=='__main__': build(sys.argv[1],sys.argv[2])
