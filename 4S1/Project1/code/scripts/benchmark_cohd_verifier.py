"""Paired resident request latency on development images; never tunes test."""
import json,random,hashlib
from pathlib import Path
from cohd_verifier_engine import CoHDVerifier,C
import numpy as np
O=C/'results/cohd_upgrade_20260915';engine=CoHDVerifier(O/'method_lock.json');items=json.loads((C/'results/router_confirm_20260915/manifest.json').read_text())['items'][:30]
# Warm both paths. Alternate order to reduce drift.
for mode in [False,True]:engine.predict(items[0]['image'],items[0]['expression'],mode)
rows=[]
for j,i in enumerate(items):
 row=dict(key=i['key'])
 for mode in ([False,True] if j%2==0 else [True,False]):
  mask,meta=engine.predict(i['image'],i['expression'],mode);name='modified' if mode else 'baseline';row[name]=meta
  folder=O/'runtime'/name;folder.mkdir(parents=True,exist_ok=True)
  from PIL import Image
  Image.fromarray(mask.astype('uint8')*255).save(folder/(i['item_id']+'__expression.png'))
 rows.append(row);print(j+1, row['baseline']['request_s'],row['modified']['request_s'],flush=True)
b=np.array([r['baseline']['request_s'] for r in rows]);m=np.array([r['modified']['request_s'] for r in rows]);rng=np.random.default_rng(20260915);idx=rng.integers(0,len(b),(10000,len(b)));delta=(m[idx].mean(1)/b[idx].mean(1)-1)
result=dict(n=len(rows),baseline_mean=float(b.mean()),modified_mean=float(m.mean()),baseline_median=float(np.median(b)),modified_median=float(np.median(m)),relative_overhead=float(m.mean()/b.mean()-1),relative_overhead_ci95=np.quantile(delta,[.025,.975]).tolist(),definition='Resident serialized request includes image IO, preprocessing, inference, verifier, original-size mask; excludes load and mask disk writing',rows=rows)
(O/'runtime.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
