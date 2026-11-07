import sys; sys.path[:0]=['/home/claude/tools/scripts','/home/claude/work/build']
import rdar
D='/mnt/user-data/uploads/Outfit 3--archive/pc/mod/'
AR=[rdar.Archive(D+a) for a in ('tq_judy_gloves.archive','tq_judy_glove_stickers.archive')]
def fnv(s):
    h=0xcbf29ce484222325
    for b in s.lower().replace('/','\\').encode(): h^=b; h=(h*0x100000001b3)&0xFFFFFFFFFFFFFFFF
    return h
def segs(path):
    h=fnv(path)
    for A in AR:
        for f in A.files:
            if f['hash']==h: return A.extract(f)
    return None
