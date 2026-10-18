import sys, random; sys.path.insert(0, sys.argv[1])
from lua import emit
random.seed(int(sys.argv[2]) if len(sys.argv)>2 else 1)
belts=["transport-belt","fast-transport-belt","express-transport-belt","turbo-transport-belt"]
ins_all=["burner-inserter","inserter","long-handed-inserter","fast-inserter","bulk-inserter","stack-inserter"]
qs=["normal","uncommon","rare","epic","legendary"]
dirs=[0,4,8,12]
cases=[]
PRESETS=[[0,0,0],[0,1,0],[1,2,1],[1,3,1],[1,4,2],[1,7,2],[2,7,3],[2,11,3],[2,11,0],[0,5,1],[2,9,2],[1,11,3]]
def force():
    return random.choice(PRESETS)
def hand():
    return random.choice([0,0,0,1,2,3,4,5,7,9,12,16])
n=0
def add(kind, **kw):
    global n; n+=1
    kw["id"]=f"{kind}|{n}|{kw['ins']}|{kw.get('q','normal')}"
    cases.append(kw)
for _ in range(160):
    add("cc", ins=random.choice(ins_all), q=random.choice(qs), ovr=hand(), dir=random.choice(dirs), force=force(), src="chest", dst="chest")
for _ in range(160):
    add("cb", ins=random.choice(ins_all), q=random.choice(qs), ovr=hand(), dir=random.choice(dirs), force=force(), src="chest", dst="belt", dstbelt=random.choice(belts))
for _ in range(160):
    add("bc", ins=random.choice(ins_all), q=random.choice(qs), ovr=hand(), dir=random.choice(dirs), force=force(), src="belt", srcbelt=random.choice(belts), src_stack=random.choice([1,1,2,3,4]), dst="chest")
for _ in range(80):
    b=random.choice(belts)
    add("bb", ins=random.choice(ins_all), q=random.choice(qs), ovr=hand(), dir=random.choice(dirs), force=force(), src="belt", srcbelt=b, src_stack=random.choice([1,4]), dst="belt", dstbelt=random.choice(belts))
for _ in range(20):
    add("lane", ins=random.choice(ins_all[1:]), q=random.choice(qs), ovr=hand(), force=force(), src="belt", srcbelt=random.choice(belts), src_stack=1, dst="chest", lanes="left")
for item in ["locomotive","uranium-fuel-cell"]:
    for ins in ["bulk-inserter","stack-inserter"]:
        add("item", ins=ins, q="normal", ovr=0, force=[2,11,3], src="chest", dst="chest", item=item, filter=item)
        add("item", ins=ins, q="normal", ovr=0, force=[2,11,3], src="chest", dst="belt", dstbelt="turbo-transport-belt", item=item, filter=item)
vecs=[((0,-1),(1.2,0)),((0,-1),(1,1)),((0,-1),(0,3.2)),((0,-3),(0,1.2)),((0,-1),(2.2,0)),((0,-2),(1,-1))]
for p,d in vecs:
    for ins in ["itt-custom","itt-custom-slow"]:
        add("vec", ins=ins, q=random.choice(qs), ovr=1, force=[0,0,0], pick=list(p), drop=list(d), src="chest", dst="chest")
# ghost twins
for _ in range(20):
    c=dict(ins=random.choice(ins_all), q=random.choice(qs), ovr=hand(), dir=random.choice(dirs), force=force())
    route=random.choice([("chest","chest"),("chest","belt"),("belt","chest")])
    c.update(src=route[0], dst=route[1], srcbelt="fast-transport-belt", dstbelt="express-transport-belt", src_stack=1)
    add("twin", **c)
    add("ghost", ghost=True, **c)
print(emit(cases, warm=600, measure=3600))
