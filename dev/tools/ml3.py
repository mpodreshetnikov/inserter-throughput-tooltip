exec(open("/tmp/claude-0/-home-user/c1c47c97-0f0f-5391-8da1-71e629f8ed70/scratchpad/tools/ml.py").read().split("train=load(")[0])
train=load(sorted(glob.glob(S+"/out_ml*.txt")), {"ml"})
vt=[load([S+f"/out_vt{i}.txt"], {"bc"}) for i in range(1,7)]
def fit(rows, depth, ntree, lr):
    X=np.array([feats(r) for r in rows]); b=np.array([physics(r) for r in rows]); y=np.array([r['cyc'] for r in rows])
    return GradientBoostingRegressor(max_depth=depth,n_estimators=ntree,learning_rate=lr,subsample=0.8,random_state=0).fit(X,np.log(y/b))
def pred(m, rows):
    return np.array([physics(r) for r in rows])*np.exp(m.predict(np.array([feats(r) for r in rows])))
test=vt[4]+vt[5]
tr=train+vt[0]+vt[1]+vt[2]+vt[3]
evaluate("physics -> vt5,6", np.array([physics(r) for r in test]), test)
for depth,ntree,lr in [(4,200,0.08),(4,400,0.05),(5,150,0.1),(5,300,0.05),(6,200,0.05)]:
    m=fit(tr, depth, ntree, lr); evaluate(f"d{depth} t{ntree} lr{lr} -> vt5,6", pred(m,test), test)
