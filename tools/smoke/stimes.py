"""Cue sheet: when each prop / effect / sound is on (seconds from the moment the PAC group is shown, before pacgen's blend-in)."""
import sys; sys.path[:0]=['/home/claude/work/smoke','/home/claude/work/anim']
import sseq,cues
BLEND=0.6
T=sseq.build_intro()
SMOKE_GRIP={'stand__rh_cigarette__01__drop_ash__03':(0.57,2.3),'stand__rh_cigarette__01__smoke__01':(0.77,4.77),'stand__rh_cigarette__01__smoke__02':(0.9,3.6)}
def windows():
    """prop name -> list of (start,end) in timeline seconds (no blend offset); loop windows given for the first loop pass"""
    w={'token_sm_glass':[(0,1e9)]}
    i0=sseq.INTRO
    w['token_sm_cig']=[(T['cig_show'],T['sm_in']+0.9)]
    w['token_sm_cig_smoke']=[(T['sm_in']+0.9,T['lips']),(T['take'],T['sm2']+3.6)]
    w['token_sm_cig_mouth']=[(T['lips'],T['take'])]
    w['token_sm_zippo']=[(T['zippo_show'],T['open']),(T['close'],T['zippo_hide'])]
    w['token_sm_zippo_open']=[(T['open'],T['close'])]
    hand=[(T['sm2']+3.6,None)]
    # loop: resting grip except the smoke-grip windows
    sm=[]
    for st,nm in sseq.LEFT:
        if nm in SMOKE_GRIP: a,b=SMOKE_GRIP[nm]; sm.append((i0+st+a,i0+st+b))
    w['loop_smoke']=sm
    return w
def props_at(t):
    w=windows(); out=['token_sm_glass']; i0=sseq.INTRO
    if t>=sseq.INTRO:
        tl=i0+((t-i0)%sseq.LOOP)
        if t>=T['sm2']+3.6 and tl<i0: pass
        insm=any(a<=tl<b for a,b in w['loop_smoke'])
        out.append('token_sm_cig_smoke' if insm else 'token_sm_cig'); return out
    for k in ('token_sm_cig','token_sm_cig_smoke','token_sm_cig_mouth','token_sm_zippo','token_sm_zippo_open'):
        if any(a<=t<b for a,b in w[k]): out.append(k)
    if T['sm2']+3.6<=t: out.append('token_sm_cig')
    return out

def timing(anim_json):
    """everything the PAC builder needs, in timeline seconds (the builder adds the blend-in)"""
    import json,numpy as np,cues
    J=json.load(open(anim_json)); d=[1/f['FrameRate'] for f in J['FrameData']]; r=J['RestartFrame']
    P=sum(d)-sum(d[:r-1])                      # PAC loop period as the file actually plays it
    w=windows(); i0=sseq.INTRO; L=sseq.LOOP
    # loop windows (first pass, timeline seconds) for the two hand grips
    sm=sorted(w['loop_smoke']); idle=[]; cur=i0
    for a,b in sm:
        if a>cur: idle.append((cur,a))
        cur=b
    if cur<i0+L: idle.append((cur,i0+L))
    take_end=T['sm2']+3.6
    props={'token_sm_cig':w['token_sm_cig']+[(take_end,i0)]+idle,
           'token_sm_cig_smoke':w['token_sm_cig_smoke']+sm,
           'token_sm_cig_mouth':w['token_sm_cig_mouth'],
           'token_sm_zippo':w['token_sm_zippo'],'token_sm_zippo_open':w['token_sm_zippo_open']}
    lit=T['flame']+0.45
    fx={'lit_mouth':[(lit,T['take'])],'lit_smoke':[(T['take'],take_end)]+sm,'lit_hand':[(take_end,i0)]+idle}
    # clip cues
    def grip_at(t):
        if t<i0:
            if T['lips']<=t<T['take']: return 'mouth'
            return 'smoke' if T['take']<=t<take_end else 'hand'
        return 'smoke' if any(a<=t<b for a,b in sm) else 'hand'
    flares=[]; ash=[]; exhale=[(T['flame']+0.75,False),(T['flame']+1.3,True)]   # puffs while lighting
    clips=[(T['sm2'],'stand__rh_cigarette__01__smoke__02')]+[(i0+st,nm) for st,nm in sseq.LEFT]
    for st,nm in clips:
        for t,c,e,f in cues.clip_events(cues.CIG,nm):
            k=cues.kind(c,e,f); tt=st+t
            if k=='ember': flares.append((tt,grip_at(tt)))
            elif k=='ash': ash.append(tt)
            elif k in ('mouth_smoke','mouth_smoke_small'): exhale.append((tt,k=='mouth_smoke'))
    return dict(blend=BLEND,loop_start=BLEND+i0,loop_period=P,props=props,fx=fx,flares=flares,ash=ash,exhale=sorted(exhale),
                flame=(T['flame'],T['close']),sounds=[(T['open'],'v_zippo_open',4),(T['close'],'v_zippo_close',3)])
