import sys; sys.path.insert(0, sys.argv[1])
from lua import emit
vecs=[((0,-1),(0,1.2)),((0,-1),(1.2,0)),((0,-1),(1,1)),((0,-1),(0,3.2)),((0,-3),(0,1.2)),((0,-1),(0,5.2)),((0,-1),(0,1.5)),((-1,-1),(1,1)),((0,-1),(2.2,0)),((0,-1),(-1.2,0)),((0,-1),(-1,1)),((0,-2),(0,2.2)),((0,-1),(1,-1)),((0,-1.4),(0,1.2)),((0,-1),(3,3))]
cases=[]
for ins in ["itt-custom","itt-custom-slow"]:
  for q in ["normal","legendary"]:
    for p,d in vecs:
        cases.append(dict(id=f"v|{ins}|{q}|{p}|{d}", ins=ins, q=q, ovr=1, pick=list(p), drop=list(d), force=[0,0,0], src="chest", dst="chest"))
for q in ["normal","legendary"]:
    cases.append(dict(id=f"cc|burner-inserter|{q}|h1", ins="burner-inserter", q=q, ovr=1, force=[0,0,0], src="chest", dst="chest"))
print(emit(cases))
