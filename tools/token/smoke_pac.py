"""PAC3 'Smoke & drink' group for Token: stance animation + bone-merged props shown on cue, ember / tip smoke /
exhale / ash particles, Zippo flame + light, ignition sound. Timing: one-shot windows during the intro, then
ratio_timer windows that repeat with the loop (Emmerich's proven event pattern)."""
import sys,json
sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/anim']
SNDREPO='https://raw.githubusercontent.com/isiahmonkey/v-pac3/main/sounds/'
def build(part,Vec,Ang,model,ANIM,timing):
    tm=timing; BL=tm['blend']; T0=tm['loop_start']; L=tm['loop_period']; n=[0]
    def nm(s): n[0]+=1; return '%s #%d'%(s,n[0])
    def ev(name,evt,args,children,op=None):
        d=dict(Event=evt,Arguments=args,Invert=True,RootOwner=True,AffectChildrenOnly=True)
        if op: d['Operator']=op
        return part('event',nm(name),d,children)
    def win(p,a,b):
        """show part p only in [a,b) (seconds after the group appears, blend included)"""
        if b<=T0+0.05: return ev('%.2f-%.2fs'%(a,b),'timerx2','%.3f@@%.3f@@1@@0'%(a,b),[p])
        g=T0-0.05; a2=a-g; off=(L-(a2%L))%L; ratio=min((b-a)/L,1.0)
        inner=ev('every %.1fs @ +%.2fs'%(L,a2%L),'ratio_timer','%.4f@@%.4f@@%.6f@@1'%(L,off,ratio),[p])
        return ev('loop running','timerx','%.3f@@1@@0'%g,[inner],'above')
    def wins(mk,ws):   # one copy of the part per window
        return [win(mk(i),a+BL,b+BL) for i,(a,b) in enumerate(ws)]
    A=tm['anchors']
    def mdl(m,i): return part('model2',nm(m),dict(Model=model(m),BoneMerge=True))
    kids=[part('event','show while smoke is on',dict(Event='command',Operator='equal',Arguments='smoke@@0@@0',Invert=True)),
          part('custom_animation','smoke & drink stance',dict(URL=ANIM%'token_smoke',AnimationType='stance',Interpolation='linear',StopOnHide=True,Rate=1)),
          part('model2','token_sm_glass',dict(Model=model('token_sm_glass'),BoneMerge=True))]
    props=[]
    for m,ws in tm['props'].items(): props+=wins(lambda i,m=m:mdl(m,i),ws)
    fx=[]
    def ember(bone,pos,size=0.35,alpha=0.85):
        return lambda i: part('sprite',nm('ember'),dict(Bone=bone,Position=Vec(pos),SpritePath='sprites/glow04_noz',Size=size,Color=Vec((255,110,40)),Alpha=alpha))
    def wisps(bone,pos):
        return lambda i: part('particles',nm('tip smoke'),dict(Bone=bone,Position=Vec(pos),Material='particle/smokesprites_0001',Color1=Vec((175,175,180)),Color2=Vec((150,150,155)),
            StartSize=0.2,EndSize=2.4,DieTime=2.2,NumberParticles=1,FireDelay=0.2,Velocity=0.6,Spread=1,Gravity=Vec((0,0,16)),AirResistance=6,Collide=False,Lighting=False,
            StartAlpha=26,EndAlpha=0,RandomRollSpeed=0.5))
    for key,bone,pos in (('lit_mouth','head',A['tip_mouth']),('lit_smoke','left hand',A['tip_smoke']),('lit_hand','left hand',A['tip_hand'])):
        ws=tm['fx'][key]; fx+=wins(ember(bone,pos),ws)+wins(wisps(bone,pos),ws)
    for t,key in tm['flares']:
        bone,pos={'mouth':('head',A['tip_mouth']),'smoke':('left hand',A['tip_smoke']),'hand':('left hand',A['tip_hand'])}[key]
        fx+=wins(ember(bone,pos,1.0,1.0),[(t-0.3,t+0.9)])
    for t in tm['ash']:
        fx+=wins(lambda i: part('particles',nm('ash flick'),dict(Bone='left hand',Position=Vec(A['tip_hand']),Material='particle/particle_smokegrenade',Color1=Vec((90,90,90)),Color2=Vec((60,60,60)),
            StartSize=0.35,EndSize=0.15,DieTime=1.2,NumberParticles=4,FireDelay=0.05,Velocity=12,Spread=0.6,Gravity=Vec((0,0,-260)),Collide=True,Lighting=True,StartAlpha=220,EndAlpha=0)),[(t,t+0.25)])
    mouth=[A['filter_mouth'][0],A['filter_mouth'][1],A['filter_mouth'][2]*0.35]
    for t,big in tm['exhale']:
        fx+=wins(lambda i,big=big: part('particles',nm('exhale'),dict(Bone='head',Position=Vec(mouth),Angles=Ang((10,-90,0)),Material='particle/smokesprites_0001',
            Color1=Vec((185,185,185)),Color2=Vec((160,160,160)),StartSize=0.6,EndSize=5 if big else 3,DieTime=1.6 if big else 1.1,NumberParticles=1,FireDelay=0.07,
            Velocity=3.5 if big else 2.5,Spread=0.35,Gravity=Vec((0,0,7)),AirResistance=10,Collide=False,Lighting=False,StartAlpha=42 if big else 30,EndAlpha=0,RandomRollSpeed=0.8)),
            [(t,t+(1.1 if big else 0.5))])
    a,b=tm['flame']
    fx+=wins(lambda i: part('sprite',nm('Zippo flame'),dict(Bone='left hand',Position=Vec(A['flame']),SpritePath='sprites/flamelet1',Size=0.9,SizeY=1.6,Color=Vec((255,200,120)))),[(a,b)])
    fx+=wins(lambda i: part('light2',nm('Zippo light'),dict(Bone='left hand',Position=Vec(A['flame']),Brightness=1.5,Size=60,Color=Vec((1,0.65,0.3)),Style=1)),[(a,b)])
    snd=[]
    for t,k,nv in tm['sounds']:
        path=';'.join(SNDREPO+'%s_%d.ogg'%(k,i) for i in range(nv))
        snd+=wins(lambda i,path=path: part('sound2',nm('ignition sound'),dict(Path=path,Volume=0.9,Radius=600,Bone='left hand',StopOnHide=False)),[(t,t+0.4)])
    return part('group','Smoke & drink (pac_event smoke 2)',{},kids+[part('group','Props (timed)',{},props),part('group','Ember, smoke, ash & flame',{},fx),part('group','Ignition sound',{},snd)])
