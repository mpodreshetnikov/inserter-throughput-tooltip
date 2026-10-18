import sys
ins = ["burner-inserter","inserter","long-handed-inserter","fast-inserter","bulk-inserter","stack-inserter"]
qs = ["normal","uncommon","rare","epic","legendary"]
cases=[]
for i in ins:
    for q in qs:
        for ovr in [1,2,5,0]:
            cases.append(dict(id=f"cc|{i}|{q}|h{ovr}|N", ins=i, q=q, ovr=ovr, force=[2,11,3], src="chest", dst="chest"))
for i in ["inserter","fast-inserter","long-handed-inserter"]:
    for d,dn in [(0,"N"),(4,"E"),(8,"S"),(12,"W")]:
        cases.append(dict(id=f"cc|{i}|normal|h1|{dn}", ins=i, q="normal", ovr=1, dir=d, force=[0,0,0], src="chest", dst="chest"))
# no-research hand sizes
for i in ins:
    cases.append(dict(id=f"cc|{i}|normal|h0|N|nores", ins=i, q="normal", ovr=0, force=[0,0,0], src="chest", dst="chest"))
def lua(v):
    if isinstance(v,str): return '"%s"'%v
    if isinstance(v,bool): return "true" if v else "false"
    if isinstance(v,(int,float)): return repr(v)
    if isinstance(v,list): return "{"+",".join(lua(x) for x in v)+"}"
    if isinstance(v,dict): return "{"+",".join(f"{k}={lua(x)}" for k,x in v.items())+"}"
print("return {warm=600, measure=3000, cases={")
for c in cases: print("  "+lua(c)+",")
print("}}")
