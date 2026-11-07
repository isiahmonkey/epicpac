"""Per-part hand fit for Token's Gorilla hands.
The hand meshes are skinned in CP to their OWN bind (fingers relaxed/curled), which differs from the body rig the
retarget uses (up to 2-3 in at the finger joints). Fitting fingers with the body rig's joints rotates every finger about
the wrong pivot. Here every hand bone transform is fitted from the part's own bind joints instead:
  hand    : similarity fit of the part's wrist + 5 finger roots onto Kleiner's
  fingers : each segment rotated/stretched so its root lands on Kleiner's joint and it points along Kleiner's bone
so in Token's bind every finger lies exactly on its Kleiner finger bone and bends about the right knuckle."""
import numpy as np, retarget as RT
VB='ValveBiped.Bip01_'
THUMB_FIT=True    # False: keep Cyberpunk's thumb shape (thumb segments follow the hand fit only)
FN={'0':'Thumb','1':'Index','2':'Middle','3':'Ring','4':'Pinky'}
def _rb(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); c=a@b
    if np.linalg.norm(v)<1e-9: return np.eye(3) if c>0 else -np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]); return np.eye(3)+K+K@K*(1/(1+c))
def _seg(cb,ce,vb,ve):
    """rigid+axial-stretch map of segment cb->ce onto vb->ve"""
    dc=(ce-cb)/np.linalg.norm(ce-cb); R=_rb(ce-cb,ve-vb); sc=np.linalg.norm(ve-vb)/np.linalg.norm(ce-cb)
    Sc=np.eye(3)+(sc-1)*np.outer(dc,dc); M=np.eye(4); M[:3,:3]=R@Sc; M[:3,3]=vb-R@Sc@cb; return M
def part_D(bones,bonepos):
    B=list(bones); raw=lambda n: (RT.C@np.asarray(bonepos[B.index(n)],float))*RT.S
    V=lambda s,n: RT.NW[RT.vn.index(VB+'%s_%s'%(s,n))][:3,3]
    out={}
    for s,S in (('L','Left'),('R','Right')):
        if S+'Hand' not in B: continue
        # hand: similarity (Umeyama) of wrist + finger roots
        keys=[(S+'Hand','Hand')]+[(S+'Hand%s1'%FN[k],'Finger'+k) for k in '01234' if S+'Hand%s1'%FN[k] in B]
        if S+'HandThumb1' not in B and S+'HandThumb2' in B: keys.append((S+'HandThumb2','Finger01'))   # renamed thumb (see basehand.thumb_rename)
        src=np.array([raw(a) for a,_ in keys]); dst=np.array([V(s,b) for _,b in keys]); wts=np.array([25.0]+[1]*(len(keys)-1))
        ms=(src*wts[:,None]).sum(0)/wts.sum(); md=(dst*wts[:,None]).sum(0)/wts.sum(); X=src-ms; Y=dst-md
        U,sv,Vt=np.linalg.svd((Y*wts[:,None]).T@X); E=np.diag([1,1,np.sign(np.linalg.det(U@Vt))]); Rh=U@E@Vt
        scl=(sv*np.diag(E)).sum()/((X**2).sum(1)*wts).sum(); Mh=np.eye(4); Mh[:3,:3]=Rh*scl; Mh[:3,3]=md-Rh@ms*scl
        out[S+'Hand']=Mh
        for n in B:
            if n.startswith(S+'InHand'): out[n]=Mh
        for k,f in FN.items():
            # CP joint number d (1..3) goes on Valve bone d-1 (Finger k, k1, k2). Cyberpunk thumbs only have joints 2 and 3 in
            # this numbering (basehand renames Thumb1/2 -> Thumb2/3: Thumb1 sits on Kleiner's Finger01, 0.24 in away, not Finger0)
            ds=[d for d in (1,2,3) if S+'Hand%s%d'%(f,d) in B]
            if not ds: continue
            vb=['Finger'+k,'Finger%s1'%k,'Finger%s2'%k]
            last=RT.NW[RT.vn.index(VB+'%s_Finger%s2'%(s,k))]
            vtip=V(s,vb[2])+last[:3,:3]@np.array([0.95*np.linalg.norm(RT.NL[RT.vn.index(VB+'%s_Finger%s2'%(s,k))][:3,3]),0,0])
            P=[raw(S+'Hand%s%d'%(f,d)) for d in ds]; P.append(P[-1]+(P[-1]-P[-2])*0.8 if len(P)>1 else P[-1])
            VP=[V(s,vb[d-1]) for d in ds]+[vtip]
            for i,d in enumerate(ds): out[S+'Hand%s%d'%(f,d)]=_seg(P[i],P[i+1],VP[i],VP[i+1]) if (k!='0' or THUMB_FIT) else Mh
    return out
def retarget(pos,nrm,ji,jw,bones,bonepos):
    """RT.retarget with the hand/finger transforms fitted from this part's own bind"""
    loc=part_D(bones,bonepos); keep={n:RT.D[n] for n in loc if n in RT.D}
    try:
        RT.D.update(loc); return RT.retarget(pos,nrm,ji,jw,bones,bonepos)
    finally: RT.D.update(keep)
