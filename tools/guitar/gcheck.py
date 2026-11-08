"""Hand / guitar checker for Token's guitar stance (Token's real skinned meshes on the posed Kleiner skeleton).
Per sampled frame:
  collision   hand-mesh vertices inside the guitar (signed distance to a densely sampled guitar surface)
  contact     each fret-hand fingertip's distance to the fingerboard, and whether the neck sits between thumb and fingers
  mapping     angle between each Valve finger bone and the Cyberpunk finger segment it is meant to copy
  strumming   pick-point motion across the strings over the pickups (strokes per second, string-plane crossings)
python3 gcheck.py [label]  -> report on stdout + gcheck_<label>.json"""
import sys,json,numpy as np
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/pbr','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
import prev2 as P, gseq, gprops, cpanim, vanim, retarget as RT
from scipy.spatial import cKDTree
K=P.K; VB='ValveBiped.Bip01_'
import os
if os.environ.get('BASEDIR'):
    P.MESH={}
    for f in P.FILES:
        f2=os.path.join(os.environ['BASEDIR'],os.path.basename(f)) if os.path.basename(f).startswith('token_base_') else f
        for m,v in P.load(f2).items(): P.MESH[m]=[np.concatenate([a,b]) for a,b in zip(P.MESH[m],v)] if m in P.MESH else v
if os.environ.get('HANDS','d')=='d':
    # hand D (Cyberpunk's base hand, approved) with the Judy tuner gloves, in place of the Gorilla arm skin
    for k in [k for k in P.MESH if k=='token_arms' or k.startswith('token_ga_')]: P.MESH.pop(k)
    for f in ('token_handsd_body.smd','token_gloves_body.smd'):
        for m,v in P.load(os.path.join(os.environ.get('HANDDIR',K+'modelsrc'),f)).items(): P.MESH[m]=v
if os.environ.get('FRET','1')=='1': gseq.install_fretting()
NODES={v:k for k,v in P.nodes.items()}
# ------------------------------------------------------------ guitar surface (item space, m) sampled every ~2 mm
GT=gprops.GP; GI=np.asarray(gprops.GM['idx']).reshape(-1,3)
def _surface(step=0.002):
    A,B,C=GT[GI[:,0]],GT[GI[:,1]],GT[GI[:,2]]; n=np.cross(B-A,C-A); ar=np.linalg.norm(n,axis=1)/2; nn=n/np.maximum(2*ar,1e-12)[:,None]
    pts=[];nor=[]
    for a,b,c,f,s in zip(A,B,C,nn,ar):
        k=max(1,int(s/(step*step)*2))
        r=np.random.default_rng(len(pts)).random((k,2)); m=r.sum(1)>1; r[m]=1-r[m]
        pts.append(a+(b-a)*r[:,:1]+(c-a)*r[:,1:]); nor.append(np.repeat(f[None],k,0))
    return np.vstack(pts+[GT]),np.vstack(nor+[np.zeros_like(GT)])
SURF,SNRM=_surface()
# make normals point outward: away from the guitar's local centre line (the item z axis through the slab)
_c=SURF.copy(); _c[:,2]=SURF[:,2]; _cen=np.c_[np.zeros(len(SURF)),np.zeros(len(SURF)),SURF[:,2]]
_flip=((SURF-_cen)*SNRM).sum(1)<0; SNRM[_flip]*=-1
TREE=cKDTree(SURF)
NECK=(0.53,0.80); BOARD_X=GT[(GT[:,2]>NECK[0])&(GT[:,2]<NECK[1]),0].max()     # fingerboard face (item +x)
_nk=GT[(GT[:,2]>NECK[0])&(GT[:,2]<NECK[1])]; NECK_Y=(float(_nk[:,1].min()),float(_nk[:,1].max())); NECK_DEPTH=0.021   # a real neck is ~21 mm deep
VOX=0.003; _lo=GT.min(0)-0.01; _shape=np.ceil((GT.max(0)+0.01-_lo)/VOX).astype(int)+1
def _solid():
    """occupancy: body = filled between front/back faces per (y,z) column; neck = box under the fingerboard"""
    from scipy import ndimage
    O=np.zeros(_shape,bool); ij=np.floor((SURF-_lo)/VOX).astype(int)
    body=SURF[:,2]<NECK[0]
    for (j,k),grp in __import__('itertools').groupby(sorted(zip(ij[body,1],ij[body,2],ij[body,0])),key=lambda x:(x[0],x[1])):
        xs=[g[2] for g in grp]; O[min(xs):max(xs)+1,j,k]=True
    O=ndimage.binary_closing(O,iterations=2)
    zz=np.arange(_shape[2])*VOX+_lo[2]; yy=np.arange(_shape[1])*VOX+_lo[1]; xx=np.arange(_shape[0])*VOX+_lo[0]
    nz=(zz>=NECK[0])&(zz<=NECK[1]); ny=(yy>=NECK_Y[0])&(yy<=NECK_Y[1]); nx=(xx>=BOARD_X-NECK_DEPTH)&(xx<=BOARD_X)
    O[np.ix_(nx,ny,nz)]=True
    D=ndimage.distance_transform_edt(O)*VOX
    return O,D
SOLID,SDEPTH=_solid()
def depth_of(q):
    ij=np.floor((q-_lo)/VOX).astype(int); ok=((ij>=0)&(ij<_shape)).all(1); d=np.zeros(len(q))
    d[ok]=SDEPTH[ij[ok,0],ij[ok,1],ij[ok,2]]; return d
# ------------------------------------------------------------ Token's hand vertices (dominant bone = hand/finger)
def _hand_verts():
    out={'L':[],'R':[]}
    for m,(Pp,N,UV,B,W) in P.MESH.items():
        dom=B[np.arange(len(B)),W.argmax(1)]
        for s in 'LR':
            ids={NODES[VB+'%s_%s'%(s,b)] for b in ['Hand']+['Finger%d%s'%(f,k) for f in range(5) for k in ('','1','2')] if VB+'%s_%s'%(s,b) in NODES}
            sel=np.isin(dom,list(ids))
            if sel.any(): out[s].append((Pp[sel],N[sel],B[sel],W[sel],dom[sel]))
    return {s:tuple(np.concatenate([x[i] for x in v]) for i in range(5)) for s,v in out.items()}
HV=_hand_verts()
def _finger_id(s):
    Pp=HV[s][0]; nw=lambda b: RT.NW[RT.vn.index(VB+'%s_%s'%(s,b))][:3,3]
    best=np.full(len(Pp),1e9); fid=-np.ones(len(Pp),int)
    for f in range(5):
        a=nw('Finger%d'%f); b=nw('Finger%d2'%f); c=b+(b-nw('Finger%d1'%f))*0.9
        for p0,p1 in ((a,nw('Finger%d1'%f)),(nw('Finger%d1'%f),b),(b,c)):
            ab=p1-p0; u=np.clip(((Pp-p0)@ab)/(ab@ab),0,1); d=np.linalg.norm(Pp-(p0+u[:,None]*ab),axis=1)
            m=d<best; best[m]=d[m]; fid[m]=f
    hb=nw('Hand'); fid[best>1.2]=-1
    # tip = the 12 vertices of each finger farthest from the hand bone in the bind
    out={}
    for f in range(5):
        ix=np.where(fid==f)[0]; far=ix[np.argsort(-np.linalg.norm(Pp[ix]-hb,axis=1))[:12]]; out[f]=far
    return out
def _skin_tips(s):
    """hand D: the end 15% (along the bone) of the skin each Finger_2 bone carries; the glove's rods are not fingertips"""
    if os.environ.get('HANDS','d')!='d': return _finger_id(s)
    Pp,N,B,W,dom=HV[s]; out={}
    skin=np.zeros(len(Pp),bool); k=0
    for m,(P_,N_,UV_,B_,W_) in P.MESH.items():
        d_=B_[np.arange(len(B_)),W_.argmax(1)]; ids={NODES[VB+'%s_%s'%(s,b)] for b in ['Hand']+['Finger%d%s'%(f,kk) for f in range(5) for kk in ('','1','2')] if VB+'%s_%s'%(s,b) in NODES}
        n_=int(np.isin(d_,list(ids)).sum()); skin[k:k+n_]=(m=='token_arms'); k+=n_
    for f in range(5):
        n=VB+'%s_Finger%d2'%(s,f); j=RT.vn.index(n); sel=np.where(skin&(dom==NODES[n]))[0]
        x=((Pp[sel]-RT.NW[j][:3,3])@RT.NW[j][:3,:3])[:,0]; out[f]=sel[x>np.percentile(x,85)]
    return out
TIPV={s:_skin_tips(s) for s in 'LR'}
def cp_tips(W,s):
    """Cyberpunk's own fingertips in its guitar (WeaponLeft) frame = guitar item space, m"""
    S={'L':'Left','R':'Right'}[s]; I={n:i for i,n in enumerate(cpanim.NAMES)}; G=np.linalg.inv(W[I['WeaponLeft']]); out={}
    for f,nm in enumerate(('Thumb','Index','Middle','Ring','Pinky')):
        if nm=='Thumb': a,b=S+'HandThumb1',S+'HandThumb2'; tip=W[I[b]][:3,3]+(W[I[b]][:3,3]-W[I[a]][:3,3])*0.9
        else: a,b=S+'Hand%s2'%nm,S+'Hand%s3'%nm; tip=W[I[b]][:3,3]+(W[I[b]][:3,3]-W[I[a]][:3,3])*0.9
        out[FN[f]]=gseq.cp_to_item((G@np.r_[tip,1])[:3])
    return out
TIPB={s:{f:NODES[VB+'%s_Finger%d2'%(s,f)] for f in range(5)} for s in 'LR'}
FN=['thumb','index','middle','ring','pinky']
def to_item(M,p):
    """posed Valve inches -> guitar item space (m)"""
    G=M[NODES[VB+'Spine4']]@gseq.G_BIND; q=(np.linalg.inv(G)@np.c_[p,np.ones(len(p))].T).T[:,:3]
    return (RT.C.T@(q/RT.S).T).T
class _C:
    def __init__(s,f): s.f=f
    def world(s,t): return s.f(t)
def frame(world_at,t):
    W=world_at(t); M=P.pose_mats(_C(lambda _:W),t); r={'t':round(t,2)}
    for s in 'LR':
        Pp,N,B,Wt,dom=HV[s]; p,_=P.skinned(M,Pp,N,B,Wt); q=to_item(M,p)
        dep=depth_of(q); inside=dep>0.0025
        r[s+'_inside']=int(inside.sum()); r[s+'_depth_mm']=round(float(dep.max()*1000),1)
        tips={FN[f]:q[ix].mean(0) for f,ix in TIPV[s].items() if len(ix)}
        ct=cp_tips(W,s); r[s+'_tip_err_mm']={k:round(float(np.linalg.norm(tips[k]-ct[k])*1000),1) for k in tips}
        if s=='L': r['L_cp_tip_height_mm']={k:round(float((v[0]-BOARD_X)*1000),1) for k,v in ct.items()}
        r[s+'_tips']={k:[round(float(x),4) for x in v] for k,v in tips.items()}
        if s=='L':
            c={}
            for k,v in tips.items():
                onneck=NECK[0]-0.02<v[2]<NECK[1]+0.02
                c[k]=dict(above_board_mm=round(float((v[0]-BOARD_X)*1000),1),across_mm=round(float(v[1]*1000),1),on_neck=bool(onneck))
            r['L_contact']=c
            th=tips.get('thumb'); fi=[tips[k] for k in ('index','middle','ring','pinky') if k in tips]
            r['L_wrap']=bool(th is not None and th[0]<BOARD_X-0.005 and np.mean([v[0] for v in fi])>BOARD_X-0.012) if fi else False
        else:
            # pick: between thumb tip and index tip
            if 'thumb' in tips and 'index' in tips: r['pick']=[round(float(x),4) for x in (tips['thumb']*0.6+tips['index']*0.4)]
    # bone mapping: Valve finger bone direction vs the CP segment it copies
    R=vanim.valve_world_rots_W(W); I=cpanim.NAMES; CPI={n:i for i,n in enumerate(I)}
    worst=[]
    for s,S in (('L','Left'),('R','Right')):
        for f,nm in ((1,'Index'),(2,'Middle'),(3,'Ring'),(4,'Pinky')):
            for k,(a,b) in enumerate(((S+'Hand%s1'%nm,S+'Hand%s2'%nm),(S+'Hand%s2'%nm,S+'Hand%s3'%nm))):
                vb=VB+'%s_Finger%d%s'%(s,f,['','1'][k]); vc=VB+'%s_Finger%d%s'%(s,f,['1','2'][k])
                if vb not in R: continue
                dv=R[vb]@RT.NL[RT.vn.index(vc)][:3,3]; dc=RT.tov(W[CPI[b]])[:3,3]-RT.tov(W[CPI[a]])[:3,3]
                ang=np.degrees(np.arccos(np.clip(dv@dc/np.linalg.norm(dv)/np.linalg.norm(dc),-1,1))); worst.append((round(float(ang),1),vb.split('_',1)[1]))
    r['map_worst']=sorted(worst,reverse=True)[:3]; r['map_mean']=round(float(np.mean([w for w,_ in worst])),1)
    return r
def strum(frames):
    t=np.array([f['t'] for f in frames if 'pick' in f]); p=np.array([f['pick'] for f in frames if 'pick' in f])
    over=(p[:,2]>0.08)&(p[:,2]<0.40)
    y=p[:,1]; dy=np.diff(y); sg=np.sign(dy); sg=sg[np.abs(dy)>1e-4]; turns=np.sum(sg[1:]!=sg[:-1])
    h=p[:,0]-BOARD_X                                         # height above the string plane (about the fingerboard face)
    cross=np.sum((np.abs(h[:-1])<0.025)&(np.sign(np.diff(y))!=0)&over[:-1])
    return dict(seconds=round(float(t[-1]-t[0]),1),over_pickups=round(float(over.mean()),2),strokes_per_s=round(float(turns/2/(t[-1]-t[0])),2),
                travel_mm=round(float(np.ptp(y)*1000),1),near_strings=round(float((np.abs(h)<0.025).mean()),2),passes=int(cross))
def run(world_at,label,step=0.25,t0=0.0,t1=None):
    t1=gseq.LOOP if t1 is None else t1
    F=[frame(world_at,t) for t in np.arange(t0,t1,step)]
    S=strum(F)
    agg=dict(frames=len(F),L_frames_with_penetration=sum(f['L_inside']>0 for f in F),L_max_depth_mm=max(f['L_depth_mm'] for f in F),
             R_frames_with_penetration=sum(f['R_inside']>0 for f in F),R_max_depth_mm=max(f['R_depth_mm'] for f in F),
             L_wrap_ok=round(float(np.mean([f['L_wrap'] for f in F])),2),
             fingertips_on_board={k:round(float(np.mean([f['L_contact'][k]['on_neck'] and -4<f['L_contact'][k]['above_board_mm']<8 for f in F if k in f['L_contact']])),2) for k in ('index','middle','ring','pinky')},
             mean_tip_height_mm={k:round(float(np.mean([f['L_contact'][k]['above_board_mm'] for f in F if k in f['L_contact']])),1) for k in FN},
             L_tip_err_mm={k:round(float(np.mean([f['L_tip_err_mm'][k] for f in F])),1) for k in FN},
             R_tip_err_mm={k:round(float(np.mean([f['R_tip_err_mm'][k] for f in F])),1) for k in FN},
             cp_tip_height_mm={k:round(float(np.mean([f['L_cp_tip_height_mm'][k] for f in F])),1) for k in FN},
             bone_map_mean_deg=round(float(np.mean([f['map_mean'] for f in F])),1),bone_map_worst=max((w for f in F for w in f['map_worst'])),strum=S)
    json.dump(dict(summary=agg,frames=F),open('/home/claude/work/guitar/gcheck_%s.json'%label,'w'),indent=0)
    return agg
if __name__=='__main__':
    lab=sys.argv[1] if len(sys.argv)>1 else 'before'
    print(json.dumps(run(gseq.world_at,lab),indent=1))
