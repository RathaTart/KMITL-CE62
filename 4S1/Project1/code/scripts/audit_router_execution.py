import hashlib,json,platform
from pathlib import Path
from router_model import load
assert platform.node()=='cenara70hx'
r=Path('/home/osta/lisa-eval/code');lock,c,a,models=load()
importance=sorted(zip(lock['feature_names'],models['learned'].feature_importances_),key=lambda x:-x[1])
result={'primary_impurity_importance':[{ 'feature':n,'value':float(v)} for n,v in importance],'interpretation':'Descriptive fitted-tree importance; correlated features and selection bias prevent causal claims. Use locked no-Zoom ablation for added-value evidence.','files':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'scripts'/name for name in ['router_model.py','router_features.py','apply_router.py','score_router.py','infer_router.py','benchmark_router_runtime.py']]}}
(r/'results/router_dev_20260915/execution_provenance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result['primary_impurity_importance'][:6],indent=2))
