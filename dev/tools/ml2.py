exec(open("/tmp/claude-0/-home-user/c1c47c97-0f0f-5391-8da1-71e629f8ed70/scratchpad/tools/ml.py").read().split("train=load(")[0])
train=load(sorted(glob.glob(S+"/out_ml*.txt")), {"ml"})
v1=load([S+"/out_vt1.txt"], {"bc"}); v2=load([S+"/out_vt2.txt"], {"bc"})
def fit(rows, depth, ntree, lr):
    X=np.array([feats(r) for r in rows]); b=np.array([physics(r) for r in rows]); y=np.array([r['cyc'] for r in rows])
    return GradientBoostingRegressor(max_depth=depth,n_estimators=ntree,learning_rate=lr,subsample=0.8,random_state=0).fit(X,np.log(y/b))
def pred(m, rows):
    return np.array([physics(r) for r in rows])*np.exp(m.predict(np.array([feats(r) for r in rows])))
for depth,ntree in [(4,200),(5,300),(4,400)]:
    print(f"depth={depth} trees={ntree}")
    m=fit(train, depth, ntree, 0.05); evaluate("random only -> vt2", pred(m,v2), v2)
    m=fit(train+v1, depth, ntree, 0.05); evaluate("random+vt1 -> vt2", pred(m,v2), v2)
    m=fit(train+v2, depth, ntree, 0.05); evaluate("random+vt2 -> vt1", pred(m,v1), v1)
