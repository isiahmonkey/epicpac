import sys,json,os; sys.path.insert(0,'/home/claude/tools/scripts'); sys.path.insert(0,'/home/claude/work/build')
import cr2w,mats,modres,names
UP='/mnt/user-data/uploads/'
def local(p):
    q=p.replace('\\','/'); q=q.split('/',1)[1] if q.startswith(('base/','ep1/','engine/')) else q
    full=p.replace('\\','/')
    for f in (UP+q, UP+'V_Gmod/source/archive/'+full, UP+'archive/'+full, UP+'V_Gmod/flat/source~archive~'+full.replace('/','~')):
        if os.path.exists(f): return f
    return None
def segs_of(p):
    if not p: return None
    s=modres.get(p)
    if s: return s
    f=local(p); return cr2w.load_loose(f) if f else None
def mesh_mats(p,app):
    s=segs_of(p)
    if s is None: return None
    b,r,m,apps=mats.mesh_info(s)
    a=app if app in apps else ('default' if 'default' in apps else list(apps)[0])
    ch,refs=mats.appearance_refs(s,a)
    return dict(app=a,chunks=ch,refs=refs)
if __name__=='__main__':
    A=json.load(open('outfit_items.json')); need=set(); rep={}
    for k,v in A.items():
        for c in v['comps']:
            mm=mesh_mats(c['mesh'],c['app'])
            rep[c['mesh']+'|'+str(c['app'])]=mm
            if mm is None: print('MISSING MESH',k,c['mesh']); continue
            for mn,rs in mm['refs'].items():
                for r_ in rs: need.add(r_)
    json.dump(rep,open('garment_mats.json','w'),indent=1)
    have=[n for n in sorted(need) if local(n) or modres.get(n)]
    miss=[n for n in sorted(need) if not (local(n) or modres.get(n))]
    print(len(need),'refs; have',len(have),'missing',len(miss)); print('\n'.join(miss[:80]))
