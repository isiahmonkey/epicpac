"""Run the staging material builder (export_glb.py) and keep each material's normal map + roughness/metal,
so the Gmod kit gets the same surface detail the staging renders had."""
import sys,os,pickle
sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build','/home/claude/work/pbr']
import glb
CAP={}
_orig=glb.GLB.material
def material(self,name,**k):
    CAP[name]={x:k.get(x) for x in ('base','normal','mr','rough','metal','nscale','emissive','alpha')}
    return _orig(self,name,**k)
glb.GLB.material=material; glb.GLB.save=lambda *a,**k:None
os.environ.setdefault('MORPH','2'); os.environ.setdefault('TONE','deep')
os.environ.update(BODY='1',GORILLA='black',HAT='1',SHOW_HAT='1',ACC='cross_bracelet_l',
    OUTFIT=os.environ.get('OUTFIT','misfits,jeans,synthpants,hoodie,pants,longfur,furjacket,bolero,walletchain,vinyl,tron,boots,vcross'))
os.chdir('/home/claude/work/staging')
src=open('/home/claude/work/staging/export_glb.py').read()
try: exec(compile(src,'export_glb','exec'),{'__name__':'cap'})
except SystemExit: pass
except Exception as e: print('export stopped:',repr(e)[:200])
pickle.dump(CAP,open('/home/claude/work/token/staged_mats.pkl','wb'))
print('captured',len(CAP),sorted(n for n,v in CAP.items() if v['normal'] is not None))
