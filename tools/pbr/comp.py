import sys,numpy as np
from PIL import Image,ImageFilter
def comp(base,emit,out,strength=0.8):
    b=np.asarray(Image.open(base).convert('RGB')).astype(np.float32); e=Image.open(emit).convert('RGB'); r=max(2,b.shape[1]//200)
    E=np.asarray(e).astype(np.float32); bl=np.asarray(e.filter(ImageFilter.GaussianBlur(r))).astype(np.float32); wd=np.asarray(e.filter(ImageFilter.GaussianBlur(r*4))).astype(np.float32)
    Image.fromarray(np.clip(b+strength*(0.9*bl+0.7*wd),0,255).astype(np.uint8)).save(out)
if __name__=='__main__': comp(*sys.argv[1:4])
