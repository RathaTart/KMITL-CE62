"""Sequential cold-process end-to-end comparison on a development image."""
import hashlib,json,platform,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');O=R/'results/runtime_full_20260915';O.mkdir(exist_ok=True)
i=json.loads((R/'results/extended_dev_20260915/manifest.json').read_text())['items'][0]
results={}
for mode,script in [('baseline','infer_extended.py'),('accelerated','infer_extended_fast.py')]:
    dest=O/mode
    if not (dest/'result.json').exists():
        with (O/(mode+'.log')).open('w') as log:
            subprocess.run(['/home/osta/blip2-qformer-eval/.venv/bin/python',str(R/'scripts'/script),'--image',i['image'],'--text',i['expression'],'--out',str(dest)],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
    results[mode]=json.loads((dest/'result.json').read_text());print(mode,results[mode]['end_to_end_seconds'],flush=True)
a=np.asarray(Image.open(results['baseline']['mask']));b=np.asarray(Image.open(results['accelerated']['mask']))
summary=dict(results=results,mask_equal=bool(np.array_equal(a,b)),changed_pixels=int((a!=b).sum()),speedup=results['baseline']['end_to_end_seconds']/results['accelerated']['end_to_end_seconds'],same_development_image=True,no_ground_truth_used=True,scope='One paired cold-process run, not a throughput benchmark or full accuracy re-evaluation',source_hashes={name:hashlib.sha256((R/'scripts'/name).read_bytes()).hexdigest() for name in ['fast_lisa_engine.py','run_fast_lisa.py','infer_extended_fast.py']})
(O/'comparison.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
