"""Thumb motion for hand D (the approved bare hand, worn under the gloves).

Hand D keeps Cyberpunk's thumb shape: its thumb mesh is the CP thumb moved by the hand fit Mh (a similarity), skinned to
Finger01 (CP Thumb1) and Finger02 (CP Thumb2); Finger0 only carries the ball of the thumb. The shared retarget map drives
Finger0 from CP Thumb1 and Finger01 from Thumb2, one joint off for this hand. Here the thumb joints get CP's own thumb
motion relative to the hand, carried through the same fit:
    R(Finger01) = R(hand) . R(hand bind)^T . Rm . K(Thumb1) . Rm^T . R(Finger01 bind)
    K(j) = CP hand bind . CP hand(t)^-1 . CP j(t) . CP j bind^-1        (rotation parts; Rm = rotation of Mh)
Finger0 is aimed so the Finger01 pivot follows CP's Thumb1 joint (CP moves it with InHandThumb).
check(): skins hand D's thumb with these rotations and compares it with the CP thumb deformed on Cyberpunk's own rig and
carried through Mh (ground truth). Must be ~0 for the mapping to be right."""
import sys, numpy as np
sys.path[:0] = ['/home/claude/work/guitar', '/home/claude/work/token', '/home/claude/work/anim', '/home/claude/tools/scripts', '/home/claude/work/build']
import retarget as RT, cpanim, handfit, basehand as BH, mesh, cr2w
VB = 'ValveBiped.Bip01_'; VIX = {n: i for i, n in enumerate(RT.vn)}; CPIDX = {n: i for i, n in enumerate(cpanim.NAMES)}
_MH = {}
def Mh(side):
    """hand fit of the base hand mesh (CP bind, tov space -> Valve bind), as used to build hand D"""
    if side not in _MH:
        g = mesh.decode(cr2w.load_loose(BH.A % side.lower())); bones = [BH.thumb_rename(n) for n in g['bones']]
        old = handfit.THUMB_FIT; handfit.THUMB_FIT = False
        try: D = handfit.part_D(bones, g['bonepos'])
        finally: handfit.THUMB_FIT = old
        M = D[('Left' if side == 'L' else 'Right') + 'Hand']; s = np.cbrt(np.linalg.det(M[:3, :3]))
        _MH[side] = (M, M[:3, :3] / s)
    return _MH[side]
def _base_local(n):
    import fingertest as FT
    return FT.BASE[n]
JOINTS = (('Finger01', 'Thumb1'), ('Finger02', 'Thumb2'))
def _rb(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def apply(out, W):
    """out: dict valve bone -> world rotation (bind frame), W: CP world matrices of the same frame. Edits out in place."""
    for side, S in (('L', 'Left'), ('R', 'Right')):
        hn = VB + side + '_Hand'
        if hn not in out: continue
        hv = out[hn]; Rhb = RT.VW[VIX[hn]][:3, :3]; Rm = Mh(side)[1]
        Hc = RT.tov(W[CPIDX[S + 'Hand']])[:3, :3]; Hc0 = RT.CW[S + 'Hand'][:3, :3]
        for vb, cj in JOINTS:
            Jc = RT.tov(W[CPIDX[S + 'Hand' + cj]])[:3, :3]; Jc0 = RT.CW[S + 'Hand' + cj][:3, :3]
            K = Hc0 @ Hc.T @ Jc @ Jc0.T
            out[VB + side + '_' + vb] = hv @ Rhb.T @ Rm @ K @ Rm.T @ RT.VW[VIX[VB + side + '_' + vb]][:3, :3]
        # Finger0 (the ball of the thumb) is aimed so the Finger01 pivot lands where CP's Thumb1 joint is: CP moves that joint
        # with its InHandThumb bone, which Kleiner has no match for (check() measured 0.7 in off without this)
        f0 = VIX[VB + side + '_Finger0']; f1 = VIX[VB + side + '_Finger01']
        out[VB + side + '_Finger0'] = hv @ Rhb.T @ RT.VW[f0][:3, :3]
        import vanim
        NW = vanim.full_world(out); Hd = NW[VIX[hn]] @ np.linalg.inv(RT.NW[VIX[hn]])
        K4h = RT.CW[S + 'Hand'] @ np.linalg.inv(RT.tov(W[CPIDX[S + 'Hand']]))
        T1 = (Hd @ Mh(side)[0] @ K4h @ np.r_[RT.tov(W[CPIDX[S + 'HandThumb1']])[:3, 3], 1])[:3]
        d0 = NW[f1][:3, 3] - NW[f0][:3, 3]; d1 = T1 - NW[f0][:3, 3]
        out[VB + side + '_Finger0'] = _rb(d0, d1) @ out[VB + side + '_Finger0']
    return out
def wrap(fn):
    def rots(W): return apply(fn(W), W)
    rots.__name__ = 'thumb_' + fn.__name__
    return rots
def check(times=np.arange(0, 30, 0.5)):
    """worst distance (in) between hand D's thumb joints/tip as skinned in the game and CP's thumb motion carried through Mh"""
    import vanim, gseq
    worst = {}
    for side, S in (('L', 'Left'), ('R', 'Right')):
        M = Mh(side)[0]; e = []
        for t in times:
            W = gseq.SONGS[0].world(t % gseq.SONGS[0].dur)
            NW = vanim.full_world(apply(vanim.valve_world_rots_W(W), W))
            h = VIX[VB + side + '_Hand']; Hd = NW[h] @ np.linalg.inv(RT.NW[h])
            K4h = RT.CW[S + 'Hand'] @ np.linalg.inv(RT.tov(W[CPIDX[S + 'Hand']]))
            c1, c2 = RT.CW[S + 'HandThumb1'][:3, 3], RT.CW[S + 'HandThumb2'][:3, 3]; tip = c2 + (c2 - c1) * 0.8
            for cj, vb, p in (('Thumb1', 'Finger01', c2), ('Thumb2', 'Finger02', tip)):     # each point moves with the joint above it
                K4 = K4h @ RT.tov(W[CPIDX[S + 'Hand' + cj]]) @ np.linalg.inv(RT.CW[S + 'Hand' + cj])
                truth = (Hd @ M @ K4 @ np.r_[p, 1])[:3]
                j = VIX[VB + side + '_' + vb]; game = (NW[j] @ np.linalg.inv(RT.NW[j]) @ M @ np.r_[p, 1])[:3]
                e.append(np.linalg.norm(truth - game))
        worst[side] = (round(float(np.mean(e)), 3), round(float(np.max(e)), 3))
    return worst
if __name__ == '__main__':
    import vanim
    print('thumb mapping error (mean, max in):', check())
    # the old shared map for comparison
    def old_check():
        global apply
        a = apply; apply = lambda out, W: out
        try: return check()
        finally: apply = a
    print('old shared map:', old_check())
