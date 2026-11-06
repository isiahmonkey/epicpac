"""Token outfit builder -> one shared build folder with incremental compiles.
  python3 outfit.py base        # token_base: head, Gorilla arms, hair, fur hat, cyberware, face, ears, skin regions
  python3 outfit.py outfit1     # token_outfit1: only that outfit's clothes + jewelry (rides on token_base in PAC)
Everything lands in /mnt/user-data/outputs/token_build/ ; plans/<id>.json says which models + materials each PAC zip gets.
"""
import sys, os, json, token_kit as K
OUT='/mnt/user-data/outputs/token_build/'
OUTFITS={
 'outfit1':dict(desc='Misfits tank, Edgerunner denim pants, vinyl platforms, wallet chain, Valentino silver necklace',
   staged='/home/claude/work/token/staged_outfit1.pkl',
   hide_skin=['pelvis','thighs','calves','feet'],      # base skin regions covered by this outfit
   pieces={'torso_inner':'misfits_tank','legs':'denim_pants','feet':'vinyl_platform_black',
           'legs_acc':'wallet_chain_silver','neck_jewelry':'valentino_cross_silver'}),
}
oid=sys.argv[1]
allopts={g:o for m in K.LAYOUT.values() for g,o in m.items()}
K.KIT=OUT; K.KEEP=True; K.BATNAME=None
if oid=='base':
    M='token_base'; K.LAYOUT={M:dict(K.LAYOUT['token_body'])}; K.BODY_MODEL=M
else:
    O=OUTFITS[oid]; M='token_'+oid
    K.LAYOUT={M:{g:{opt:allopts[g][opt]} for g,opt in O['pieces'].items()}}; K.BODY_MODEL=None
    if os.path.exists(O['staged']):
        import pickle; K.P=pickle.load(open(O['staged'],'rb'))
K.DEFAULT_ON=set(K.LAYOUT[M])
plan=K.main()
os.makedirs(OUT+'plans',exist_ok=True)
entry=dict(model=M,materials=plan[M]['materials'],bodygroups=plan[M]['bodygroups'],tris=plan[M]['tris'])
if oid=='base':
    json.dump(entry,open(OUT+'plans/_base.json','w'),indent=1)
else:
    entry.update(desc=O['desc'],hide_skin=O['hide_skin'])
    json.dump(entry,open(OUT+'plans/%s.json'%oid,'w'),indent=1)
print(M,'tris',plan[M]['tris'],'materials',len(plan[M]['materials']))
