"""Cyberpunk's base male hands, retargeted onto Token's Kleiner skeleton with the per-part hand fit, cut at the wrist.
Gate: bone mapping + tearing over the guitar loop, compared with the shipped Gorilla hands."""
import sys,numpy as np
sys.path[:0]=['/home/claude/work/token','/home/claude/work/guitar','/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/anim']
import cr2w, mesh, retarget as RT, handfit
VB='ValveBiped.Bip01_'
A='/mnt/user-data/uploads/characters/common/player_base_bodies/player_man_average/arms_hq/a0_000_pma_base_hq__%s.mesh'
def thumb_rename(n):
    """Cyberpunk's thumb has two joints (Thumb1, Thumb2) that sit on Kleiner's Finger01 / Finger02 (0.24 / 0.44 in).
    The shared mapping puts Thumb1 on Finger0, 1.6 in back in the palm, which pushed the thumb into the hand. Renaming them
    Thumb2 / Thumb3 lands them on Finger01 / Finger02 through the existing map."""
    for S in ('Left','Right'):
        if n==S+'HandThumb2': return S+'HandThumb3'
        if n==S+'HandThumb1': return S+'HandThumb2'
    return n
_BASEBP={}
TRANSFER=True
THENAR=True
_BASEW={}
def _base_weights(side):
    """base hand vertices (CP bind) with their smoothed weights by bone NAME"""
    if side not in _BASEW:
        g=mesh.decode(cr2w.load_loose(A%side)); P=[];L=[]
        for s in g['subs']:
            ji=np.asarray(s['ji']); jw=np.asarray(s['jw'],float); F=np.asarray(s['idx']).reshape(-1,3)
            lk=[[(g['bones'][j],w) for j,w in zip(a,b) if w>0] for a,b in zip(ji,jw)]
            # smooth in CP bone space so the glove inherits the same joint bands as the bare hand
            names=sorted({n for l in lk for n,_ in l}); ix={n:i for i,n in enumerate(names)}
            sm=smooth_links(F,[[(ix[n],w) for n,w in l] for l in lk],8)
            P.append(np.asarray(s['pos'],float)); L+=[[(names[b],w) for b,w in l] for l in sm]
        from scipy.spatial import cKDTree
        _BASEW[side]=(cKDTree(np.vstack(P)),L)
    return _BASEW[side]
def _transfer(g,side):
    """clothing rule: every glove vertex takes the skin weights of the nearest bare-hand vertex, so the glove bends exactly like the hand"""
    tree,L=_base_weights(side); B=list(g['bones']); bi={n:i for i,n in enumerate(B)}
    for s in g['subs']:
        _,nn=tree.query(np.asarray(s['pos'],float)); ji=np.zeros((len(nn),4),int); jw=np.zeros((len(nn),4))
        for v,k in enumerate(nn):
            for c,(n,w) in enumerate(L[k][:4]): ji[v,c]=bi.get(n,bi[('Left' if side=='l' else 'Right')+'Hand']); jw[v,c]=w
        s['ji']=ji; s['jw']=jw
def base_bonepos(side):
    if side not in _BASEBP:
        g=mesh.decode(cr2w.load_loose(A%side)); _BASEBP[side]=dict(zip([thumb_rename(n) for n in g['bones']],np.asarray(g['bonepos'],float)))
    return _BASEBP[side]
def hand(side,segs=None):
    """segs: a garment on the hand (glove). Garment meshes are modelled on the player's base hand, but modded ones can carry a
    stale bone bind (the Judy gloves' joints sit ~5 cm off their own vertices), so the base hand's joints are used for every bone it has."""
    g=mesh.decode(segs if segs is not None else cr2w.load_loose(A%side)); out=[]
    g['bones']=[thumb_rename(n) for n in g['bones']]
    if segs is not None:
        bb=base_bonepos(side); g['bonepos']=[bb.get(b,p) for b,p in zip(g['bones'],g['bonepos'])]
        if TRANSFER: _transfer(g,side)
    for k,s in enumerate(g['subs']):
        P,N,lk=handfit.retarget(np.asarray(s['pos'],float),np.asarray(s.get('nrm'),float)[:,:3],np.asarray(s['ji']),np.asarray(s['jw']),g['bones'],g['bonepos'])
        if THENAR: lk=thenar_links(P,lk,side)
        out.append(dict(pos=P,nrm=N,lk=lk,idx=np.asarray(s['idx']).reshape(-1,3),uv=np.asarray(s['uv0']),chunk=s.get('chunk',k)))
    return out
THENAR_R=1.1      # in: reach of the thumb-base (Finger0) weights over the ball of the thumb and the web
def thenar_links(P,lk,side,R=THENAR_R):
    """Kleiner's thumb base bone (Finger0) moves ~31 deg in the idle, but Cyberpunk's hand has no thumb-metacarpal weights,
    so the thumb swung while the ball of the thumb and the web stayed on the hand: the web flap. Hand weight near the
    Finger0->Finger01 segment is handed to Finger0 with a smooth falloff, the way Valve hands are weighted."""
    S=side.upper(); i0=RT.vn.index(VB+S+'_Finger0'); i1=RT.vn.index(VB+S+'_Finger01'); ih=RT.vn.index(VB+S+'_Hand')
    a=RT.NW[i0][:3,3]; b=RT.NW[i1][:3,3]; ab=b-a
    u=np.clip(((P-a)@ab)/(ab@ab),-0.6,1.0); d=np.linalg.norm(P-(a+u[:,None]*ab),axis=1)
    f=np.clip(1-d/R,0,1); f=f*f*(3-2*f)
    out=[]
    for l,fv in zip(lk,f):
        w=dict(l)
        if fv>0 and ih in w:
            mv=w[ih]*fv; w[ih]-=mv; w[i0]=w.get(i0,0)+mv
        top=sorted(w.items(),key=lambda x:-x[1])[:3]; s_=sum(x for _,x in top); out.append([(b_,x/s_) for b_,x in top if x>1e-4])
    return out
def wrist_cut(parts,side,margin=0.6):
    """keep triangles at or beyond the wrist (hand side), like the Gorilla hand did"""
    H=RT.NW[RT.vn.index(VB+side.upper()+'_Hand')]; F=RT.NW[RT.vn.index(VB+side.upper()+'_Forearm')]
    ax=(H[:3,3]-F[:3,3]); ax/=np.linalg.norm(ax); out=[]
    for p in parts:
        d=(p['pos']-H[:3,3])@ax; keep=(d[p['idx']]>-margin).all(1)
        if keep.any(): q=dict(p); q['idx']=p['idx'][keep]; out.append(q)
    return out
if __name__=='__main__':
    import gtear as T, gseq, vanim, collections
    gseq.install_fretting()
    NWs=[vanim.full_world(vanim.valve_world_rots_W(gseq.world_at(t))) for t in np.linspace(0,gseq.LOOP,16,endpoint=False)]
    nodes={i:n for i,n in enumerate(RT.vn)}
    tot={'tris':0,'torn':0,'worst':1.0,'map_bad':[]}
    for s in 'lr':
        parts=wrist_cut(hand(s),s)
        for p in parts:
            P=p['pos']; F=p['idx']; Bn=np.array([[b for b,_ in l]+[0]*(4-len(l)) for l in p['lk']]); Wt=np.array([[w for _,w in l]+[0]*(4-len(l)) for l in p['lk']])
            E0=np.stack([np.linalg.norm(P[F[:,a]]-P[F[:,b]],axis=1) for a,b in ((0,1),(1,2),(2,0))],1); worst=np.ones(len(F))
            for NW in NWs:
                Q=T.skin(NW,nodes,P,Bn,Wt); E=np.stack([np.linalg.norm(Q[F[:,a]]-Q[F[:,b]],axis=1) for a,b in ((0,1),(1,2),(2,0))],1)
                r=E/np.maximum(E0,1e-6); worst=np.maximum(worst,np.where(E0>0.02,np.maximum(r,1/np.maximum(r,1e-6)),1).max(1))
            tot['tris']+=len(F); tot['torn']+=int((worst>1.6).sum()); tot['worst']=max(tot['worst'],round(float(worst.max()),2))
            dom=Bn[np.arange(len(Bn)),Wt.argmax(1)]
            for f in range(5):
                for k in ('','1','2'):
                    n=VB+'%s_Finger%d%s'%(s.upper(),f,k); i=RT.vn.index(n); sel=dom==i
                    if sel.sum()<20: continue
                    q=(P[sel]-RT.NW[i][:3,3])@RT.NW[i][:3,:3]; r_=np.linalg.norm(q[:,1:],axis=1)
                    if np.median(r_)>0.75 or (r_>1).mean()>0.1: tot['map_bad'].append('%s off-axis med %.2f, >1in %.0f%%'%(n[17:],np.median(r_),100*(r_>1).mean()))
    print(tot)
def smooth_links(F,lk,iters=8,keep=3):
    """Laplacian smoothing of skin weights wherever neighbouring vertices disagree (spreads each joint's bend over a wider band)"""
    n=len(lk); nb=[set() for _ in range(n)]
    for a,b,c in F: nb[a]|={b,c}; nb[b]|={a,c}; nb[c]|={a,b}
    W=[dict(l) for l in lk]
    act=[i for i in range(n) if any(set(W[j])!=set(W[i]) for j in nb[i])]
    for _ in range(iters):
        grow=set(act)
        for i in act: grow|=nb[i]
        act=sorted(grow)
    for _ in range(iters):
        new={}
        for i in act:
            acc=dict((b,w*0.5) for b,w in W[i].items()); m=len(nb[i]) or 1
            for j in nb[i]:
                for b,w in W[j].items(): acc[b]=acc.get(b,0)+0.5*w/m
            new[i]=acc
        for i,acc in new.items():
            top=sorted(acc.items(),key=lambda x:-x[1])[:keep]; s=sum(w for _,w in top); W[i]=dict((b,w/s) for b,w in top)
    return [list(w.items()) for w in W]
def weld_index(P,F,tol=1e-4):
    """UV seams split vertices: smoothing must see welded neighbours"""
    key=np.round(P/tol).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); return inv.ravel()
def hand_smoothed(side,iters=8,segs=None,cut=True):
    out=[]
    for p in (wrist_cut(hand(side,segs),side) if cut else hand(side,segs)):
        w=weld_index(p['pos'],p['idx']); Fw=w[p['idx']]; m=w.max()+1
        lkw=[None]*m
        for i,l in enumerate(p['lk']):
            if lkw[w[i]] is None: lkw[w[i]]=l
        lkw=smooth_links(Fw,lkw,iters); q=dict(p); q['lk']=[lkw[w[i]] for i in range(len(p['lk']))]; out.append(q)
    return out
