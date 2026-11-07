"""PAC3 test outfit for step 2 of the hand reset: Token (outfit 2), Gorilla arm hidden, hand D (token_handsd) with the
Judy tuner gloves (token_gloves, Street Kid sticker on the left) and the finger-test stance (11 s loop)."""
import sys
sys.argv=[sys.argv[0],'outfit2']
B='/mnt/user-data/outputs/token_build/'
exec(open('/home/claude/work/token/pacfile.py').read().split("root=part(")[0])
hide2=hide+'arms=1;arms_cyber=1;arms_plates_l=1;arms_plates_r=1;'
root=part('group','Token - glove test',dict(OwnerName='self'),[
  part('entity2','hide player',dict(NoDraw=True,DrawShadow=True)),
  part('model2','token_base',dict(Model=model('token_base'),BoneMerge=True,ModelModifiers=hide2)),
  part('model2','token_outfit2',dict(Model=model('token_outfit2'),BoneMerge=True)),
  part('model2','token_handsd',dict(Model=model('token_handsd'),BoneMerge=True)),
  part('model2','token_gloves',dict(Model=model('token_gloves'),BoneMerge=True)),
  part('custom_animation','finger test',dict(URL=ANIM%'token_fingertest',AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
])
out=B+'pac3_outfits/token_glovetest.txt'
open(out,'w',newline='\n').write('[1] = %s,\n'%lua(root,2)); print(out)
