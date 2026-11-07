"""Preview CP drinking clips on Token: retarget clip -> Kleiner ValveBiped pose -> skin Token's built SMDs -> glb strip of frames."""
import sys,os,re,glob,numpy as np
sys.path[:0]=['/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/pbr']
import cpanim,vanim,glb, retarget as RT
from PIL import Image
K='/mnt/user-data/outputs/token_build/'
SKIP=('bind','phys','skin_torso','skin_pelvis','skin_thighs','skin_calves','skin_feet','zz_')
FILES=[f for f in sorted(glob.glob(K+'modelsrc/token_base_*.smd')+glob.glob(K+'modelsrc/token_outfit1_*.smd')) if not any(s in f for s in SKIP)]
nodes={}
L=open(K+'modelsrc/token_base_bind.smd').read().split('\n'); k=L.index('nodes')+1
while L[k]!='end':
    t=L[k].split('"'); nodes[int(t[0])]=t[1]; k+=1
def load(f):
    T=open(f).read().split('triangles\n')[1].split('\n'); out={}
    for i in range(0,len(T)-3,4):
        if T[i].strip()=='end': break
        m=T[i]; d=out.setdefault(m,[[],[],[],[],[]])
        for k in (1,2,3):
            t=T[i+k].split(); n=int(t[9]); b=[int(t[10+2*q]) for q in range(n)]+[0]*(3-n); w=[float(t[11+2*q]) for q in range(n)]+[0]*(3-n)
            d[0].append(list(map(float,t[1:4]))); d[1].append(list(map(float,t[4:7]))); d[2].append([float(t[7]),1-float(t[8])]); d[3].append(b[:3]); d[4].append(w[:3])
    return {m:[np.array(x) for x in v] for m,v in out.items()}
MESH={}
for f in FILES:
    for m,v in load(f).items():
        if m in MESH: MESH[m]=[np.concatenate([a,b]) for a,b in zip(MESH[m],v)]
        else: MESH[m]=v
LOCAL_EAR=('token_earring' in str(FILES))
def pose_mats(clip,t):
    NW=vanim.full_world(vanim.valve_world_rots(clip,t))
    M=np.zeros((max(nodes)+1,4,4))
    for b,n in nodes.items():
        M[b]=NW[RT.vn.index(n)]@np.linalg.inv(RT.NW[RT.vn.index(n)]) if n in RT.vn else np.eye(4)
    return M
def skinned(M,P,N,B,W):
    h=np.c_[P,np.ones(len(P))]; out=np.zeros((len(P),3)); on=np.zeros((len(P),3))
    for k in range(3):
        Mb=M[B[:,k]]; out+=W[:,k,None]*np.einsum('nij,nj->ni',Mb[:,:3,:4],h); on+=W[:,k,None]*np.einsum('nij,nj->ni',Mb[:,:3,:3],N)
    return out,on/np.maximum(np.linalg.norm(on,axis=1,keepdims=True),1e-9)
# ---- props on WeaponRight (CP's hand-prop attach point), carried through the same hand fit as the mesh
import garments,mesh as cpmesh
PROP_SIDE={}; REL={}
PROPS={'bottle':'base\\environment\\decoration\\food\\drinks\\drink_bottle\\drink_bottle_m_whiskey.mesh',
       'glass':'base\\environment\\decoration\\dining_accessories\\tableware\\glass\\glass_f_whiskey.mesh'}
def prop_parts(kind):
    m=cpmesh.decode(garments.segs_of(PROPS[kind])); out=[]
    for x in m['subs']:
        P=np.asarray(x['pos'],float); P=(RT.C@P.T).T*RT.S; out.append((P,np.asarray(x['idx']).reshape(-1,3),np.asarray(x['uv0'])))
    return out
def prop_world(clip,t,side='Right'):
    W=clip.world(t); N=cpanim.NAMES; h=W[N.index(side+'Hand')]
    rel=REL[side] if side in REL else np.linalg.inv(h)@W[N.index('Weapon'+side)]; Xbind=RT.D[side+'Hand']@RT.CW[side+'Hand']@RT.tov(rel)
    vb='ValveBiped.Bip01_%s_Hand'%side[0]; i=RT.vn.index(vb)
    NW=vanim.full_world(vanim.valve_world_rots(clip,t)); return NW[i]@np.linalg.inv(RT.NW[i])@Xbind

def build(clip,times,out,gap=36.0,props=()):
    G=glb.GLB(); MAT={}
    PM={k:prop_parts(k) for k in props}
    gl=G.material('pglass',color=(0.75,0.8,0.78,0.25),rough=0.05,alpha='BLEND',double=True); liq=G.material('pliq',color=(0.45,0.2,0.04,0.9),rough=0.1,alpha='BLEND')
    for fi,t in enumerate(times):
        M=pose_mats(clip,t)
        for m,(P,N,UV,B,W) in MESH.items():
            if m not in MAT:
                base=re.sub(r'_L\d+$','',m); tp=K+'materialsrc/%s.tga'%base; im=Image.open(tp).convert('RGBA') if os.path.exists(tp) else None
                vm=open(K+'materials/%s.vmt'%m).read() if os.path.exists(K+'materials/%s.vmt'%m) else ''
                a='BLEND' if '$translucent' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
                MAT[m]=G.material(m,base=im,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=0.3 if 'envmap' in vm else 0.7,metal=0.6 if 'envmap' in vm else 0)
            p,n=skinned(M,P,N,B,W); p=p+np.array([gap*fi,0,0])   # frames side by side across the camera
            p=np.stack([-p[:,1],p[:,0],p[:,2]],1)/39.37; n=np.stack([-n[:,1],n[:,0],n[:,2]],1)
            G.mesh('%s_%d'%(m,fi),p,np.arange(len(p)),UV,MAT[m],normals=n)
        for k in props:
            X=prop_world(clip,t,PROP_SIDE.get(k,'Right'))
            for j,(P,F,UV) in enumerate(PM[k]):
                q=(X[:3,:3]@P.T).T+X[:3,3]+np.array([gap*fi,0,0]); q=np.stack([-q[:,1],q[:,0],q[:,2]],1)/39.37
                G.mesh('%s%d_%d'%(k,j,fi),q,F.ravel(),UV,liq if j==len(PM[k])-1 and len(PM[k])>1 else gl)
    G.save(out)
if __name__=='__main__':
    f,name,out=sys.argv[1],sys.argv[2],sys.argv[3]; nf=int(sys.argv[4]) if len(sys.argv)>4 else 4; props=tuple(sys.argv[5].split(',')) if len(sys.argv)>5 else ()
    A=cpanim.clips(f); c=cpanim.Clip(A[name]); d=c.dur
    build(c,[d*(i+0.5)/nf for i in range(nf)],out,props=props)
    print('ok',name,round(d,1))
