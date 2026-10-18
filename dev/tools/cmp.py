import sys,json,collections
rows=[]
for l in open(sys.argv[1]):
    if "RESULT " in l: rows.append(json.loads(l.split("RESULT ",1)[1]))
by=collections.defaultdict(list)
bad=[]
for d in rows:
    kind=d['id'].split("|")[0]
    if kind=="ghost": continue
    m,p=d['rate'],d['pred']
    err=(p-m)/m if m>0 else (0 if p==0 else 9)
    by[kind].append(err)
    tol=0.30 if d['papprox'] else 0.02
    if abs(err)>tol: bad.append((kind,err,d))
for k,errs in by.items():
    ae=[abs(e) for e in errs]
    print(f"{k:5s} n={len(errs):3d} exact={sum(1 for e in ae if e<0.01):3d} mean|err|={sum(ae)/len(ae)*100:5.2f}% max={max(ae)*100:5.1f}% bias={sum(errs)/len(errs)*100:+.2f}%")
print("fields per case:", collections.Counter(d['nfields'] for d in rows))
print("--- outliers")
for k,e,d in sorted(bad,key=lambda x:-abs(x[1]))[:25]:
    print(f"{k} err={e*100:+6.1f}% meas={d['rate']:.3f} pred={d['pred']:.3f} pcyc={d['pcycle']:.1f} items={d['pitems']} lim={d['plim']} {d['pk']}->{d['dk']} tpc={d['tpc']} deltas={d['deltas']} id={d['id']} st={d['status']}")
twins={}
for d in rows:
    k=d['id'].split("|")
    if k[0] in("twin","ghost"): twins.setdefault(int(k[1]) - (1 if k[0]=="ghost" else 0), {})[k[0]]=d
print("--- ghost vs real prediction")
for i,t in sorted(twins.items()):
    if "twin" in t and "ghost" in t:
        a,b=t["twin"],t["ghost"]
        print(f"{a['id']:45s} real={a['pred']:.3f} ghost={b['pred']:.3f} {'OK' if abs(a['pred']-b['pred'])<1e-6 else 'DIFF'} {b['pk']}->{b['dk']}")
