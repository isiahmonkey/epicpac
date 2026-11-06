import numpy as np,collections,sys
B='/mnt/user-data/outputs/token_build/modelsrc/'; tag=sys.argv[1]
nodes={}
L=open(B+'token_base_bind.smd').read().split('\n'); k=L.index('nodes')+1
while L[k]!='end':
    t=L[k].split('"'); nodes[int(t[0])]=t[1].replace('ValveBiped.Bip01_',''); k+=1
tot=0
for part in ['arms_gorilla_black','arms_cyber_gorilla_black','arms_plates_l_gorilla_black','arms_plates_r_gorilla_black']:
    A=open(B+'token_base_%s.smd'%part).read().split('triangles\n')[1].split('\n'); Bb=open(B+'zz_%s_token_base_%s.smd'%(tag,part)).read().split('triangles\n')[1].split('\n')
    bad=collections.Counter()
    for i in range(0,len(A)-3,4):
        if A[i].strip()=='end': break
        pa=np.array([list(map(float,A[i+k].split()[1:4])) for k in (1,2,3)]); pb=np.array([list(map(float,Bb[i+k].split()[1:4])) for k in (1,2,3)])
        ea=np.linalg.norm(pa-np.roll(pa,1,0),axis=1); eb=np.linalg.norm(pb-np.roll(pb,1,0),axis=1); r=(eb/np.maximum(ea,1e-6)).max()
        if r>1.5 or r<0.5:
            t=A[i+1].split(); bad[tuple(sorted(nodes[int(t[10+2*q])] for q in range(int(t[9]))))]+=1
    tot+=sum(bad.values()); print(part,sum(bad.values()),bad.most_common(4))
print(tag,'TOTAL stretched tris',tot)
