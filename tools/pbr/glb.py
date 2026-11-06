"""Minimal glTF 2.0 (.glb) writer for STAGING: meshes in CP space (Z-up, face +Y) -> glTF (Y-up), PBR materials."""
import json,struct,io,numpy as np
from PIL import Image
R=np.array([[1,0,0],[0,0,1],[0,-1,0]],np.float32)          # CP (x,y,z) -> glTF (x, z, -y): proper rotation
def vnormals(p,t):
    n=np.cross(p[t[:,2]]-p[t[:,0]],p[t[:,1]]-p[t[:,0]])     # CP winding is clockwise -> this cross is outward
    vn=np.zeros_like(p)
    for k in range(3): np.add.at(vn,t[:,k],n)
    vn=vn/np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-12); bad=~np.isfinite(vn).all(1)|(np.abs(vn).sum(1)<1e-6); vn[bad]=[0,0,1]; return vn
class GLB:
    def __init__(s): s.bin=bytearray(); s.j=dict(asset=dict(version='2.0',generator='epicpac staging'),scenes=[dict(nodes=[])],scene=0,nodes=[],meshes=[],materials=[],textures=[],images=[],samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)],accessors=[],bufferViews=[]); s._img={}; s._keep={}
    def _view(s,data,target=None):
        while len(s.bin)%4: s.bin.append(0)
        o=len(s.bin); s.bin+=data; v=dict(buffer=0,byteOffset=o,byteLength=len(data))
        if target: v['target']=target
        s.j['bufferViews'].append(v); return len(s.j['bufferViews'])-1
    def _acc(s,a,ctype,typ,target,minmax=False):
        a=np.ascontiguousarray(a); d=dict(bufferView=s._view(a.tobytes(),target),componentType=ctype,count=len(a),type=typ)
        if minmax: d['min']=a.min(0).tolist(); d['max']=a.max(0).tolist()
        s.j['accessors'].append(d); return len(s.j['accessors'])-1
    def tex(s,im,key=None,jpeg=False):
        if im is None: return None
        k=key or id(im)
        if k in s._img and s._keep.get(k) is im: return s._img[k]
        s._keep=getattr(s,'_keep',{}); s._keep[k]=im          # keep alive: id() of a freed temp image gets reused
        b=io.BytesIO(); 
        if jpeg: im.convert('RGB').save(b,'JPEG',quality=92); mt='image/jpeg'
        else: im.save(b,'PNG',optimize=False,compress_level=3); mt='image/png'
        s.j['images'].append(dict(bufferView=s._view(b.getvalue()),mimeType=mt))
        s.j['textures'].append(dict(sampler=0,source=len(s.j['images'])-1)); s._img[k]=len(s.j['textures'])-1; return s._img[k]
    def material(s,name,base=None,color=(1,1,1,1),normal=None,nscale=1.0,mr=None,metal=0.0,rough=0.6,emis=None,emis_f=(0,0,0),alpha='OPAQUE',cutoff=0.5,double=False,ext=None):
        m=dict(name=name,pbrMetallicRoughness=dict(baseColorFactor=list(color),metallicFactor=metal,roughnessFactor=rough),alphaMode=alpha,doubleSided=double)
        if base is not None: m['pbrMetallicRoughness']['baseColorTexture']=dict(index=s.tex(base))
        if mr is not None: m['pbrMetallicRoughness']['metallicRoughnessTexture']=dict(index=s.tex(mr)); m['pbrMetallicRoughness']['metallicFactor']=1.0; m['pbrMetallicRoughness']['roughnessFactor']=1.0
        if normal is not None: m['normalTexture']=dict(index=s.tex(normal),scale=nscale)
        if emis is not None: m['emissiveTexture']=dict(index=s.tex(emis)); m['emissiveFactor']=list(emis_f)
        if alpha=='MASK': m['alphaCutoff']=cutoff
        if ext: m['extras']=ext
        s.j['materials'].append(m); return len(s.j['materials'])-1
    def mesh(s,name,pos,idx,uv,mat,normals=None):
        t=idx.reshape(-1,3).astype(np.int64); p=np.asarray(pos,np.float32)
        n=normals if normals is not None else vnormals(p,t)
        P=(p@R.T).astype(np.float32); N=(n@R.T).astype(np.float32)
        I=t[:,[0,2,1]].astype(np.uint32).ravel()               # flip to CCW for glTF
        prim=dict(attributes=dict(POSITION=s._acc(P,5126,'VEC3',34962,True),NORMAL=s._acc(N,5126,'VEC3',34962),TEXCOORD_0=s._acc(np.asarray(uv,np.float32),5126,'VEC2',34962)),indices=s._acc(I,5125,'SCALAR',34963),material=mat)
        s.j['meshes'].append(dict(name=name,primitives=[prim])); s.j['nodes'].append(dict(name=name,mesh=len(s.j['meshes'])-1)); s.j['scenes'][0]['nodes'].append(len(s.j['nodes'])-1)
    def save(s,path):
        while len(s.bin)%4: s.bin.append(0)
        s.j['buffers']=[dict(byteLength=len(s.bin))]
        js=json.dumps(s.j,separators=(',',':')).encode()
        while len(js)%4: js+=b' '
        out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(s.bin))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(s.bin),0x004E4942)+bytes(s.bin)
        open(path,'wb').write(out); return len(out)
def cp_normal(im,flip_g=False):
    """CP normal maps store XY only (B=0): rebuild Z for glTF"""
    a=np.asarray(im.convert('RGB')).astype(np.float32)/127.5-1; x,y=a[...,0],a[...,1]
    if flip_g: y=-y
    z=np.sqrt(np.clip(1-x*x-y*y,0,1))
    return Image.fromarray(((np.dstack([x,y,z])+1)*127.5).clip(0,255).astype(np.uint8))
def mr_map(rough,metal):
    """glTF metallicRoughness: G=roughness, B=metalness"""
    r=np.asarray(rough).astype(np.uint8); m=np.asarray(metal).astype(np.uint8)
    return Image.fromarray(np.dstack([np.zeros_like(r),r,m]))
