import json,struct,sys
def strip(src,dst,drop):
    b=open(src,'rb').read(); jl=struct.unpack_from('<I',b,12)[0]; J=json.loads(b[20:20+jl])
    J['nodes']=[n for n in J['nodes'] if n['name'] not in drop]; J['scenes'][0]['nodes']=list(range(len(J['nodes'])))
    js=json.dumps(J,separators=(',',':')).encode(); js+=b' '*((4-len(js)%4)%4); rest=b[20+jl:]
    open(dst,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(js)+len(rest))+struct.pack('<II',len(js),0x4E4F534A)+js+rest)
if __name__=='__main__': strip(sys.argv[1],sys.argv[2],sys.argv[3].split(','))
