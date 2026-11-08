"""Render Token (outfit 2) playing the guitar with hand D + the Judy gloves, as the game will pose it (gseq + fretting +
clearance). python3 grender.py out.png t1,t2,... [yaw_deg] [zoom: body|hands]"""
import sys, os, numpy as np
sys.path[:0] = ['/home/claude/work/guitar', '/home/claude/work/smoke', '/home/claude/work/drink', '/home/claude/tools/scripts']
os.environ.setdefault('FRET', '1')
import gcheck as GC, gseq, retarget as RT, render as R
from PIL import Image
P = GC.P; K = P.K
PROPS = ['token_guitar', 'token_sm_cig_mouth']
PM = {}
for m in PROPS:
    for k, v in P.load(K + 'modelsrc/%s_body.smd' % m).items(): PM[k] = v
TEX = {}
def tex(m):
    if m not in TEX:
        f = K + 'materialsrc/%s.tga' % m; TEX[m] = Image.open(f) if os.path.exists(f) else None
    return TEX[m]
ALPHA = ('dec', 'kng', 'mlt', 'mtx', 'sticker', 'lashes', 'brows', 'hair', 'coatfrizz', 'coatfur', 'hatfur')
def parts_at(t, hide=('token_hat', 'token_hatcap', 'token_hatfur')):
    W = gseq.world_at(t); M = P.pose_mats(GC._C(lambda _: W), t); out = []
    for m, (Pp, N, UV, B, Wt) in list(P.MESH.items()) + list(PM.items()):
        if m in hide: continue
        p, _ = P.skinned(M, Pp, N, B, Wt); d = dict(pos=p, idx=np.arange(len(p)), uv=UV)
        tx = tex(m)
        if tx is not None: d['tex'] = tx
        if any(a in m for a in ALPHA): d['alpha'] = 1
        out.append(d)
    return out, M
def focus(M, zoom):
    sp = (M[GC.NODES['ValveBiped.Bip01_Spine4']] @ RT.NW[RT.vn.index('ValveBiped.Bip01_Spine4')])[:3, 3]
    if zoom == 'hands':
        hl = (M[GC.NODES['ValveBiped.Bip01_L_Hand']] @ RT.NW[RT.vn.index('ValveBiped.Bip01_L_Hand')])[:3, 3]
        hr = (M[GC.NODES['ValveBiped.Bip01_R_Hand']] @ RT.NW[RT.vn.index('ValveBiped.Bip01_R_Hand')])[:3, 3]
        c = (hl + hr) / 2; e = np.array([1, 1, 0.5625]) * max(np.linalg.norm(hl - hr) / 2 + 6, 10)
    else: e = np.array([40, 40, 22.5]); c = sp + np.array([0, 0, -12.0])
    return (c - e, c + e)
if __name__ == '__main__':
    out = sys.argv[1]; times = [float(x) for x in sys.argv[2].split(',')]
    yaw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0; zoom = sys.argv[4] if len(sys.argv) > 4 else 'body'
    ims = []
    for t in times:
        ps, M = parts_at(t)
        ims.append(R.view(ps, None, yaw=np.radians(yaw), size=(1920, 1080), focus=focus(M, zoom)))
    if len(ims) == 1: ims[0].save(out)
    else:
        S = Image.new('RGB', (960 * 2, 540 * ((len(ims) + 1) // 2)))
        for i, im in enumerate(ims): S.paste(im.resize((960, 540)), ((i % 2) * 960, (i // 2) * 540))
        S.save(out)
    print(out)
