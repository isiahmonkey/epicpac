"""Keep Token's real hand mesh (hand D + gloves, 24% larger than V's) out of the guitar.

 finger_points(side)  skin points of each finger segment in that bone's bind frame (inches), sub-sampled
 depth(points_world, Gp)  how deep (inches) world points sit inside the guitar solid (gcheck's voxel depth field)
 settle_finger(...)   after the fret IK: bends one fretting finger (knuckle curl + spread, middle and end joints) so its
                      tip stays on the fret target while no point of the finger is inside the neck
 hand_need(NW, side)  for the strumming hand: deepest point of the hand mesh inside the body (m), used to lift the hand
All depths come from the same field the gate (handqa / gcheck) measures with."""
import os, numpy as np
import retarget as RT
VB = 'ValveBiped.Bip01_'; VIX = {n: i for i, n in enumerate(RT.vn)}
_G = None
def G():
    global _G
    if _G is None:
        import gcheck; _G = gcheck
    return _G
_FP = {}
def finger_points(side, per=200):
    if side not in _FP:
        g = G(); Pp, N, B, W, dom = g.HV[side]; out = {}; rng = np.random.default_rng(0)
        for f in range(5):
            for k in ('', '1', '2'):
                n = VB + '%s_Finger%d%s' % (side, f, k)
                if n not in g.NODES: continue
                sel = np.where(dom == g.NODES[n])[0]
                if len(sel) > per: sel = rng.choice(sel, per, replace=False)
                j = VIX[n]; out[n] = ((np.linalg.inv(RT.NW[j]) @ np.c_[Pp[sel], np.ones(len(sel))].T).T)[:, :3]
        hn = VB + side + '_Hand'; sel = np.where(dom == g.NODES[hn])[0]
        if len(sel) > 4 * per: sel = rng.choice(sel, 4 * per, replace=False)
        out[hn] = ((np.linalg.inv(RT.NW[VIX[hn]]) @ np.c_[Pp[sel], np.ones(len(sel))].T).T)[:, :3]
        _FP[side] = out
    return _FP[side]
def to_item(p, Gp):
    q = (np.linalg.inv(Gp) @ np.c_[p, np.ones(len(p))].T).T[:, :3]
    return (RT.C.T @ (q / RT.S).T).T
def depth(p, Gp):
    """inches inside the guitar"""
    return G().depth_of(to_item(p, Gp)) / 0.0254
def Gp_of(NW):
    import gseq
    vch = VIX[VB + 'Spine4']; return NW[vch] @ np.linalg.inv(RT.NW[vch]) @ gseq.G_BIND
def hand_need(NW, side, margin=0.002):
    """metres the hand must move out of the guitar (deepest skin/glove point + margin), 0 if clear"""
    Gp = Gp_of(NW); FP = finger_points(side); worst = 0.0
    for n, loc in FP.items():
        if not len(loc): continue
        p = (NW[VIX[n]] @ np.c_[loc, np.ones(len(loc))].T).T[:, :3]
        worst = max(worst, float(depth(p, Gp).max()))
    return worst * 0.0254 + margin if worst > 0 else 0.0
def _rot(a, ang):
    a = a / np.linalg.norm(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
def settle_finger(ch, Rs, p0, offs, T, Gp, hand_R, lim, w_depth=200.0):
    """ch: 3 bone names; Rs: their world rotations after the fret IK; p0: knuckle position; offs: child offsets incl. tip;
    T: target tip (world inches). Returns new Rs."""
    from scipy.optimize import minimize
    FP = finger_points(ch[0][17])   # 'L' / 'R'
    locs = [FP.get(c) for c in ch]
    def build(x):
        a0, b0, a1, a2 = x
        R0 = _rot(Rs[0][:, 1], b0) @ _rot(Rs[0][:, 2], a0) @ Rs[0]
        D1 = R0 @ Rs[0].T; R1 = _rot((D1 @ Rs[1])[:, 2], a1) @ D1 @ Rs[1]
        D2 = R1 @ Rs[1].T; R2 = _rot((D2 @ Rs[2])[:, 2], a2) @ D2 @ Rs[2]
        return [R0, R1, R2]
    def fk(R):
        P = [p0]
        for k in range(3): P.append(P[-1] + R[k] @ offs[k])
        return P
    def cost(x):
        R = build(x); P = fk(R); c = np.sum((P[3] - T) ** 2) * 4.0 + 0.05 * np.sum(np.asarray(x) ** 2)
        for k in range(3):
            if locs[k] is None or not len(locs[k]): continue
            d = depth(P[k] + locs[k] @ R[k].T, Gp); c += w_depth * np.sum(np.maximum(d, 0) ** 2)
        import gseq
        for k, par in ((0, hand_R), (1, R[0]), (2, R[1])):
            cu = gseq._curl(par, R[k]); lo, hi = lim[k]; c += 20.0 * (max(0, lo - cu) ** 2 + max(0, cu - hi) ** 2)
        return c
    x0 = np.zeros(4)
    if cost(x0) - 4.0 * np.sum((fk(Rs)[3] - T) ** 2) - 0.0 < 1e-9:   # nothing inside the neck: keep the IK answer
        return Rs
    r = minimize(cost, x0, method='Powell', options=dict(maxiter=600, xtol=1e-3, ftol=1e-6))
    return build(r.x)
def settle_thumb(R, NW_fn, side='L', w_depth=200.0):
    """bend the thumb (Finger01 / Finger02 curl and spread) the least amount that takes it out of the neck.
    R: valve world rotations (edited in place); NW_fn: R -> world matrices (FK)."""
    from scipy.optimize import minimize
    n1, n2 = VB + side + '_Finger01', VB + side + '_Finger02'
    if n1 not in R or n2 not in R: return R
    FP = finger_points(side); R1, R2 = R[n1].copy(), R[n2].copy()
    NW = NW_fn(R); Gp = Gp_of(NW); p1 = NW[VIX[n1]][:3, 3]; off2 = RT.NL[VIX[n2]][:3, 3]
    def build(x):
        a1, b1, a2 = x
        Q1 = _rot(R1[:, 1], b1) @ _rot(R1[:, 2], a1) @ R1; Q2 = _rot((Q1 @ R1.T @ R2)[:, 2], a2) @ Q1 @ R1.T @ R2
        return Q1, Q2
    def cost(x):
        Q1, Q2 = build(x); p2 = p1 + Q1 @ off2; c = 1.0 * np.sum(np.asarray(x) ** 2)
        for p, Q, loc in ((p1, Q1, FP.get(n1)), (p2, Q2, FP.get(n2))):
            if loc is not None and len(loc): c += w_depth * np.sum(np.maximum(depth(p + loc @ Q.T, Gp), 0) ** 2)
        return c
    if cost(np.zeros(3)) < 1e-9: return R
    r = minimize(cost, np.zeros(3), method='Powell', options=dict(maxiter=400, xtol=1e-3, ftol=1e-7))
    R[n1], R[n2] = build(r.x); return R
