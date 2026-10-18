import sys, random, math; sys.path.insert(0, sys.argv[1])
from lua import emit, lua
random.seed(int(sys.argv[2]))
nproto=int(sys.argv[3])
protos=[]
for i in range(nproto):
    rot=math.exp(random.uniform(math.log(0.010), math.log(0.12)))
    ratio=random.choice([2.5,2.5,random.uniform(1.2,4.0)])
    ext=rot*ratio
    r=random.choice([1,1,1,2,2,3])
    protos.append(dict(name=f"itt-r{sys.argv[2]}-{i}", rot=round(rot,5), ext=round(ext,5), r=r))
open(sys.argv[4],"w").write("return "+lua(protos)+"\n")
belts=["transport-belt","fast-transport-belt","express-transport-belt","turbo-transport-belt"]
cases=[]
for p in protos:
    for b in belts:
        for h in random.sample([1,2,3,4,5,6,8,10,12,16],5):
            ss=random.choice([1,1,2,3,4])
            lanes=random.choice(["both","both","both","left"])
            c=dict(id=f"ml|{p['name']}|{h}|{b}|{ss}|{lanes}", ins=p['name'], q="normal", ovr=h, force=[2,11,3], src="belt", srcbelt=b, src_stack=ss, dst="chest")
            if lanes=="left": c["lanes"]="left"
            cases.append(c)
print(emit(cases, warm=600, measure=3600))
