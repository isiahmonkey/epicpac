import sys,os,numpy as np; sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/pbr']
import garments,mats,mesh,xbm,glb
from PIL import Image
def tex(p):
    s=garments.segs_of(p) if p else None
    try: return xbm.load(s).convert('RGBA') if s else None
    except Exception: return None
def build(path,out,app=None,liquid=(0.45,0.20,0.04)):
    s=garments.segs_of(path); m=mesh.decode(s); b,r,mm,apps=mats.mesh_info(s); app=app or list(apps)[0]; cm=apps[app]
    G=glb.GLB(); M={}
    P=np.concatenate([x['pos'] for x in m['subs']]); c=(P.min(0)+P.max(0))/2; c[2]=P[:,2].min()
    for x in m['subs']:
        mn=cm[x['chunk']] if x['chunk']<len(cm) else cm[0]
        refs=mats.material_refs(s,mn)[0]; mt=refs[0] if refs else ''
        xb=[t for t in refs if t.endswith('.xbm')]
        d=next((tex(t) for t in xb if t.endswith(('_d.xbm','label.xbm','label_m.xbm','_d01.xbm')) and tex(t) is not None),None)
        k=mn+'_%d'%x['chunk']
        if 'chunk_invisible' in str(refs) or 'bounding' in mn: continue
        if 'fluid' in mn or 'liquid' in mn or ('interior' in mn and 'bottle' in path and 'glass_f' not in path):
            M[k]=G.material(k,color=liquid+(0.92,),rough=0.08,alpha='BLEND',ext={'order':1})          # whiskey
        elif 'glass' in mt or 'glass' in mn or 'deffered' in mn or 'xglass' in mn or 'exterior' in mn:
            M[k]=G.material(k,base=d,color=(0.80,0.86,0.84,0.22),rough=0.04,alpha='BLEND',ext={'order':2,'clearcoat':1.0})
        elif 'decal' in mt or 'label' in mn:
            M[k]=G.material(k,base=d if d is not None else None,color=(1,1,1,1) if d is not None else (0.75,0.6,0.25,1),alpha='BLEND' if d is not None else 'OPAQUE',rough=0.5,metal=0.3 if 'gold' in mn else 0.0,ext={'order':3})
        elif 'cap' in mn:
            M[k]=G.material(k,color=(0.08,0.07,0.06,1) if 'label' in mn else (0.6,0.55,0.45,1),metal=0.9,rough=0.35)
        else:
            M[k]=G.material(k,base=d,color=(0.5,0.5,0.5,1),rough=0.5)
        G.mesh(k,x['pos']-c,x['idx'],x['uv0'],M[k])
    G.save(out); return P.max(0)-P.min(0)
if __name__=='__main__':
    print(build(sys.argv[1],sys.argv[2]))
