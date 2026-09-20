"""Saved-mask scale experiment; every numerical operation runs remotely."""
import argparse,json,hashlib,traceback,platform,shutil
from pathlib import Path
assert platform.node()=='cenara70hx'
import numpy as np
from PIL import Image
import torch
from cohd_scale_engine import predict,VARIANTS
from cctv_eval_utils import metrics,aggregate
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--out',required=True);p.add_argument('--variants',default=','.join(VARIANTS));p.add_argument('--n',type=int);a=p.parse_args()
out=Path(a.out);assert not out.exists();out.mkdir(parents=True)
for filename in ['run_cohd_scale.py','cohd_scale_engine.py','cohd_verifier_engine.py','cctv_eval_utils.py']:
 shutil.copy2(Path(__file__).parent/filename,out/filename)
items=json.loads(Path(a.manifest).read_text())['items'];items=items[:a.n] if a.n else items;variants=a.variants.split(',');results={k:[] for k in variants};failures={}
(out/'lock.json').write_text(json.dumps(dict(manifest=a.manifest,sha256=hashlib.sha256(Path(a.manifest).read_bytes()).hexdigest(),variants={k:VARIANTS[k] for k in variants},keys=[i['key'] for i in items],code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
for k in variants:
 try:
  predict(items[0]['image'],items[0]['expression'],k)
 except Exception:
  failures[k]=traceback.format_exc();print('FAILED',k,failures[k],flush=True);torch.cuda.empty_cache()
active=[k for k in variants if k not in failures]
for j,i in enumerate(items):
 for k in active[j%len(active):]+active[:j%len(active)]:
  torch.cuda.reset_peak_memory_stats();mask,meta=predict(i['image'],i['expression'],k);dest=out/k;dest.mkdir(exist_ok=True);mp=dest/(i['item_id']+'.png');Image.fromarray(mask.astype('uint8')*255).save(mp)
  results[k].append(dict(key=i['key'],domain=i.get('domain','gref'),source_group=i.get('source_group','gref'),target_count=i['target_count'],metrics=metrics(i,mask),mask=str(mp),mask_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),**meta))
 (out/'progress.json').write_text(json.dumps(dict(done=j+1,total=len(items),variants=active)))
 print(j+1,len(items),{k:round(results[k][-1]['request_s'],3) for k in active},flush=True)
summary={k:dict(metrics=aggregate(v),runtime_mean=float(np.mean([r['request_s'] for r in v])),runtime_p95=float(np.quantile([r['request_s'] for r in v],.95)),peak_bytes=max(r['peak_bytes'] for r in v)) for k,v in results.items() if v}
(out/'per_image.json').write_text(json.dumps(results,indent=2));(out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'failures.json').write_text(json.dumps(failures,indent=2));print(json.dumps(summary,indent=2),flush=True)
