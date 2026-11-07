"""Bone-mapping check for Token's hands: for every finger bone, where the vertices weighted to it sit in that bone's own
frame in the bind (x = along the bone). A correct mapping puts them at 0 < x < bone length, close to the axis.
python3 gmap.py <modelsrc dir> [plot.png]"""
import sys,numpy as np; sys.path.insert(0,'/home/claude/work/guitar')
import gtear as T, retarget as RT
VB='ValveBiped.Bip01_'
def run(d,png=None):
    nodes=T.nodes_of(d); inv={v:k for k,v in nodes.items()}; P=[];D=[]
    for f in ('token_base_arms_gorilla_black.smd','token_base_arms_cyber_gorilla_black.smd','token_base_arms_plates_l_gorilla_black.smd','token_base_arms_plates_r_gorilla_black.smd'):
        p,b,w,_=T.load(d+'/'+f); P.append(p); D.append(b[np.arange(len(b)),w.argmax(1)])
    p=np.vstack(P); dom=np.concatenate(D); bad=0; rows=[]
    for s in 'LR':
        for f in range(5):
            for k in ('','1','2'):
                n=VB+'%s_Finger%d%s'%(s,f,k); i=RT.vn.index(n); sel=dom==inv[n]
                L=np.linalg.norm(RT.NL[RT.vn.index(VB+'%s_Finger%d%s'%(s,f,{'':'1','1':'2','2':'2'}[k]))][:3,3]) if k!='2' else 1.0
                if not sel.any(): rows.append((n[17:],0,None,None,None)); continue
                q=(p[sel]-RT.NW[i][:3,3])@RT.NW[i][:3,:3]; x=np.median(q[:,0]); r=np.median(np.linalg.norm(q[:,1:],axis=1))
                ok=(-0.3<x<L+0.3) and r<0.75; bad+=not ok; rows.append((n[17:],int(sel.sum()),round(float(x),2),round(float(r),2),'ok' if ok else 'OFF'))
    for r in rows: print('%-10s verts %6d  along %-6s  off-axis %-6s %s'%r)
    print('bones off their mesh:',bad,'of',len(rows)); return bad
if __name__=='__main__': run(sys.argv[1])
