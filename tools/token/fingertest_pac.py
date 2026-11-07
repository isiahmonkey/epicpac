"""PAC3 test outfit for step 1 of the hand reset: Token (outfit 2) with the Gorilla hands hidden, Cyberpunk's bare hands
(token_testhands) on, and the finger-test stance (each finger curls in turn, then a fist; 11 s loop)."""
import sys, json, hashlib
sys.argv=[sys.argv[0],'outfit2']
B='/mnt/user-data/outputs/token_build/'
exec(open('/home/claude/work/token/pacfile.py').read().split("root=part(")[0])   # helpers: part, model, lua, ANIM, hide, plan
hide2=hide+'arms=1;arms_cyber=1;arms_plates_l=1;arms_plates_r=1;'   # whole Gorilla arm off: the test model carries the full Cyberpunk base arm
root=part('group','Token - finger test',dict(OwnerName='self'),[
  part('entity2','hide player',dict(NoDraw=True,DrawShadow=True)),
  part('model2','token_base',dict(Model=model('token_base'),BoneMerge=True,ModelModifiers=hide2)),
  part('model2','token_outfit2',dict(Model=model('token_outfit2'),BoneMerge=True)),
  part('model2','token_testhands',dict(Model=model('token_testhands'),BoneMerge=True)),
  part('custom_animation','finger test',dict(URL=ANIM%'token_fingertest',AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
])
out=B+'pac3_outfits/token_fingertest.txt'
open(out,'w',newline='\n').write('[1] = %s,\n'%lua(root,2)); print(out)
