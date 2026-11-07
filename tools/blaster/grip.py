"""CP handgun grip: the WeaponRight item frame relative to RightHand, from the gang handgun idles."""
import sys,numpy as np; sys.path[:0]=['/home/claude/work/anim','/home/claude/tools/scripts']
import cpanim
F='/mnt/user-data/uploads/V_Gmod/flat/source~archive~base~animations~npc~gameplay~man_average~gang~handgunboth~ma_gang_handgunboth_action_combat.anims'
N=cpanim.NAMES; I={n:i for i,n in enumerate(N)}
def grip():
    C=cpanim.clips(F); rels=[]
    for k in ('ovr_idle','aim_ovr_idle','idle_low'):
        c=cpanim.Clip(C[k])
        for t in np.linspace(0,c.dur,8,endpoint=False):
            W=c.world(t); rels.append(np.linalg.inv(W[I['RightHand']])@W[I['WeaponRight']])
    R=sum(r[:3,:3] for r in rels); U,_,Vt=np.linalg.svd(R); M=np.eye(4); M[:3,:3]=U@Vt; M[:3,3]=np.mean([r[:3,3] for r in rels],0)
    P=np.array([r[:3,3] for r in rels]); print('grip spread cm',(P.std(0)*100).round(2))
    return M
if __name__=='__main__': print(grip().round(3))
