import sys,json,math,collections
rows=collections.OrderedDict()
for l in open(sys.argv[1]):
    if "RESULT " not in l: continue
    d=json.loads(l.split("RESULT ",1)[1])
    _,ins,q,h,b,ss=d['id'].split("|")
    key=(ins,q,b); rows.setdefault(key,{})[int(h)]=d
bv={"transport-belt":0.03125,"fast-transport-belt":0.0625,"express-transport-belt":0.09375,"turbo-transport-belt":0.125}
for (ins,q,b),m in rows.items():
    d1=next(iter(m.values())); rot=d1['rot']
    H=math.ceil(0.5/rot-1e-6)-1
    beltrate=2*bv[b]/0.25*60
    cells=[]
    for h in sorted(m):
        r=m[h]['rate']; cyc=60*h/r if r>0 else 0
        flag="*" if r>beltrate*0.97 else " "
        cells.append(f"{h}:{cyc:5.1f}{flag}")
    print(f"{ins:14s} {q:9s} {b[:6]:6s} 2H={2*H:3d} | "+" ".join(cells))
