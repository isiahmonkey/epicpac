"""Bake CP77 multilayered materials (mlsetup + mlmask + mltemplates) to flat albedo / roughness / metalness maps."""
import sys,functools,numpy as np; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/build')
import cr2w,xbm,garments,mlmask
from PIL import Image
MISSING=set()
COLOR_OVERRIDE={}   # {layer index: linear rgb} - recolours a layer (e.g. Takemura white enamel -> black)
LAYER_COLORS={}
NORMALS=True
@functools.lru_cache(None)
def tex(path):
    s=garments.segs_of(path)
    if s is None: MISSING.add(path); return None
    try: im=xbm.load(s)
    except Exception as e: MISSING.add(path+' ('+str(e)+')'); return None
    return np.asarray(im.convert('RGBA')).astype(np.float32)/255
@functools.lru_cache(None)
def template(path):
    s=garments.segs_of(path)
    if s is None: MISSING.add(path); return None
    b=s[0]; r=cr2w.parse(b); return cr2w.chunk(b,r,0)[1]
def ref(v): return v[1] if isinstance(v,tuple) and v and v[0]=='ref' else None
def ov(lst,name,default):
    for e in lst or []:
        if e.get('n')==name: return e.get('v',[0.0]*len(default) if isinstance(default,list) else 0.0)   # unserialized = zero default
    for e in lst or []:
        if e.get('n')=='null': return e.get('v',default)
    return default
def srgb2lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def lin2srgb(c): c=np.clip(c,0,1); return np.where(c<=0.0031308,c*12.92,1.055*c**(1/2.4)-0.055)
def tiled(t,R,rep,ch=None):
    """sample texture t tiled `rep` times across an RxR target, prefiltered (cheap mip)"""
    if t is None: return None
    h,w=t.shape[:2]; cell=R/max(rep,1e-3)              # target pixels per repeat
    if rep<0.5:   # a tiny sliver of the texture stretched over the whole UV: CP reads it as a flat colour; magnifying it made big blotches/blocks
        return np.broadcast_to(t.reshape(-1,t.shape[2]).mean(0) if t.ndim==3 else t.mean(),(R,R)+t.shape[2:]).astype(np.float32).copy()
    sz=int(np.clip(cell,2,w))
    small=np.asarray(Image.fromarray((t*255).astype(np.uint8)).resize((sz,sz),Image.LANCZOS)).astype(np.float32)/255
    # bilinear, wrapping (the old nearest lookup magnified small tiles into visible pixel blocks)
    u=(np.arange(R)+0.5)*sz*rep/R-0.5; i0=np.floor(u).astype(np.int64); f=(u-i0).astype(np.float32); i0%=sz; i1=(i0+1)%sz
    a=small[i0]*(1-f)[:,None,None] if small.ndim==3 else small[i0]*(1-f)[:,None]
    b=small[i1]*f[:,None,None] if small.ndim==3 else small[i1]*f[:,None]
    rows=a+b
    fx=f[None,:,None] if rows.ndim==3 else f[None,:]
    return rows[:,i0]*(1-fx)+rows[:,i1]*fx
def bake(mlsetup,mlmask_path,R=1024):
    s=garments.segs_of(mlsetup)
    if s is None: MISSING.add(mlsetup); return None
    b=s[0]; r=cr2w.parse(b); layers=cr2w.chunk(b,r,0)[1].get('layers',[])
    ms=garments.segs_of(mlmask_path)
    M=mlmask.load(ms) if ms else None
    if M is None: MISSING.add(mlmask_path)
    nxy=np.zeros((R,R,2),np.float32); col=np.ones((R,R,3),np.float32)*0.5; rough=np.full((R,R),0.6,np.float32); metal=np.zeros((R,R),np.float32); vis=[]; info=[]
    for i,L in enumerate(layers):
        if M is not None and i>=len(M): break
        m=np.ones((R,R),np.float32) if (i==0 or M is None) else np.asarray(Image.fromarray(M[i]).resize((R,R),Image.BILINEAR)).astype(np.float32)/255
        # CP mask mixer (per the WolvenKit Blender add-on): microblend alpha breaks up the layer mask at `microblendContrast`
        c_=max(float(L.get('microblendContrast',1.0) if L.get('microblendContrast') is not None else 1.0),1e-5)
        if c_<0.999 and i>0 and L.get('mbTile') is not None:   # no own mbTile: CP would stretch the noise over the garment -> blend smoothly
            mbt=tex(ref(L.get('microblend')))
            if mbt is not None:
                mbr=float(L.get('mbTile') or L.get('matTile') or 1.0)
                mba=tiled(mbt,R,mbr)[...,3]
                if mba.min()>0.99: mba=tiled(mbt,R,mbr)[...,0]     # some microblends keep the height in R
                mix=(m+mba-1)*(1-c_)+m*c_; m=np.clip(mix/c_,0,1)
        m=m*float(L.get('opacity',1.0) if L.get('opacity') is not None else 1.0)
        if any(k in (ref(L.get('material')) or '') for k in ('dirt_','dust_','grime','mud_')): m=m*0.2      # grime reads twice as heavy without CP's runtime microblend detail
        if m.max()<=0.002: continue
        if i>0 and L.get('colorScale') in ('null_null',None,'null'): continue      # placeholder layers (no colour set): CP leaves them as unpainted grey -> skip
        T=template(ref(L.get('material')))
        if T is None: continue
        o=T.get('overrides',{})
        rep=float(L.get('matTile',1.0))*float(T.get('tilingMultiplier',1.0))
        ct=tiled(tex(ref(T.get('colorTexture'))),R,rep)
        cs=np.array(ov(o.get('colorScale'),L.get('colorScale','null'),[1,1,1]),np.float32)
        c=(srgb2lin(ct[...,:3]) if ct is not None else np.full((R,R,3),0.5,np.float32))*cs
        LAYER_COLORS[i]=(cs.tolist(),float(m.mean()))
        if i in COLOR_OVERRIDE: c=(srgb2lin(ct[...,:3]) if ct is not None else np.full((R,R,3),0.5,np.float32)).mean(-1,keepdims=True)/0.5*np.array(COLOR_OVERRIDE[i],np.float32)
        rt=tiled(tex(ref(T.get('roughnessTexture'))),R,rep); rv=rt[...,0] if rt is not None else np.full((R,R),0.5,np.float32)
        ro=ov(o.get('roughLevelsOut'),L.get('roughLevelsOut','null'),[1,0]); rv=ro[1]+(ro[0]-ro[1])*rv
        mt=tiled(tex(ref(T.get('metalnessTexture'))),R,rep); mv=mt[...,0] if mt is not None else np.zeros((R,R),np.float32)
        mo=ov(o.get('metalLevelsOut'),L.get('metalLevelsOut','null'),[1,0]); mv=mo[1]+(mo[0]-mo[1])*mv
        if float(mv.mean())>0.5: c=np.minimum(c*1.8,0.22)   # metals: CP's colour is a dark F0 tint that only reads via reflections; Gmod needs a visible steel albedo
        col=col*(1-m[...,None])+c*m[...,None]; rough=rough*(1-m)+rv*m; metal=metal*(1-m)+mv*m
        nt=tiled(tex(ref(T.get('normalTexture'))),R,rep) if NORMALS else None     # per-layer surface normal (weave, perforation, grain)
        if nt is not None:
            ns=float(ov(o.get('normalStrength'),L.get('normalStrength','null'),1.0) or 0.0)
            lxy=np.dstack([nt[...,0]*2-1,nt[...,1]*2-1])*ns
            nxy=nxy*(1-m[...,None])+lxy*m[...,None]
        vis=[v*(1-m) for v in vis]; vis.append(m.copy()); info.append((ref(T.get('colorTexture')),rep,ref(L.get('material'))))
    # detail texture = the tiled surface that is actually VISIBLE most (after all layers above it), ignoring flat/huge-scale layers
    best=None
    for v,(t,rep,mat) in zip(vis,info):
        if t is None or rep<1.5: continue
        sc=float(v.mean())
        if best is None or sc>best[0]: best=(sc,t,rep,mat)
    dom=best
    return dict(nxy=nxy,albedo=lin2srgb(col),rough=np.clip(rough,0,1),metal=np.clip(metal,0,1),detail=dom)
if __name__=='__main__':
    o=bake(sys.argv[1],sys.argv[2],512)
    Image.fromarray((np.hstack([o['albedo'],np.dstack([o['rough']]*3),np.dstack([o['metal']]*3)])*255).astype(np.uint8)).save(sys.argv[3])
    print('missing',MISSING)
