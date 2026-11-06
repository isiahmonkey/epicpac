import struct
def parse(b):
    assert b[:4]==b'CR2W'
    tables=[struct.unpack_from('<III',b,40+12*i) for i in range(10)]
    so,sc,_=tables[0]
    sraw=b[so:so+sc]
    def s(o):
        e=sraw.index(b'\0',o); return sraw[o:e].decode('utf8','replace')
    names=[s(struct.unpack_from('<II',b,tables[1][0]+8*i)[0]) for i in range(tables[1][1])]
    imports=[]
    for i in range(tables[2][1]):
        o,ci,fl=struct.unpack_from('<IHH',b,tables[2][0]+8*i); imports.append((s(o),names[ci] if ci<len(names) else ci))
    chunks=[]
    for i in range(tables[4][1]):
        ci,of,par,dsz,doff,_,_=struct.unpack_from('<HHIIIII',b,tables[4][0]+24*i); chunks.append((names[ci],dsz,doff))
    bufs=[struct.unpack_from('<IIIIII',b,tables[5][0]+24*i) for i in range(tables[5][1])]
    return dict(names=names,imports=imports,chunks=chunks,bufs=bufs,tables=tables)

def props(b, r, off, end):
    """parse classic RED4 property list starting at off; returns list (name,type,valbytes,valoff)"""
    n=r['names']; out=[]
    p=off
    if b[p]==0: p+=1
    while p+2<=end:
        ni=struct.unpack_from('<H',b,p)[0]
        if ni==0: break
        ti,sz=struct.unpack_from('<HI',b,p+2)
        out.append((n[ni],n[ti],p+8,p+4+sz)); p+=4+sz
    return out

PRIM={'Uint8':'<B','Int8':'<b','Uint16':'<H','Int16':'<h','Uint32':'<I','Int32':'<i','Uint64':'<Q','Int64':'<q','Float':'<f','Bool':'<B'}
def val(b,r,tp,p,end):
    n=r['names']
    if tp in PRIM: return struct.unpack_from(PRIM[tp],b,p)[0]
    if tp=='TweakDBID': return struct.unpack_from('<Q',b,p)[0]
    if tp=='String':
        x=b[p]; neg=x&0x80; v=x&0x3f; sh=6; q=p+1
        if x&0x40:
            while True:
                c=b[q]; q+=1; v|=(c&0x7f)<<sh; sh+=7
                if not c&0x80: break
        return b[q:q+v].decode('utf8','replace') if neg else b[q:q+2*v].decode('utf16','replace')
    if tp=='CName': return n[struct.unpack_from('<H',b,p)[0]]
    if tp.startswith('handle:') or tp.startswith('whandle:'): return ('#',struct.unpack_from('<i',b,p)[0]-1)
    if tp.startswith('rRef:') or tp.startswith('raRef:'):
        i=struct.unpack_from('<H',b,p)[0]; return ('ref',r['imports'][i-1][0] if 0<i<=len(r['imports']) else i)
    if tp=='DataBuffer' or tp=='serializationDeferredDataBuffer' or tp=='SharedDataBuffer':
        return ('buf',struct.unpack_from('<H',b,p)[0])
    if tp.startswith('[') and ']' in tp:
        n_=int(tp[1:tp.index(']')]); et=tp[tp.index(']')+1:]
        cnt=struct.unpack_from('<I',b,p)[0]; p+=4
        if et in PRIM:
            sz=struct.calcsize(PRIM[et]); return [struct.unpack_from(PRIM[et],b,p+i*sz)[0] for i in range(cnt)]
    if tp.startswith('array:') or tp.startswith('static:'):
        if tp.startswith('static:'):
            et=tp.split(':',1)[1].split(',',1)[1]
        et=tp.split(':',1)[1] if tp.startswith('array:') else et
        cnt=struct.unpack_from('<I',b,p)[0]; p+=4
        out=[]
        if et in PRIM:
            sz=struct.calcsize(PRIM[et]); return [struct.unpack_from(PRIM[et],b,p+i*sz)[0] for i in range(cnt)]
        fixed={'CName':2}.get(et) or (4 if et.startswith('handle:') else 2 if (et.startswith('raRef') or et.startswith('rRef')) else None)
        if et.startswith('array:'):
            for i in range(cnt):
                c2=struct.unpack_from('<I',b,p)[0]; v=val(b,r,et,p,end); out.append(v)
                ie=et.split(':',1)[1]; p+=4+c2*(struct.calcsize(PRIM[ie]) if ie in PRIM else 2)
            return out
        if fixed:
            for i in range(cnt): out.append(val(b,r,et,p+i*fixed,end))
            return out
        if cnt==0 and end-p>4:            # some WolvenKit-written files leave the count 0: read entries until the property ends
            while p<end-2:
                d,p=struct_(b,r,p,end); out.append(d)
            return out
        for i in range(cnt):
            d,p=struct_(b,r,p,end); out.append(d)
        return out
    if end-p==2: return n[struct.unpack_from('<H',b,p)[0]]
    d,_=struct_(b,r,p,end); return d
def struct_(b,r,p,end):
    n=r['names']; d={}
    if b[p]==0: p+=1
    while p+2<=end:
        ni=struct.unpack_from('<H',b,p)[0]
        if ni==0: p+=2; break
        ti,sz=struct.unpack_from('<HI',b,p+2)
        try: d[n[ni]]=val(b,r,n[ti],p+8,p+4+sz)
        except Exception as e: d[n[ni]]=('ERR',n[ti],str(e))
        p+=4+sz
    return d,p
def chunk(b,r,i):
    cn,dsz,doff=r['chunks'][i]; return cn,struct_(b,r,doff,doff+dsz)[0]

def load_loose(path):
    """Return segs list like archive extraction: [cr2w bytes, buf1, buf2...]"""
    import sys
    sys.path.insert(0,'/home/claude/tools/scripts')
    import rdar
    b=open(path,'rb').read()
    r=parse(b)
    segs=[b]
    for (flags,idx,off,dsz,msz,crc) in r['bufs']:
        raw=b[off:off+dsz]
        segs.append(rdar.unkark(raw,msz) if dsz!=msz else raw)
    return segs
