"""Write a PAC3 outfit file (garrysmod/data/pac3/<name>.txt) for a Token outfit.
   python3 pacfile.py outfit1            -> local model paths (test on your own PC)
   python3 pacfile.py outfit1 URLBASE    -> zip URLs for everyone (URLBASE/token_base_pac3.zip ...)"""
import sys, json, hashlib
B='/mnt/user-data/outputs/token_build/'
oid=sys.argv[1]; url=sys.argv[2].rstrip('/') if len(sys.argv)>2 else None
plan=json.load(open(B+'plans/%s.json'%oid))
uid=lambda s: hashlib.sha1(('token/'+oid+'/'+s).encode()).hexdigest()
ANIM_V=1
model=lambda m: (url+'/%s_pac3.zip'%m) if url else 'models/player/token/%s.mdl'%m
ANIM='https://raw.githubusercontent.com/isiahmonkey/epicpac/main/anim/%s.json?v='+str(ANIM_V)
class Vec(tuple): pass
class Ang(tuple): pass
def lua(v,t=1):
    if isinstance(v,Vec): return 'Vector(%s)'%(', '.join('%g'%x for x in v))
    if isinstance(v,Ang): return 'Angle(%s)'%(', '.join('%g'%x for x in v))
    if isinstance(v,bool): return 'true' if v else 'false'
    if isinstance(v,(int,float)): return repr(v)
    if isinstance(v,str): return '"%s"'%v.replace('\\','\\\\').replace('"','\\"')
    if isinstance(v,list): v={i+1:x for i,x in enumerate(v)}
    pad='\t'*t; s='{\n'
    for k,x in v.items(): s+=pad+'[%s] = %s,\n'%(lua(k) if isinstance(k,str) else k, lua(x,t+1))
    return s+'\t'*(t-1)+'}'
part=lambda cls,name,extra,children=[]: {'children':children,'self':dict(ClassName=cls,Name=name,UniqueID=uid(name),**extra)}
hide=';'.join('skin_%s=1'%r for r in plan['hide_skin'])+';' if plan['hide_skin'] else ''
root=part('group','Token - %s'%oid,dict(OwnerName='self'),[
  part('entity2','hide player',dict(NoDraw=True,DrawShadow=True)),
  part('model2','token_base',dict(Model=model('token_base'),BoneMerge=True,ModelModifiers=hide)),
  part('model2','token_'+oid,dict(Model=model('token_'+oid),BoneMerge=True)),
  part('model2','token_earring',dict(Model=model('token_earring'),BoneMerge=True)),   # swings via its own jigglebone
  part('model2','token_hat',dict(Model=model('token_hat'),BoneMerge=True),[
    part('event','hide_hat (pac_event hide_hat 2)',dict(Event='command',Operator='equal',Arguments='hide_hat@@0@@0',Invert=False))]),
  part('group','Whiskey (pac_event whiskey 2)',{},[
    part('event','show while whiskey is on',dict(Event='command',Operator='equal',Arguments='whiskey@@0@@0',Invert=True)),
    part('custom_animation','whiskey stance',dict(URL=ANIM%'token_whiskey',AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
    part('model2','token_drinkware',dict(Model=model('token_drinkware'),BoneMerge=True)),
  ]),
  part('group','Bouncer (pac_event bouncer 2)',{},[
    part('event','show while bouncer is on',dict(Event='command',Operator='equal',Arguments='bouncer@@0@@0',Invert=True)),
    part('custom_animation','bouncer stance',dict(URL=ANIM%'token_bouncer',AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
  ]),
])
out=B+'pac3_outfits/token_%s.txt'%oid
open(out,'w',newline='\n').write('[1] = %s,\n'%lua(root,2))
print(out); print(open(out).read())
