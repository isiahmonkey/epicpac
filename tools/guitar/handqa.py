"""One gate for Token hand / prop work. Every number has ONE definition, every check compares against the shipped build,
and the run fails (exit 1) on any regression or failed self-test. Nothing gets reported as fixed unless this passes.

python3 handqa.py <candidate modelsrc dir> [--stance guitar] [--frames 24]

Checks
 0 self-test       gcheck geometry/metric self-test must pass, else nothing else is trusted
 1 bone mapping    every finger bone must have mesh on it: median position along the bone in [-0.3, len+0.3] in, off-axis < 0.75 in,
                   and no more than 10% of its vertices more than 1 in off the bone (catches whole shells riding one finger)
                   (a bone with NO vertices fails: that is a frozen finger)
 2 tearing         union over sampled frames of triangles stretched/compressed > TEAR x (edges > 0.02 in), split hand vs arm;
                   also reports the single worst stretch. Candidate must not exceed shipped in either region.
 3 collision       hand vertices inside the guitar solid (max over frames) and deepest penetration (mm)
 4 contact         fretting fingertip (mesh) distance to its target on the fingerboard, mean / max mm
 5 strum           strokes per second of the pick point, must stay within 25% of Cyberpunk's own clip"""
import sys,os,json,subprocess,numpy as np,argparse
sys.path.insert(0,'/home/claude/work/guitar')
SHIPPED='/mnt/user-data/outputs/token_build/modelsrc'
TEAR=1.6; HAND_R=5.0
ap=argparse.ArgumentParser(); ap.add_argument('cand'); ap.add_argument('--stance',default='guitar'); ap.add_argument('--frames',type=int,default=24)
a=ap.parse_args()
R={'candidate':a.cand,'stance':a.stance}; fails=[]
def fail(msg): fails.append(msg); print('FAIL',msg)
# 0 ------------------------------------------------------------------
st=subprocess.run([sys.executable,'/home/claude/work/guitar/gcheck_selftest.py'],capture_output=True,text=True)
R['selftest']='pass' if st.returncode==0 else 'FAIL'
if st.returncode: print(st.stdout); fail('self-test'); json.dump(R,open('/home/claude/work/guitar/handqa_last.json','w'),indent=1); sys.exit(1)
import gtear as T, gseq, retarget as RT, vanim
VB='ValveBiped.Bip01_'
# 1 ------------------------------------------------------------------
def mapping(d):
    nodes=T.nodes_of(d); inv={v:k for k,v in nodes.items()}; P=[];D=[]
    for f in ('arms_gorilla_black','arms_cyber_gorilla_black','arms_plates_l_gorilla_black','arms_plates_r_gorilla_black'):
        p,b,w,_=T.load(d+'/token_base_%s.smd'%f); P.append(p); D.append(b[np.arange(len(b)),w.argmax(1)])
    p=np.vstack(P); dom=np.concatenate(D); out={}
    for s in 'LR':
        for f in range(5):
            for k in ('','1','2'):
                if f==0 and k=='2': continue                 # CP thumbs have two segments: Finger02 legitimately carries none
                n=VB+'%s_Finger%d%s'%(s,f,k); i=RT.vn.index(n); sel=dom==inv[n]
                if not sel.any(): out[n[17:]]='no mesh (frozen)'; continue
                L=np.linalg.norm(RT.NL[RT.vn.index(VB+'%s_Finger%d%s'%(s,f,{'':'1','1':'2'}[k]))][:3,3]) if k!='2' else 1.0
                q=(p[sel]-RT.NW[i][:3,3])@RT.NW[i][:3,:3]; x=float(np.median(q[:,0])); r=float(np.median(np.linalg.norm(q[:,1:],axis=1)))
                if not (-0.3<x<L+0.3 and r<0.75): out[n[17:]]='off its mesh (along %.2f, off-axis %.2f in)'%(x,r)
                far=float((np.linalg.norm(q[:,1:],axis=1)>1.0).mean())
                if far>0.10 and sel.sum()>50: out[n[17:]+' outliers']='%.0f%% of its %d vertices lie >1 in from the bone (they swing with the finger)'%(far*100,sel.sum())
    return out
# 2 ------------------------------------------------------------------
def poses():
    if a.stance=='guitar': gseq.install_fretting(); f=gseq.world_at; L=gseq.LOOP
    return [vanim.full_world(vanim.valve_world_rots_W(f(t))) for t in np.linspace(0,L,a.frames,endpoint=False)]
NWS=poses()
def tearing(d):
    nodes=T.nodes_of(d); hands=[RT.NW[RT.vn.index(VB+s+'_Hand')][:3,3] for s in 'LR']; res={'hand':0,'arm':0,'worst':1.0}
    for f in ('arms_gorilla_black','arms_cyber_gorilla_black','arms_plates_l_gorilla_black','arms_plates_r_gorilla_black'):
        P,Bn,Wt,_=T.load(d+'/token_base_%s.smd'%f); F=np.arange(len(P)).reshape(-1,3)
        E0=np.stack([np.linalg.norm(P[F[:,i]]-P[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1); worst=np.ones(len(F))
        for NW in NWS:
            Q=T.skin(NW,nodes,P,Bn,Wt); E=np.stack([np.linalg.norm(Q[F[:,i]]-Q[F[:,j]],axis=1) for i,j in ((0,1),(1,2),(2,0))],1)
            r=E/np.maximum(E0,1e-6); worst=np.maximum(worst,np.where(E0>0.02,np.maximum(r,1/np.maximum(r,1e-6)),1).max(1))
        c=P[F].mean(1); near=np.min([np.linalg.norm(c-h,axis=1) for h in hands],0)<HAND_R
        bad=worst>TEAR; res['hand']+=int((bad&near).sum()); res['arm']+=int((bad&~near).sum()); res['worst']=max(res['worst'],round(float(worst.max()),2))
    return res
for lab,d in (('shipped',SHIPPED),('candidate',a.cand)):
    R[lab]={'mapping':mapping(d),'tearing':tearing(d)}
    print(lab,'mapping problems:',len(R[lab]['mapping']),'| torn tris hand %(hand)d arm %(arm)d, worst %(worst).1fx'%R[lab]['tearing'])
if R['candidate']['mapping']: fail('bone mapping: '+'; '.join('%s %s'%kv for kv in list(R['candidate']['mapping'].items())[:6]))
for reg in ('hand','arm'):
    if R['candidate']['tearing'][reg]>R['shipped']['tearing'][reg]: fail('tearing in the %s region: %d torn tris vs %d shipped'%(reg,R['candidate']['tearing'][reg],R['shipped']['tearing'][reg]))
# 3-5 ----------------------------------------------------------------
if a.stance=='guitar':
    os.environ['BASEDIR']=a.cand; os.environ['FRET']='1'
    import gcheck as G
    ts=np.linspace(0,gseq.LOOP,a.frames,endpoint=False); fr=[G.frame(gseq.world_at,t) for t in ts]
    errs=[]
    for f_,t in zip(fr,ts):
        W=gseq.world_at(t); M=G.P.pose_mats(G._C(lambda _:W),t); Pp,N,B,Wt,dom=G.HV['L']; p,_=G.P.skinned(M,Pp,N,B,Wt); q=G.to_item(M,p)
        tg=gseq.fret_targets(W)
        for fi in range(1,5):
            ix=G.TIPV['L'][fi]
            if len(ix): errs.append(np.linalg.norm(q[ix].mean(0)-tg[fi])*1000)
    R['collision']=dict(L_max_inside=max(f['L_inside'] for f in fr),L_max_depth_mm=max(f['L_depth_mm'] for f in fr),R_max_inside=max(f['R_inside'] for f in fr),R_max_depth_mm=max(f['R_depth_mm'] for f in fr))
    R['contact']=dict(fret_tip_err_mean_mm=round(float(np.mean(errs)),1),fret_tip_err_max_mm=round(float(np.max(errs)),1))
    # strumming is ~5 strokes/s: sample a 6 s window densely (30 fps) or it aliases away
    sw=[G.frame(gseq.world_at,t) for t in np.arange(10.0,16.0,1/30)]; R['strum']=G.strum(sw)
    cp=[]; I={n:i for i,n in enumerate(G.cpanim.NAMES)}
    for t in np.arange(10.0,16.0,1/30):
        W=gseq.SONGS[0].world(t); cp.append((np.linalg.inv(W[I['WeaponLeft']])@W[I['RightHandIndex3']][:,3])[1])
    cp=np.array(cp); v=np.sign(np.diff(cp)); v=v[v!=0]; R['strum']['cp_strokes_per_s']=round(float(np.sum(v[1:]!=v[:-1])/2/6.0),2)
    print('collision',R['collision']); print('contact',R['contact']); print('strum',R['strum'])
    if R['collision']['L_max_depth_mm']>3 or R['collision']['R_max_depth_mm']>3: fail('hands inside the guitar (max depth L %.1f / R %.1f mm)'%(R['collision']['L_max_depth_mm'],R['collision']['R_max_depth_mm']))
    if abs(R['strum']['strokes_per_s']-R['strum']['cp_strokes_per_s'])>0.25*R['strum']['cp_strokes_per_s']: fail('strum rate %.2f/s vs Cyberpunk %.2f/s'%(R['strum']['strokes_per_s'],R['strum']['cp_strokes_per_s']))
    if R['contact']['fret_tip_err_mean_mm']>8: fail('fretting fingertips %.1f mm from their frets on average'%R['contact']['fret_tip_err_mean_mm'])
R['result']='PASS' if not fails else 'FAIL'; R['fails']=fails
json.dump(R,open('/home/claude/work/guitar/handqa_last.json','w'),indent=1)
print('RESULT',R['result'],len(fails),'failures'); sys.exit(0 if not fails else 1)
