import sys,json,re
def load_locale(p):
    d={}; sec=None
    for line in open(p, encoding="utf-8"):
        line=line.rstrip("\n")
        m=re.match(r"\[(.+)\]$",line)
        if m: sec=m.group(1); continue
        if "=" in line and sec: k,v=line.split("=",1); d[sec+"."+k]=v
    return d
def loc(ls, L):
    if isinstance(ls,str): return ls
    if isinstance(ls,(int,float)): return ("%g"%ls)
    key=ls[0]; params=[loc(x,L) for x in ls[1:]]
    if key=="": return "".join(params)
    t=L.get(key, "UNKNOWN KEY:"+key)
    for i,p in enumerate(params): t=t.replace(f"__{i+1}__",p)
    return t
L={lang:load_locale(f"/home/user/inserter-throughput-tooltip/locale/{lang}/locale.cfg") for lang in ["en","ru"]}
shown=0
want=set(sys.argv[2].split(",")) if len(sys.argv)>2 else None
for line in open(sys.argv[1]):
    if not line.startswith("FIELDS "): continue
    _,cid,js=line.split(" ",2)
    kind=cid.split("|")[0]
    if want and kind not in want: continue
    want and want.discard(kind)
    fields=json.loads(js)
    print("==",cid)
    for lang in ["en","ru"]:
        for f in fields: print(f"  [{lang}] {loc(f['name'],L[lang])}: {loc(f['value'],L[lang])}")
