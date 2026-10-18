import sys, random; sys.path.insert(0, sys.argv[1])
from lua import emit
random.seed(int(sys.argv[2]))
belts=["transport-belt","fast-transport-belt","express-transport-belt","turbo-transport-belt"]
cases=[]
for ins in ["burner-inserter","inserter","long-handed-inserter","fast-inserter","bulk-inserter","stack-inserter"]:
  for q in ["normal","uncommon","rare","epic","legendary"]:
    for b in belts:
      for h in random.sample([1,2,3,4,5,6,8,10,12,16],3):
        ss=random.choice([1,1,2,3,4]); lanes=random.choice(["both","both","both","left"])
        c=dict(id=f"bc|{ins}|{q}|{h}|{b}|{ss}|{lanes}", ins=ins, q=q, ovr=h, dir=random.choice([0,4,8,12]), force=[2,11,3], src="belt", srcbelt=b, src_stack=ss, dst="chest")
        if lanes=="left": c["lanes"]="left"
        cases.append(c)
print(emit(cases, warm=600, measure=3600))
