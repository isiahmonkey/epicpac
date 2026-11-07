"""Weight check for Token's hands: pose the arm/hand SMDs with a stance and report triangles whose edges stretch or
collapse (skin tearing, plates bending) plus vertices whose weights mix bones that aren't neighbours.
python3 gtear.py <modelsrc dir> <stance: guitar|smoke|whiskey|bind> [times]"""
import sys,glob,os,json,numpy as np,collections
sys.path[:0]=['/home/claude/work/guitar','/home/claude/work/smoke','/home/claude/work/drink','/home/claude/work/anim','/home/claude/tools/scripts','/home/claude/work/build']
import vanim, retarget as RT
VB='ValveBiped.Bip01_'
def load(f):
    T=open(f).read().split('triangles\n')[1].split('\n'); P=[];Bn=[];Wt=[];M=[]
    for i in range(0,len(T)-3,4):
        if T[i].strip()=='end': break
        for k in (1,2,3):
            t=T[i+k].split(); n=int(t[9]); P.append(list(map(float,t[1:4])))
            Bn.append([int(t[10+2*q]) for q in range(n)][:4]+[0]*(4-min(n,4))); Wt.append([float(t[11+2*q]) for q in range(n)][:4]+[0]*(4-min(n,4)))
        M.append(T[i].strip())
    return np.array(P),np.array(Bn),np.array(Wt),M
def nodes_of(d):
    L=open(d+'/token_base_bind.smd').read().split('\n'); k=L.index('nodes')+1; out={}
    while L[k]!='end': t=L[k].split('"'); out[int(t[0])]=t[1]; k+=1
    return out
def skin(NW,nodes,P,Bn,Wt):
    Mk=np.stack([NW[RT.vn.index(nodes[b])]@np.linalg.inv(RT.NW[RT.vn.index(nodes[b])]) if b in nodes and nodes[b] in RT.vn else np.eye(4) for b in range(max(nodes)+1)])
    h=np.c_[P,np.ones(len(P))]; out=np.zeros((len(P),3))
    for k in range(4): out+=Wt[:,k,None]*np.einsum('nij,nj->ni',Mk[Bn[:,k]][:,:3,:4],h)
    return out/np.maximum(Wt.sum(1,keepdims=True),1e-9)
def neighbours(nodes):
    """bones allowed to share a vertex: a bone, its parent, its children, and sibling finger roots (the palm web)"""
    par={i:RT.vp[RT.vn.index(n)] for i,n in nodes.items() if n in RT.vn}; idx={n:i for i,n in nodes.items()}
    ok=collections.defaultdict(set)
    for i,n in nodes.items():
        if n not in RT.vn: continue
        p=RT.vn[par[i]] if par[i]>=0 else None; ok[i].add(i)
        if p in idx: ok[i].add(idx[p]); ok[idx[p]].add(i)
    for s in 'LR':
        roots=[idx.get(VB+'%s_Finger%d'%(s,f)) for f in range(5)]+[idx.get(VB+s+'_Hand')]
        for a in roots:
            for b in roots:
                if a is not None and b is not None: ok[a].add(b)
    return ok
def check(d,NWs,label):
    nodes=nodes_of(d); ok=neighbours(nodes); res={}
    for f in sorted(glob.glob(d+'/token_base_arms*.smd')):
        P,Bn,Wt,M=load(f); nm=os.path.basename(f)[11:-4]
        bad_w=sum(1 for b,w in zip(Bn,Wt) for i in range(4) for j in range(4) if w[i]>0.05 and w[j]>0.05 and Bn[j][0:1] is not None and b[j] not in ok[b[i]])
        F=np.arange(len(P)).reshape(-1,3); E0=np.stack([np.linalg.norm(P[F[:,a]]-P[F[:,b]],axis=1) for a,b in ((0,1),(1,2),(2,0))],1)
        worst=[];torn=0
        for NW in NWs:
            Q=skin(NW,nodes,P,Bn,Wt); E=np.stack([np.linalg.norm(Q[F[:,a]]-Q[F[:,b]],axis=1) for a,b in ((0,1),(1,2),(2,0))],1)
            r=(E/np.maximum(E0,1e-6)); big=(E0>0.02)
            s=np.where(big,np.maximum(r,1/np.maximum(r,1e-6)),1).max(1); torn=max(torn,int((s>1.6).sum())); worst.append(float(s.max()))
        res[nm]=dict(tris=len(F),torn_tris_max=torn,worst_stretch=round(max(worst),2),non_neighbour_weight_pairs=bad_w)
    print(label,json.dumps(res,indent=1)); return res
def poses(stance,n=24):
    if stance=='bind': return [list(RT.NW)]
    if stance=='guitar': import gseq as S; L=S.LOOP; f=S.world_at
    elif stance=='smoke': import sseq as S; S.build_intro(); L=S.INTRO+S.LOOP; f=S.world_at
    elif stance=='whiskey':
        import seq_whiskey as S; L=S.TOTAL; f=S.world_at
    return [vanim.full_world(vanim.valve_world_rots_W(f(t))) for t in np.linspace(0,L,n,endpoint=False)]
if __name__=='__main__':
    d=sys.argv[1]
    for st in sys.argv[2].split(','): check(d,poses(st),st)
