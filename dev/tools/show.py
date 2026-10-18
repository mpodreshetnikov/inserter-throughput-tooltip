import sys,json
for l in open(sys.argv[1]):
    if "RESULT " not in l: continue
    d=json.loads(l.split("RESULT ",1)[1]); print(f"{d['id']:58s} rate={d['rate']:7.3f} tpc={d['tpc']:3d} cyc={d['cycles']:4d} deltas={d['deltas']} st={d['status']}")
