import sys,numpy as np,glob,os
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build']
import retarget as RT
pose=sys.argv[1]; tag=sys.argv[2]
def a2m(p,y,r):
    p,y,r=np.radians([p,y,r]);sp,cp,sy,cy,sr,cr=np.sin(p),np.cos(p),np.sin(y),np.cos(y),np.sin(r),np.cos(r)
    return np.array([[cp*cy,sr*sp*cy-cr*sy,cr*sp*cy+sr*sy],[cp*sy,sr*sp*sy+cr*cy,cr*sp*sy-sr*cy],[-sp,sr*cp,cr*cp]])
C=np.array([[0,1,0],[-1,0,0],[0,0,1.]])
PM={}
for l in open(pose):
    n,t,a=l.strip().split('|')
    if t=='nil': continue
    M=np.eye(4); M[:3,:3]=C@a2m(*map(float,a.split())); M[:3,3]=C@np.array(list(map(float,t.split()))); PM[n]=M
B='/mnt/user-data/outputs/token_build/modelsrc/'
nodes={}
L=open(B+'token_base_bind.smd').read().split('\n'); k=L.index('nodes')+1
while L[k]!='end':
    t=L[k].split('"'); nodes[int(t[0])]=t[1]; k+=1
NW=[np.array(m) for m in RT.NW]
Mk={}
for b,n in nodes.items():
    if n in PM and n in RT.vn: Mk[b]=PM[n]@np.linalg.inv(NW[RT.vn.index(n)])
miss=[n for n in nodes.values() if n not in PM]; print('bones missing in pose',miss)
for f in sorted(glob.glob(B+'token_base_arms*_gorilla_black.smd')):
    src=open(f).read(); head,tri=src.split('triangles\n'); out=[head+'triangles']
    for j,l in enumerate(tri.split('\n')):
        t=l.split()
        if j%4==0 or len(t)<10: out.append(l); continue
        p=np.array(list(map(float,t[1:4]))+[1]); v=np.zeros(4)
        for q in range(int(t[9])): b=int(t[10+2*q]); w=float(t[11+2*q]); v+=w*(Mk.get(b,np.eye(4))@p)
        t[1:4]=['%.5f'%x for x in v[:3]]; out.append(' '.join(t))
    open(B+'zz_%s_%s'%(tag,os.path.basename(f)),'w').write('\n'.join(out))
# hand positions for camera
for sd in 'LR':
    h=PM['ValveBiped.Bip01_%s_Hand'%sd][:3,3]; print(sd,'hand ours',h.round(2),'-> cam target (tx,ty,tz)',round(-h[1]/39.37*-1,3))
    P=np.array([-h[1],h[0],h[2]])/39.37; print('  CP-like',P.round(3),'glTF target',(P[0],P[2],-P[1]))
