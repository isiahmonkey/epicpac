import sys, struct, io
sys.path.insert(0,'/home/claude/tools/scripts')
import cr2w
from PIL import Image
DXGI={'BC1':71,'BC2':74,'BC3':77,'BC4':80,'BC5':83,'BC6H':95,'BC7':98,'RGBA8':28,'R8':61}
CMAP={'TCM_DXTNoAlpha':'BC1','TCM_DXTAlpha':'BC3','TCM_DXTAlphaLinear':'BC3','TCM_Normalmap':'BC5','TCM_Normals':'BC5','TCM_Normals_DEPRECATED':'BC5',
      'TCM_QualityR':'BC4','TCM_QualityRG':'BC5','TCM_QualityColor':'BC7','TCM_HalfHDR':'BC6H','TCM_HalfHDR_Unsigned':'BC6H','TCM_RGBE':'BC6H'}
def info(segs):
    b=segs[0]; r=cr2w.parse(b)
    _,t=cr2w.chunk(b,r,0)
    blob=[i for i,(c,_,_) in enumerate(r['chunks']) if c.startswith('rendRenderTextureBlob')][0]
    _,bl=cr2w.chunk(b,r,blob)
    return t,bl,r
def load(segs, mip=0):
    t,bl,r=info(segs)
    w,h=t.get('width'),t.get('height')
    st=t.get('setup',{}); comp=st.get('compression','TCM_None')
    mips=bl['header']['mipMapInfo']; m=mips[mip]
    data=segs[-1]
    off=m['placement'].get('offset',0); size=m['placement']['size']
    bias=st.get('platformMipBiasPC',0)
    w0,h0=w,h
    w>>=mip+bias; h>>=mip+bias; w=max(w,1); h=max(h,1)
    if bias and m['layout']['rowPitch']>=((w0>>mip)+3)//4*8 and m['placement']['size']>=((w0>>mip)*(h0>>mip))//2:   # mip chain still starts at full res (mod-authored)
        w,h=max(w0>>mip,1),max(h0>>mip,1); fullres=True
    else: fullres=False
    raw=data[off:off+size]
    fmt=CMAP.get(comp)
    if fmt is None:
        rf=st.get('rawFormat','TRF_TrueColor')
        bpp=m['layout']['rowPitch']//w
        if bpp==4: return Image.frombuffer('RGBA',(w,h),raw[:w*h*4],'raw','RGBA',m['layout']['rowPitch'],1)
        if bpp==1: return Image.frombuffer('L',(w,h),raw[:w*h],'raw','L',m['layout']['rowPitch'],1)
        raise ValueError('raw fmt %s bpp %s'%(rf,bpp))
    # sanity from pitch
    bpb=m['layout']['rowPitch']//max(1,(w+3)//4) if not fullres else m['placement']['size']//max(1,((w+3)//4)*((h+3)//4))
    if fmt in('BC1','BC4') and bpb==16: fmt={'BC1':'BC3','BC4':'BC5'}[fmt]
    if fmt in('BC3','BC5','BC7') and bpb==8: fmt='BC1' if fmt!='BC5' else 'BC4'
    pf=struct.pack('<II4sIIIII',32,4,b'DX10',0,0,0,0,0)
    hdr=b'DDS '+struct.pack('<IIIIIII',124,0x1|0x2|0x4|0x1000|0x80000,h,w,len(raw),0,1)+b'\0'*44+pf+struct.pack('<IIIII',0x1000,0,0,0,0)
    dx10=struct.pack('<IIIII',DXGI[fmt],3,0,1,0)
    im=Image.open(io.BytesIO(hdr+dx10+raw)); im.load()
    return im
