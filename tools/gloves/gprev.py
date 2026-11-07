"""Close-up render of token_handsd + token_gloves posed like the finger test (sim of the game pose)."""
import sys,os,re,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/drink','/home/claude/tools/scripts']
import prev2 as P, fingertest as FT, render as R
from PIL import Image
K='/mnt/user-data/outputs/token_build/'
MESH={}
for m in ('token_handsd','token_gloves'):
    for k,v in P.load(K+'modelsrc/%s_body.smd'%m).items(): MESH[k]=v
TEX={}
def tex(m):
    if m not in TEX:
        f=K+'materialsrc/%s.tga'%m; TEX[m]=Image.open(f) if os.path.exists(f) else None
    return TEX[m]
def shot(t,yaw,side,out,zoom=1.0):
    M=np.stack(FT.pose_bind(t)); parts=[]
    for m,(Pp,N,UV,B,W) in MESH.items():
        p,n=P.skinned(M,Pp,N,B,W); d=dict(pos=p,idx=np.arange(len(p)),uv=np.c_[UV[:,0],1-UV[:,1]] if False else UV)
        tx=tex(m)
        if tx is not None: d['tex']=tx
        if 'dec' in m or 'kng' in m or 'mlt' in m or 'mtx' in m or 'sticker' in m: d['alpha']=1
        parts.append(d)
    import retarget as RT
    hi=M[RT.vn.index('ValveBiped.Bip01_%s_Hand'%side)]@RT.NW[RT.vn.index('ValveBiped.Bip01_%s_Hand'%side)]
    c=hi[:3,3]+hi[:3,:3]@np.array([2.0,0,0]); e=4.0/zoom
    return R.view(parts,out,yaw=yaw,size=(560,560),focus=(c-e,c+e))
if __name__=='__main__':
    ims=[]
    for t in [float(x) for x in sys.argv[1].split(',')]:
        for side in 'LR':
            for yaw in (0.0,1.57,3.14):
                ims.append(shot(t,yaw,side,None))
    n=6; rows=[ims[i:i+n] for i in range(0,len(ims),n)]
    W=560*n; S=Image.new('RGB',(W,560*len(rows)))
    for r,row in enumerate(rows):
        for c,im in enumerate(row): S.paste(im,(c*560,r*560))
    S.save(sys.argv[2]); print(sys.argv[2])
