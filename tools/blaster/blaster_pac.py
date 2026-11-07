"""PAC3 file for the Blade Runner Blaster (Dark): shows the gun in the right hand whenever you hold the .357
and hides the stock .357 world model.  python3 blaster_pac.py [MODEL_URL] [WEAPON_CLASS]"""
import sys,hashlib
sys.path.insert(0,'/home/claude/work/token')
url=sys.argv[1] if len(sys.argv)>1 and sys.argv[1]!='-' else None
wclass=sys.argv[2] if len(sys.argv)>2 else 'weapon_357'
uid=lambda s: hashlib.sha1(('br_blaster/'+s).encode()).hexdigest()
def lua(v,t=1):
    if isinstance(v,bool): return 'true' if v else 'false'
    if isinstance(v,(int,float)): return repr(v)
    if isinstance(v,str): return '"%s"'%v.replace('\\','\\\\').replace('"','\\"')
    if isinstance(v,list): v={i+1:x for i,x in enumerate(v)}
    pad='\t'*t; s='{\n'
    for k,x in v.items(): s+=pad+'[%s] = %s,\n'%(lua(k) if isinstance(k,str) else k, lua(x,t+1))
    return s+'\t'*(t-1)+'}'
part=lambda cls,name,extra,children=[]: {'children':children,'self':dict(ClassName=cls,Name=name,UniqueID=uid(name),**extra)}
model=url or 'models/player/token/br_blaster.mdl'
root=part('group','Blade Runner Blaster (Dark)',dict(OwnerName='self'),[
  part('event','only while holding %s (hides the stock gun)'%wclass,dict(Event='weapon_class',Operator='find simple',Arguments='%s@@1'%wclass,Invert=True)),
  part('model2','Blaster',dict(Model=model,BoneMerge=True)),
])
out='/mnt/user-data/outputs/token_build/pac3_outfits/br_blaster%s.txt'%('' if not url else '_share')
open(out,'w',newline='\n').write('[1] = %s,\n'%lua(root,2)); print(out)
