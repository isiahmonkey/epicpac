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
STICKER_LIFT=0.015   # in: sticker drawn this far above the band (it z-fought with the screen and band)
RIGID_MAX=2.0     # in: pieces up to this size move as one solid part ...
OWN=False         # True: the glove's own Cyberpunk weights (retargeted like the hand) instead of copying the skin's
SMOOTH=8          # weight smoothing passes over the glove mesh
RIGID_ONE=0.85    # ... if at least this share of their skin weight is on one bone
def d_settings():
    handfit.THUMB_FIT=False; BH.THENAR=True
def hand_D(side):
    d_settings(); return BH.hand_smoothed(side,8,cut=False)
def _flat(parts):
    P=np.vstack([p['pos'] for p in parts]); N=np.vstack([p['nrm'] for p in parts]); L=[l for p in parts for l in p['lk']]; return P,N,L
CHAIN=True        # copy skin weights within the same finger only
WRIST_OWN=False   # wrist unit keeps the glove's own weights (see fitted)
def _chain(b):
    n=RT.vn[b]
    return int(n[n.index('Finger')+6]) if 'Finger' in n else -1
def fitted(side,path,chunks=None):
    d_settings(); BH.TRANSFER=False
    parts=[p for p in BH.hand(side,garch.segs(path)) if chunks is None or p['chunk'] in chunks]
    HP,HN,HL=_flat(hand_D(side)); tree=cKDTree(HP)
    hch=np.array([_chain(max(l,key=lambda t:t[1])[0]) for l in HL]); _ct={}
    def chain_tree(c):
        if c not in _ct:
            src=np.where(hch==c)[0]
            if len(src)<20: src=np.arange(len(HP))
            _ct[c]=(cKDTree(HP[src]),src)
        return _ct[c]
    from scipy.sparse import coo_matrix; from scipy.sparse.csgraph import connected_components
    for p in parts:
        _,nn=tree.query(p['pos']); lk=list(p['lk']) if OWN else [HL[k] for k in nn]
        if WRIST_OWN and not OWN:
            # wrist unit (band, screen, cuff): the glove's own artist weights, which keep it a hard ring over the wrist;
            # copied skin weights bent it with the wrist (stretched up to 0.55 in in the guitar loop)
            own_dom=np.array([_chain(max(l,key=lambda t:t[1])[0]) for l in p['lk']])
            WR=own_dom==-1
        else: WR=None
        if CHAIN and not OWN:
            # copy skin weights only from the same finger the glove's own weights put this vertex on: a glove triangle
            # copied from two different fingers tore (up to 105x stretch, gloves.stretch)
            own=np.array([_chain(max(l,key=lambda t:t[1])[0]) for l in p['lk']])
            for c in np.unique(own):
                sel=np.where(own==c)[0]; t,src=chain_tree(c)
                _,k=t.query(p['pos'][sel])
                for i,kk in zip(sel,k): lk[i]=HL[src[kk]]
        if SMOOTH:   # neighbours copied from different fingers tore the glove apart (gloves.stretch): smooth over the glove's own welded mesh
            w=BH.weld_index(p['pos'],p['idx']); lkw=[None]*(w.max()+1)
            for i,l in enumerate(lk):
                if lkw[w[i]] is None: lkw[w[i]]=l
            lkw=BH.smooth_links(w[p['idx']],lkw,SMOOTH); lk=[lkw[w[i]] for i in range(len(lk))]
        # hardware pieces (plates, bars, buttons) move solid with one weight set, the way a rigid part would;
        # big pieces (the glove body hugging the skin) keep the skin's own weights
        if WR is not None and WR.any():
            for i in np.where(WR)[0]: lk[i]=p['lk'][i]
        P=p['pos']; F=p['idx']; key=np.round(P/1e-3).astype(np.int64); _,w=np.unique(key,axis=0,return_inverse=True); w=w.ravel(); Fw=w[F]; n=w.max()+1
        g=coo_matrix((np.ones(Fw.size),(np.r_[Fw[:,0],Fw[:,1],Fw[:,2]],np.r_[Fw[:,1],Fw[:,2],Fw[:,0]])),shape=(n,n))
        _,lab=connected_components(g,directed=False); vl=lab[w]
        for c in np.unique(vl):
            ix=np.where(vl==c)[0]
            if np.ptp(P[ix],0).max()>RIGID_MAX: continue
            acc={}
            for i in ix:
                for b,x in lk[i]: acc[b]=acc.get(b,0)+x
            # only a piece that sits on ONE bone moves solid; a piece across a knuckle keeps the skin's weights (a rigid
            # 2-bone blend left finger rods up to 3 in off the finger when it curled: gloves.drift)
            top=sorted(acc.items(),key=lambda t:-t[1]); tot=sum(x for _,x in top)
            if top[0][1]/tot<RIGID_ONE: continue
            for i in ix: lk[i]=[(top[0][0],1.0)]
        p['lk']=lk
    return parts
def glove(side):
    """glove body (chunk 0) fitted to the skin; the screen and decals (other chunks) take the weights of the body point
    they sit on, so they ride it exactly instead of sliding over or under it"""
    ps=fitted(side,GLOVE[side],WORN); body=[p for p in ps if p['chunk']==0]
    BP,_,BL=_flat(body); t=cKDTree(BP)
    for p in ps:
        if p['chunk']!=0: _,k=t.query(p['pos']); p['lk']=[BL[i] for i in k]
    return ps
def sticker(side):
    """the sticker sits on the wrist band: it takes the band's weights (nearest glove vertex), so the two cannot part"""
    d_settings(); BH.TRANSFER=False
    parts=BH.hand(side,garch.segs(STICKER[side])); GP,GN,GL=_flat(glove(side)); t=cKDTree(GP)
    for p in parts: _,k=t.query(p['pos']); p['lk']=[GL[i] for i in k]; p['pos']=p['pos']+p['nrm']*STICKER_LIFT
    return parts
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
def drift(NWs,side,parts=None):
    """how far each glove vertex moves away from the skin point it sat on in the bind (inches): the glove should ride
    the hand. Fixed bind pairing, so no nearest-point jumps (the sink metric above re-pairs every frame and can jump)."""
    import gtear as T
    nodes={i:n for i,n in enumerate(RT.vn)}
    def arr(ps):
        P,N,L=_flat(ps); B=np.array([[b for b,_ in l][:4]+[0]*(4-min(4,len(l))) for l in L]); W=np.array([[w for _,w in l][:4]+[0]*(4-min(4,len(l))) for l in L]); return P,B,W
    hp,hb,hw=arr(hand_D(side)); gp,gb,gw=arr(parts if parts is not None else glove(side))
    # pair each glove point with the nearest skin of the SAME finger (pairing across fingers measured the gap between
    # two fingers opening, not the glove leaving the skin)
    ch=lambda B,W: np.array([_chain(b[w.argmax()]) for b,w in zip(B,W)])
    hc,gc=ch(hb,hw),ch(gb,gw); d0=np.full(len(gp),9.0); i0=np.zeros(len(gp),int)
    for c in np.unique(gc):
        src=np.where(hc==c)[0]; sel=np.where(gc==c)[0]
        if len(src)<20: continue
        dd,k=cKDTree(hp[src]).query(gp[sel]); d0[sel]=dd; i0[sel]=src[k]
    near=d0<0.6         # glove points lying on the skin (frame and rods further out are rigid hardware)
    worst=np.zeros(len(gp))
    for NW in NWs:
        hq=T.skin(NW,nodes,hp,hb,hw); gq=T.skin(NW,nodes,gp,gb,gw)
        off0=gp-hp[i0]; offt=gq-hq[i0]
        worst=np.maximum(worst,np.abs(np.linalg.norm(offt,axis=1)-np.linalg.norm(off0,axis=1)))
    w=worst[near]
    return dict(on_skin=int(near.sum()),drift_p99_in=round(float(np.percentile(w,99)),3),drift_max_in=round(float(w.max()),3),over_quarter_in=int((w>0.25).sum()))
def stretch(NWs,side):
    """worst edge stretch/compression of the glove (ratio), small edges ignored"""
    import gtear as T
    nodes={i:n for i,n in enumerate(RT.vn)}; ps=glove(side); worst=1.0; bad=0
    for p in ps:
        P=p['pos']; F=p['idx']; L=p['lk']; B=np.array([[b for b,_ in l][:4]+[0]*(4-min(4,len(l))) for l in L]); W=np.array([[w for _,w in l][:4]+[0]*(4-min(4,len(l))) for l in L])
        E0=np.stack([np.linalg.norm(P[F[:,i]]-P[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1); w=np.ones(len(F))
        for NW in NWs:
            Q=T.skin(NW,nodes,P,B,W); E=np.stack([np.linalg.norm(Q[F[:,i]]-Q[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1)
            r=E/np.maximum(E0,1e-6); w=np.maximum(w,np.where(E0>0.02,np.maximum(r,1/np.maximum(r,1e-6)),1).max(1))
        worst=max(worst,float(w.max())); bad+=int((w>1.6).sum())
    return dict(worst_stretch=round(worst,2),tris_over_1_6x=bad)
