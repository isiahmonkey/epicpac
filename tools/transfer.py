"""Transfer a Female-V body tattoo (painted in pwa body+arm UV layout) onto Male V, keeping its anatomical placement.
female surface (UV->3D) -> per-part bbox affine to male proportions -> snap to closest male surface -> bake into male body / arm UVs."""
import sys,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts')
import cr2w,mesh,bake
from PIL import Image
from scipy.spatial import cKDTree
F='/mnt/user-data/uploads/characters/common/player_base_bodies/player_female_average/'
M='/mnt/user-data/uploads/characters/common/player_base_bodies/player_man_average/'
def load(path,chunks=None):
    subs=mesh.decode(cr2w.load_loose(path))['subs']; subs=subs if chunks is None else subs[:chunks]
    P=[];I=[];U=[];o=0
    for s in subs: P.append(s['pos']);I.append(s['idx'].reshape(-1,3)+o);U.append(s['uv0']);o+=len(s['pos'])
    return np.concatenate(P),np.concatenate(I),np.concatenate(U)
fb=load(F+'t0_000_pwa_base__full.mesh'); fl=load(F+'arms_hq/a0_000_pwa_base_hq__l.mesh',3); fr=load(F+'arms_hq/a0_000_pwa_base_hq__r.mesh',3)
mb=load(M+'t0_000_pma_base__full.mesh'); ml=load(M+'arms_hq/a0_000_pma_base_hq__l.mesh',3); mr=load(M+'arms_hq/a0_000_pma_base_hq__r.mesh',3)
def box_map(src,dst):
    lo,hi=src.min(0),src.max(0); LO,HI=dst.min(0),dst.max(0); return lambda p:(p-lo)/(hi-lo)*(HI-LO)+LO
def snap(p,targets):
    allp=np.concatenate([t[0] for t in targets])
    # dense surface samples of the male mesh for a closest-point snap
    S=[];
    for P,I,_ in targets:
        bc=np.array([(a,b,1-a-b) for a in np.linspace(0,1,5) for b in np.linspace(0,1,5) if a+b<=1.0001])
        S.append(np.einsum('kj,tjd->tkd',bc,P[I]).reshape(-1,3))
    S=np.concatenate(S); d,i=cKDTree(S).query(p); return S[i],d
def warp(part,src,dst,targets):
    P,I,U=part; q=box_map(src[0],dst[0])(P); q2,d=snap(q,targets); return (q2,I,U),d
parts={'body':warp(fb,fb,mb,[mb]),'armL':warp(fl,fl,ml,[ml]),'armR':warp(fr,fr,mr,[mr])}
def bake_to(bases,tex,R=2048):
    out=np.full((R,R,4),255,np.uint8)
    for base in bases:
        for k,(p,d) in parts.items(): bake.bake_overlay(out,base[0],base[1].ravel(),base[2],p[0],p[1].ravel(),p[2],tex,1.0,None,maxdist=0.006)
    a=255-out[...,:3].min(2); o=np.zeros_like(out); o[...,3]=a; return Image.fromarray(o,'RGBA')
if __name__=='__main__':
    ink=None
    for j in sys.argv[1:]:
        a=np.asarray(Image.open(j).convert('RGBA')).astype(np.float32)
        ink=a if ink is None else np.maximum(ink,a)
    ink[...,:3]=np.minimum(ink[...,:3],0); tex=Image.fromarray(ink.astype(np.uint8),'RGBA').resize((2048,2048),Image.LANCZOS)
    bake_to([mb],tex).save('/home/claude/work/tattoo/male_body_tattoo.png')
    bake_to([ml,mr],tex).save('/home/claude/work/tattoo/male_arms_tattoo.png')
    print('ok')
