"""PAC3 test outfit for step 3: Token (outfit 2) with hand D + Judy tuner gloves, the black Electric A on its strap and the
cigarette, playing the guitar stance. Toggle with: pac_event guitar 2 (on) / pac_event guitar 0 (off)."""
import sys
sys.argv=[sys.argv[0],'outfit2']
B='/mnt/user-data/outputs/token_build/'
exec(open('/home/claude/work/token/pacfile.py').read().split("root=part(")[0])
ANIM_GUITAR=ANIM.replace('?v=','?v=handd')%'token_guitar'
hide2=hide+'arms=1;arms_cyber=1;arms_plates_l=1;arms_plates_r=1;'
root=part('group','Token - guitar test',dict(OwnerName='self'),[
  part('entity2','hide player',dict(NoDraw=True,DrawShadow=True)),
  part('model2','token_base',dict(Model=model('token_base'),BoneMerge=True,ModelModifiers=hide2)),
  part('model2','token_outfit2',dict(Model=model('token_outfit2'),BoneMerge=True)),
  part('model2','token_handsd',dict(Model=model('token_handsd'),BoneMerge=True)),
  part('model2','token_gloves',dict(Model=model('token_gloves'),BoneMerge=True)),
  part('group','Guitar (pac_event guitar 2)',{},[
    part('event','show while guitar is on',dict(Event='command',Operator='equal',Arguments='guitar@@0@@0',Invert=True)),
    part('model2','token_guitar',dict(Model=model('token_guitar'),BoneMerge=True)),
    part('model2','token_sm_cig_mouth',dict(Model=model('token_sm_cig_mouth'),BoneMerge=True)),
    part('custom_animation','guitar stance',dict(URL=ANIM_GUITAR,AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
  ]),
])
out=B+'pac3_outfits/token_guitartest.txt'
open(out,'w',newline='\n').write('[1] = %s,\n'%lua(root,2)); print(out)
