import numpy as np, render
from PIL import Image, ImageFilter
def view(parts, yaw=0.0, size=(700,900), focus=None, strength=0.7, radius=None, **kw):
    """normal render + emission pass: parts with 'emit' draw their emission map unlit, everything else
    draws black (so it still occludes); the pass is bloomed and added (faint glow around the hues)."""
    base=render.view(parts,yaw=yaw,size=size,focus=focus,**kw)
    if not any('emit' in p for p in parts): return base
    ep=[]
    for p in parts:
        q=dict(pos=p['pos'],idx=p['idx'],uv=p.get('uv'))
        if 'emit' in p: q['tex']=p['emit']; q['alpha']=0
        elif p.get('alpha',0)==2: continue               # decals don't occlude light
        else: q['color']=(0,0,0)
        ep.append(q)
    e=np.asarray(render.view(ep,yaw=yaw,size=size,focus=focus,bg=(0,0,0),light=(0,-1,0),**kw)).astype(np.float32)
    r=radius or max(2,size[0]//180)
    bloom=np.asarray(Image.fromarray(e.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)
    wide=np.asarray(Image.fromarray(e.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r*3))).astype(np.float32)
    out=np.asarray(base).astype(np.float32)+strength*(0.35*e+0.9*bloom+0.6*wide)
    return Image.fromarray(np.clip(out,0,255).astype(np.uint8))
