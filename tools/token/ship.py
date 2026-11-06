"""Zip only what changed in token_build since the last delivery -> token_build_patchNN.zip (or _full on first run)."""
import os,hashlib,json,zipfile,sys
B='/mnt/user-data/outputs/token_build/'; MAN='/home/claude/work/token/shipped_manifest.json'
old=json.load(open(MAN)) if os.path.exists(MAN) and '--full' not in sys.argv else {}
new={}; changed=[]
for d in ('modelsrc','materialsrc','materials','plans'):
    for f in sorted(os.listdir(B+d)):
        rel=d+'/'+f; h=hashlib.md5(open(B+rel,'rb').read()).hexdigest(); new[rel]=h
        if old.get(rel)!=h: changed.append(rel)
n=len([k for k in old]) and len([f for f in os.listdir('/mnt/user-data/outputs') if f.startswith('token_build_patch')])+1
name='/mnt/user-data/outputs/'+('token_build_full.zip' if not old else 'token_build_patch%02d.zip'%n)
with zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED) as z:
    for rel in changed: z.write(B+rel,rel)
json.dump(new,open(MAN,'w'))
print(name,len(changed),'files',round(os.path.getsize(name)/1e6,1),'MB')
