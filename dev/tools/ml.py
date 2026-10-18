import json, math, re, sys, glob
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
S="/tmp/claude-0/-home-user/c1c47c97-0f0f-5391-8da1-71e629f8ed70/scratchpad"
BV={"transport-belt":0.03125,"fast-transport-belt":0.0625,"express-transport-belt":0.09375,"turbo-transport-belt":0.125}
radius={}
for f in glob.glob(S+"/fwrite/mods/itt-harness/protos*.lua"):
    for m in re.finditer(r'name="([^"]+)",rot=([\d.]+),ext=([\d.]+),r=(\d)', open(f).read()):
        radius[m.group(1)]=int(m.group(4))
radius.update({"long-handed-inserter":2,"itt-bulk-long":2})
def load(files, kinds):
    rows=[]
    for f in files:
        for l in open(f):
            if "RESULT " not in l: continue
            d=json.loads(l.split("RESULT ",1)[1])
            c=d.get("case")
            if not c or c.get("src")!="belt" or c.get("dst")!="chest": continue
            if d['id'].split("|")[0] not in kinds: continue
            if d['rate']<=0: continue
            v=BV[c['srcbelt']]; ss=d['pstack']; lanes=1 if c.get('lanes')=="left" else 2
            n=d['pitems']; k=math.ceil(n/ss)
            supply=lanes*v/0.25*ss*60
            if d['rate']>=0.97*supply: continue  # censored by belt supply
            r=radius.get(c['ins'],1)
            H=d['phalf']; rot=d['rot']; ext=d['ext']
            cyc=n*60/d['rate']
            rows.append(dict(group=c['ins']+"|"+c.get('q','normal'), H=H, rot=rot, ext=ext, r=r, v=v, ss=ss, lanes=lanes, n=n, k=k, cyc=cyc, src=f))
    return rows
def feats(r):
    tang=2*math.pi*r['r']*r['rot']
    return [r['H'], math.log(r['rot']), math.log(r['ext']), r['r'], r['v'], r['k'], r['lanes'], r['ss'],
            r['v']/r['ext'], r['v']/tang, 0.25/(r['lanes']*r['v'])/max(1,0.2/r['ext']), (r['k']-1)*max(1,0.2/r['ext']), (r['k']-1)*0.25/(r['lanes']*r['v'])]
def physics(r): return 2*r['H']+(r['k']-1)*max(1,0.2/r['ext'])
def evaluate(name, pred, rows):
    e=np.array([(r['cyc']-p)/p for r,p in zip(rows,pred)])  # rate error = cyc_meas/cyc_pred - 1
    ae=np.abs(e)
    print(f"  {name:28s} n={len(rows):4d} mean|err|={ae.mean()*100:5.2f}%  p90={np.percentile(ae,90)*100:5.1f}%  max={ae.max()*100:5.1f}%  bias={e.mean()*100:+5.2f}%")
train=load(sorted(glob.glob(S+"/out_ml*.txt")), {"ml"})
test=load([S+"/out_vt1.txt",S+"/out_vt2.txt"], {"bc"})
print("train", len(train), "vanilla test", len(test))
X=np.array([feats(r) for r in train]); base=np.array([physics(r) for r in train]); y=np.array([r['cyc'] for r in train])
groups=np.array([r['group'] for r in train])
Xt=np.array([feats(r) for r in test]); baset=np.array([physics(r) for r in test])
print("physics model:")
evaluate("train (random protos)", base, train); evaluate("vanilla test", baset, test)
target=np.log(y/base)
for depth,ntree,lr in [(3,150,0.05),(4,200,0.05),(3,400,0.03)]:
    oof=np.zeros(len(y))
    for tr,va in GroupKFold(5).split(X,target,groups):
        m=GradientBoostingRegressor(max_depth=depth,n_estimators=ntree,learning_rate=lr,subsample=0.8,random_state=0).fit(X[tr],target[tr])
        oof[va]=m.predict(X[va])
    m=GradientBoostingRegressor(max_depth=depth,n_estimators=ntree,learning_rate=lr,subsample=0.8,random_state=0).fit(X,target)
    print(f"GBM depth={depth} trees={ntree} lr={lr}:")
    evaluate("CV unseen protos", base*np.exp(oof), train); evaluate("vanilla test", baset*np.exp(m.predict(Xt)), test)
# simple ridge on residual
oof=np.zeros(len(y))
for tr,va in GroupKFold(5).split(X,target,groups):
    m=Ridge(1.0).fit(X[tr],target[tr]); oof[va]=m.predict(X[va])
m=Ridge(1.0).fit(X,target)
print("Ridge(log ratio):"); evaluate("CV unseen protos", base*np.exp(oof), train); evaluate("vanilla test", baset*np.exp(m.predict(Xt)), test)
