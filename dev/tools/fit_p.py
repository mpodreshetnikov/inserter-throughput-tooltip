import sys,json,math,collections
bv={"transport-belt":0.03125,"fast-transport-belt":0.0625,"express-transport-belt":0.09375,"turbo-transport-belt":0.125}
data=[]
for f in sys.argv[1:]:
  for l in open(f):
    if "RESULT " not in l: continue
    d=json.loads(l.split("RESULT ",1)[1])
    p=d['id'].split("|")
    if p[0]!="bc": continue
    ins,q,h,b,ss=p[1],p[2],int(p[3].lstrip("h")),p[4],int(p[5].lstrip("s"))
    data.append((ins,q,h,b,ss,d))
def model(d,h,b,ss,D=0.25,mode=0):
    rot,ext=d['rot'],d['ext']
    H=math.ceil(0.5/rot-1e-6)-1
    v=bv[b]
    k=math.ceil(h/ss)
    t=max(1.0, D/ext)
    cyc=2*H+(k-1)*t
    rate=h*60/cyc
    beltrate=2*v/0.25*ss*60
    return min(rate,beltrate)
for D in [0.2,0.22,0.25,0.28]:
    errs=[]
    for ins,q,h,b,ss,d in data:
        m=model(d,h,b,ss,D)
        errs.append((m-d['rate'])/d['rate'])
    ae=[abs(e) for e in errs]
    print(f"D={D}: n={len(errs)} mean|err|={sum(ae)/len(ae)*100:.1f}% max={max(ae)*100:.1f}% bias={sum(errs)/len(errs)*100:+.1f}% p90={sorted(ae)[int(len(ae)*0.9)]*100:.1f}%")
print("--- grid")
best=[]
import itertools
for D0,D1,b0,fl in itertools.product([0.2,0.22,0.24,0.26,0.28,0.3],[0,0.4,0.8,1.2],[-2,-1,0],[0.8,1.0]):
    errs=[]
    for ins,q,h,b,ss,d in data:
        rot,ext=d['rot'],d['ext']; H=math.ceil(0.5/rot-1e-6)-1; v=bv[b]; k=math.ceil(h/ss)
        t=max(fl,(D0-D1*v)/ext)
        cyc=max(1,2*H+b0+(k-1)*t)
        m=min(h*60/cyc, 2*v/0.25*ss*60)
        errs.append((m-d['rate'])/d['rate'])
    ae=[abs(e) for e in errs]
    best.append((sum(ae)/len(ae), max(ae), sum(errs)/len(errs), sorted(ae)[int(len(ae)*0.9)], D0,D1,b0,fl))
best.sort()
for r in best[:8]: print("mean=%.2f%% max=%.1f%% bias=%+.1f%% p90=%.1f%%  D0=%s D1=%s b0=%s fl=%s"%(r[0]*100,r[1]*100,r[2]*100,r[3]*100,*r[4:]))
