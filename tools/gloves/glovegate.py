"""Glove checks over any set of poses (world matrices): stretch (edges grown > 0.2 in, near the hand) and drift from the skin.
python3 glovegate.py [guitar|finger]"""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/gloves','/home/claude/work/guitar']
import gloves as G, retarget as RT, gtear as T
VB='ValveBiped.Bip01_'
def poses(kind,n=12):
    if kind=='finger':
        import fingertest as FT
        return [[m@RT.NW[i] for i,m in enumerate(FT.pose_bind(t))] for t in np.linspace(0,11,n,endpoint=False)]
    import gseq, vanim
    gseq.install_fretting()
    return [vanim.full_world(vanim.valve_world_rots_W(gseq.world_at(t))) for t in np.linspace(0,gseq.LOOP,n,endpoint=False)]
def grow(parts,NWS):
    nodes={i:n for i,n in enumerate(RT.vn)}; n_=0; worst=0.0
    for p in parts:
        P=p['pos']; F=p['idx']; L=p['lk']; B=np.array([[b for b,_ in l][:4]+[0]*(4-min(4,len(l))) for l in L]); W=np.array([[w for _,w in l][:4]+[0]*(4-min(4,len(l))) for l in L])
        E0=np.stack([np.linalg.norm(P[F[:,i]]-P[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1); g=np.zeros(len(F))
        for NW in NWS:
            Q=T.skin(NW,nodes,P,B,W); E=np.stack([np.linalg.norm(Q[F[:,i]]-Q[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1); g=np.maximum(g,(E-E0).max(1))
        n_+=int((g>0.2).sum()); worst=max(worst,float(g.max()))
    return n_,round(worst,2)
if __name__=='__main__':
    NWS=poses(sys.argv[1] if len(sys.argv)>1 else 'guitar')
    for wo in (False,True):
        G.WRIST_OWN=wo; out={}
        for s in 'lr': out[s]=dict(stretch=grow(G.glove(s),NWS),drift=G.drift(NWS,s))
        print('WRIST_OWN',wo,out)
