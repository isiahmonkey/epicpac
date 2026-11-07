"""Judy tuner gloves (tq mod, 'black' + Street Kid sticker on the left) fitted to Token's approved hand (version D).
The glove takes each vertex's skin weights from the nearest point of the D hand, so glove and hand bend as one piece.
check(): glove vertices that sink into the skin, over the finger test and the guitar loop."""
import sys,os,numpy as np
sys.path[:0]=['/home/claude/work/gloves','/home/claude/work/guitar','/home/claude/work/token','/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/anim']
import garch, basehand as BH, handfit, retarget as RT
from scipy.spatial import cKDTree
GLOVE={'l':'base\\tq\\meshes\\personal_link\\g1_000_pma_judy_glove_tq_personal_link.mesh','r':'base\\tq\\meshes\\g1_000_pma_judy_glove_r_tq.mesh'}
STICKER={'l':'base\\tq\\meshes\\g1_000_pma_judy_glove_sticker_tq_personal_link.mesh','r':'base\\tq\\meshes\\g1_000_pma_judy_glove_sticker_r_tq.mesh'}
WORN=(0,1,3,4,5,6)        # 2 = shadow proxy, 7-9 = the forearm cable rig (the mod's own toggle hides them)
STICKER_SIDE='l'
RIGID_MAX=2.0     # in: pieces up to this size move as one solid part
def d_settings():
    handfit.THUMB_FIT=False; BH.THENAR=True
def hand_D(side):
    d_settings(); return BH.hand_smoothed(side,8,cut=False)
def _flat(parts):
    P=np.vstack([p['pos'] for p in parts]); N=np.vstack([p['nrm'] for p in parts]); L=[l for p in parts for l in p['lk']]; return P,N,L
def fitted(side,path,chunks=None):
    d_settings(); BH.TRANSFER=False
    parts=[p for p in BH.hand(side,garch.segs(path)) if chunks is None or p['chunk'] in chunks]
    HP,HN,HL=_flat(hand_D(side)); tree=cKDTree(HP)
    from scipy.sparse import coo_matrix; from scipy.sparse.csgraph import connected_components
    for p in parts:
        _,nn=tree.query(p['pos']); lk=[HL[k] for k in nn]
        # hardware pieces (plates, bars, buttons) move solid with one weight set, the way a rigid part would;
        # big pieces (the glove body hugging the skin) keep the skin's own weights
        P=p['pos']; F=p['idx']; key=np.round(P/1e-3).astype(np.int64); _,w=np.unique(key,axis=0,return_inverse=True); w=w.ravel(); Fw=w[F]; n=w.max()+1
        g=coo_matrix((np.ones(Fw.size),(np.r_[Fw[:,0],Fw[:,1],Fw[:,2]],np.r_[Fw[:,1],Fw[:,2],Fw[:,0]])),shape=(n,n))
        _,lab=connected_components(g,directed=False); vl=lab[w]
        for c in np.unique(vl):
            ix=np.where(vl==c)[0]
            if np.ptp(P[ix],0).max()>RIGID_MAX: continue
            acc={}
            for i in ix:
                for b,x in lk[i]: acc[b]=acc.get(b,0)+x
            top=sorted(acc.items(),key=lambda t:-t[1])[:2]; sm=sum(x for _,x in top); one=[(b,x/sm) for b,x in top]
            for i in ix: lk[i]=one
        p['lk']=lk
    return parts
def glove(side): return fitted(side,GLOVE[side],WORN)
def sticker(side): return fitted(side,STICKER[side])
def check(NWs,side):
    """worst sink of glove into skin (inches) over the given poses; skin side = against the hand normal"""
    import gtear as T
    nodes={i:n for i,n in enumerate(RT.vn)}
    H=hand_D(side); G=glove(side)+(sticker(side) if side==STICKER_SIDE else [])
    def arr(parts):
        P,N,L=_flat(parts); B=np.array([[b for b,_ in l][:4]+[0]*(4-min(4,len(l))) for l in L]); W=np.array([[w for _,w in l][:4]+[0]*(4-min(4,len(l))) for l in L]); return P,N,B,W
    hp,hn,hb,hw=arr(H); gp,gn,gb,gw=arr(G)
    # bind: how far each glove vertex sits outside the skin
    t0=cKDTree(hp); d0,i0=t0.query(gp); s0=((gp-hp[i0])*hn[i0]).sum(1)
    worst=[]
    for NW in NWs:
        hq=T.skin(NW,nodes,hp,hb,hw); gq=T.skin(NW,nodes,gp,gb,gw)
        M={b:NW[b][:3,:3]@RT.NW[b][:3,:3].T for b in range(len(RT.vn))}
        hnq=np.einsum('nij,nj->ni',np.stack([M[b] for b in hb[:,0]]),hn)
        t=cKDTree(hq); d,i=t.query(gq); s=((gq-hq[i])*hnq[i]).sum(1)
        sink=np.clip(s0-s,0,None)*(s0>-0.05)        # only glove points that started outside the skin
        worst.append(float(sink.max()));
    return dict(glove_verts=len(gp),bind_inside=int((s0<-0.05).sum()),worst_sink_in=round(max(worst),3))
