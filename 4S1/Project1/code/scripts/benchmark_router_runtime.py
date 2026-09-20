"""Exercise an early exit and a fallback selected from development, with paired baseline."""
import json,platform,subprocess
from pathlib import Path
from router_model import load,decide
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915';O=R/'results/router_runtime_20260915';O.mkdir(exist_ok=True);loaded=load();rows=json.loads((D/'features_labels.json').read_text())['rows'];items={i['key']:i for i in json.loads((D/'manifest.json').read_text())['items']};chosen={}
for row in rows:
    a=decide(row['features'],loaded)['Learned_primary'];branch='early_exit' if a==5 else 'lisa_fallback' if a==0 else 'other'
    if branch in ['early_exit','lisa_fallback'] and branch not in chosen:chosen[branch]=items[row['key']]
records=[]
for branch,i in chosen.items():
    for method in ['LISA_cached','Learned_primary']:
        dest=O/(branch+'_'+method)
        if not (dest/'result.json').exists():
            with (O/(branch+'_'+method+'.log')).open('w') as f:subprocess.run(['/home/osta/blip2-qformer-eval/.venv/bin/python','scripts/infer_router.py','--image',i['image'],'--text',i['expression'],'--out',str(dest),'--method',method],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
        r=json.loads((dest/'result.json').read_text());records.append(dict(branch=branch,key=i['key'],**r));print(branch,method,r['end_to_end_seconds'],flush=True)
(O/'comparison.json').write_text(json.dumps(dict(scope='Two purposively selected development cases exercising branches; not an unbiased mean latency benchmark',records=records),indent=2))
