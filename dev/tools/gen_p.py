import sys; sys.path.insert(0, sys.argv[1])
from lua import emit
belts=["transport-belt","fast-transport-belt","express-transport-belt","turbo-transport-belt"]
cases=[]
for ins in ["itt-bulk-slow","itt-bulk-long","bulk-inserter"]:
  for q in ["normal","uncommon","rare","epic","legendary"]:
    for b in belts:
      for h in [1,2,3,4,6,8,12]:
        cases.append(dict(id=f"bc|{ins}|{q}|{h}|{b}|1", ins=ins,q=q,ovr=h,force=[2,11,3],src="belt",srcbelt=b,src_stack=1,dst="chest"))
print(emit(cases, warm=600, measure=4800))
