import sys,json,collections,re
rows=[]
for f in sys.argv[1:]:
  for l in open(f):
    if "RESULT " in l: rows.append(json.loads(l.split("RESULT ",1)[1]))
cases={}
for f in ["cases_val.lua"]:
    pass
groups=collections.defaultdict(list)
for d in rows:
    if not d['papprox'] or d['rate']<=0: continue
    e=(d['pred']-d['rate'])/d['rate']
    groups[("lim",d['plim'])].append(e)
    groups[("ins",d['id'].split("|")[2])].append(e)
    groups[("q",d['id'].split("|")[3])].append(e)
    groups[("items",min(d['pitems'],16)//4*4)].append(e)
for k in sorted(groups, key=str):
    v=groups[k]; print(k, len(v), "mean=%+.1f%%"%(sum(v)/len(v)*100), "mean|e|=%.1f%%"%(sum(abs(x) for x in v)/len(v)*100))
