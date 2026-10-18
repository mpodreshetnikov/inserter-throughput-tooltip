def lua(v):
    if isinstance(v,str): return '"%s"'%v
    if isinstance(v,bool): return "true" if v else "false"
    if isinstance(v,(int,float)): return repr(v)
    if isinstance(v,(list,tuple)): return "{"+",".join(lua(x) for x in v)+"}"
    if isinstance(v,dict): return "{"+",".join(f"{k}={lua(x)}" for k,x in v.items())+"}"
def emit(cases, warm=600, measure=3000):
    out=[f"return {{warm={warm}, measure={measure}, cases={{"]
    for c in cases: out.append("  "+lua(c)+",")
    out.append("}}")
    return "\n".join(out)
