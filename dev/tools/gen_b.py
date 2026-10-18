import sys; sys.path.insert(0, sys.argv[1])
from lua import emit
belts=["transport-belt","fast-transport-belt","express-transport-belt","turbo-transport-belt"]
hands={"inserter":[1,3],"long-handed-inserter":[1,3],"fast-inserter":[1,2,3],"bulk-inserter":[1,4,12],"stack-inserter":[1,4,8,16]}
cases=[]
mode=sys.argv[2]
for ins,hs in hands.items():
  for b in belts:
    for h in hs:
      for q in ["normal","legendary"]:
        if mode=="cb":
          cases.append(dict(id=f"cb|{ins}|{q}|h{h}|{b}|bs4", ins=ins,q=q,ovr=h,force=[2,11,3],src="chest",dst="belt",dstbelt=b))
        elif mode=="bc":
          for ss in ([1,4] if True else [1]):
            cases.append(dict(id=f"bc|{ins}|{q}|h{h}|{b}|ss{ss}", ins=ins,q=q,ovr=h,force=[2,11,3],src="belt",srcbelt=b,src_stack=ss,dst="chest"))
        elif mode=="bb":
          cases.append(dict(id=f"bb|{ins}|{q}|h{h}|{b}", ins=ins,q=q,ovr=h,force=[2,11,3],src="belt",srcbelt=b,src_stack=1,dst="belt",dstbelt=b))
if mode=="cb":
  for b in belts:
    for bs in [0,1,2]:
      for h in [4,16]:
        cases.append(dict(id=f"cb|stack-inserter|normal|h{h}|{b}|bs{min(4,bs+1)}", ins="stack-inserter",q="normal",ovr=h,force=[2,11,bs],src="chest",dst="belt",dstbelt=b))
print(emit(cases))
