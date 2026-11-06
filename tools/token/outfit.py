"""Build one self-contained outfit PAC kit for Token.  usage: python3 outfit.py outfit1"""
import sys, token_kit as K
OUTFITS={
 # every outfit: base body (head, Gorilla arms, hair, cyberware, face, ears) + fur hat
 'outfit1':dict(desc='Misfits tank, Edgerunner denim pants, vinyl platforms, wallet chain, Valentino silver necklace',
   skin=['torso','collar'],          # skin covered by pants/boots is dropped (pelvis, thighs, calves, feet)
   pieces={'torso_inner':'misfits_tank','legs':'denim_pants','feet':'vinyl_platform_black',
           'legs_acc':'wallet_chain_silver','neck_jewelry':'valentino_cross_silver'}),
}
oid=sys.argv[1]; O=OUTFITS[oid]; M='token_'+oid
base=dict(K.LAYOUT['token_body'])
allopts={g:o for m in K.LAYOUT.values() for g,o in m.items()}
groups={}
for g,o in base.items(): groups[g]=o                       # head + base kit, hat included
for g,opt in O['pieces'].items(): groups[g]={opt:allopts[g][opt]}
K.LAYOUT={M:groups}
K.DEFAULT_ON=set(groups)                                   # everything on; 'none' is the last option
K.BODY_REGIONS={r:c for r,c in K.BODY_REGIONS.items() if r in O['skin']}
K.BODY_MODEL=M; K.KIT='/mnt/user-data/outputs/%s_kit/'%M
K.KITZIP='%s_kit.zip'%M; K.PACZIP='%s_pac3.zip'%M; K.BATNAME='compile_%s.bat'%M
plan=K.main()
