"""Render Token (outfit 2) playing: gseq pose, token_guitar + token_sm_cig_mouth, one glb per time."""
import sys,os,re,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/pbr']
import prev2 as P, gseq, glb
from PIL import Image
K=P.K
if os.environ.get('FRET','1')=='1': gseq.install_fretting()
if os.environ.get('BASEDIR'):          # swap Token's base meshes for a test build (e.g. unlocked fingers)
    import glob
    P.MESH={}
    for f in P.FILES:
        f2=os.path.join(os.environ['BASEDIR'],os.path.basename(f)) if os.path.basename(f).startswith('token_base_') else f
        for m,v in P.load(f2).items(): P.MESH[m]=[np.concatenate([a,b]) for a,b in zip(P.MESH[m],v)] if m in P.MESH else v
PROPS=['token_guitar','token_sm_cig_mouth']
if os.environ.get('GLOVES')=='1':        # swap the Gorilla hands for the Judy gloves (preview only)
    sys.path[:0]=['/home/claude/work/gloves']
    import basehand as BH, garch, retarget as RT
    BH.TRANSFER=os.environ.get('TRANSFER','0')=='1'
    G={'l':'base\\tq\\meshes\\personal_link\\g1_000_pma_judy_glove_tq_personal_link.mesh','r':'base\\tq\\meshes\\g1_000_pma_judy_glove_r_tq.mesh'}
    for k in [k for k in P.MESH if k.startswith('token_ga_') or 'ga_' in k]: P.MESH.pop(k)
    Hs=[RT.NW[RT.vn.index('ValveBiped.Bip01_%s_Hand'%x)] for x in 'LR']
    for k,(Pp,N,UV,B,W) in list(P.MESH.items()):     # drop anything beyond the wrists (Gorilla knuckle plating)
        if 'arm' not in k and 'cyber' not in k: continue
        keep=np.ones(len(Pp)//3,bool)
        for H in Hs:
            F=np.asarray(H)[:3,3]; ax=H[:3,3]-RT.NW[RT.vn.index('ValveBiped.Bip01_%s_Forearm'%('L' if H is Hs[0] else 'R'))][:3,3]; ax/=np.linalg.norm(ax)
            d=((Pp-H[:3,3])@ax).reshape(-1,3).max(1); keep&=d<0.3
        sel=np.repeat(keep,3); P.MESH[k]=[x[sel] for x in (Pp,N,UV,B,W)]
    for s_ in 'lr':
        for p in [q for q in BH.hand(s_,garch.segs(G[s_])) if q['chunk'] in (0,1,3,4,5,6)]:   # 2 = proxy, 7-9 = cable rig (the mod's own 'toggle' look hides these)
            F=p['idx'].ravel(); Bn=np.array([[b for b,_ in l][:3]+[0]*(3-min(3,len(l))) for l in p['lk']]); Wt=np.array([[w for _,w in l][:3]+[0]*(3-min(3,len(l))) for l in p['lk']])
            P.MESH['glove_%s_%d'%(s_,p['chunk'])]=[p['pos'][F],p['nrm'][F],p['uv'][F],Bn[F],Wt[F]]
        for p in BH.hand_smoothed(s_,8):          # the bare hand under the glove
            F=p['idx'].ravel(); Bn=np.array([[b for b,_ in l][:3]+[0]*(3-min(3,len(l))) for l in p['lk']]); Wt=np.array([[w for _,w in l][:3]+[0]*(3-min(3,len(l))) for l in p['lk']])
            P.MESH['barehand_%s_%d'%(s_,p['chunk'])]=[p['pos'][F],p['nrm'][F],p['uv'][F],Bn[F],Wt[F]]
class Clip:
    def world(self,t): return gseq.world_at(t)
def build(times,out,gap=36.0,hide_hat=True,props=PROPS):
    PM={m:P.load(K+'modelsrc/%s_body.smd'%m) for m in props}
    G=glb.GLB(); MAT={}; c=Clip()
    meshes=dict((k,v) for k,v in P.MESH.items() if not (hide_hat and 'hat' in k))
    for fi,t in enumerate(times):
        M=P.pose_mats(c,t)
        allm=list(meshes.items())+[(m,v) for pm in props for m,v in PM[pm].items()]
        for m,(Pp,N,UV,B,W) in allm:
            if m not in MAT:
                base=re.sub(r'_L\d+$','',m); tp=K+'materialsrc/%s.tga'%base; im=Image.open(tp).convert('RGBA') if os.path.exists(tp) else None
                vm=open(K+'materials/%s.vmt'%m).read() if os.path.exists(K+'materials/%s.vmt'%m) else ''
                a='BLEND' if '$translucent' in vm else ('MASK' if '$alphatest' in vm else 'OPAQUE')
                if m.startswith('token_guitar') and im is not None: im=im.convert('RGB').convert('RGBA')
                if m.startswith('glove_'): im=Image.new('RGBA',(4,4),(22,22,24,255)); a='OPAQUE'
                if m.startswith('barehand_'): im=Image.new('RGBA',(4,4),(92,58,40,255)); a='OPAQUE'
                MAT[m]=G.material(m,base=im,alpha=a,cutoff=0.45,double='$nocull' in vm,rough=(0.55 if m.startswith('token_guitar') else 0.3) if 'envmap' in vm else 0.7,metal=0.0)
            p,n=P.skinned(M,Pp,N,B,W); p=p+np.array([gap*fi,0,0])
            p=np.stack([-p[:,1],p[:,0],p[:,2]],1)/39.37; n=np.stack([-n[:,1],n[:,0],n[:,2]],1)
            G.mesh('%s_%d'%(m,fi),p,np.arange(len(p)),UV,MAT[m],normals=n)
    G.save(out)
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[2].split(',')]; build(ts,sys.argv[1])
