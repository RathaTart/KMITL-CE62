"""Actual full-image paired resident runtime, remote GPU, no cached inference."""
import json,time,hashlib
import numpy as np
from PIL import Image
import torch
from cctv_engine import CCTVEngine,O
engine=CCTVEngine();items=json.loads((O/'validation_manifest.json').read_text())['items'];cctv=[i for i in items if i.get('domain')=='PersonPath22'];gref=[i for i in items if not i.get('domain')];chosen=[cctv[j] for j in np.linspace(0,len(cctv)-1,12).astype(int)]+[gref[j] for j in np.linspace(0,len(gref)-1,12).astype(int)];modes=['original','customA','customB'];rows=[]
for mode in modes:engine.predict(chosen[0]['image'],chosen[0]['expression'],mode)
for j,i in enumerate(chosen):
 row=dict(key=i['key'],times={})
 for mode in modes[j%3:]+modes[:j%3]:
  torch.cuda.reset_peak_memory_stats();mask,meta,_,_=engine.predict(i['image'],i['expression'],mode);row['times'][mode]=meta['request_s'];row.setdefault('gpu_peak_bytes',{})[mode]=torch.cuda.max_memory_allocated();D=O/'runtime'/mode;D.mkdir(parents=True,exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(D/(i['item_id']+'__expression.png'))
 rows.append(row);print(j+1,len(chosen),row['times'],flush=True)
summary={}
for mode in modes:
 x=np.array([r['times'][mode] for r in rows]);summary[mode]=dict(mean=float(x.mean()),median=float(np.median(x)),p95=float(np.quantile(x,.95)),gpu_peak_bytes=max(r['gpu_peak_bytes'][mode] for r in rows))
rng=np.random.default_rng(20260915);idx=rng.integers(0,len(rows),(10000,len(rows)));base=np.array([r['times']['original'] for r in rows])
for mode in modes[1:]:
 x=np.array([r['times'][mode] for r in rows]);summary[mode]['relative_overhead']=float(x.mean()/base.mean()-1);summary[mode]['relative_overhead_ci95']=np.quantile(x[idx].mean(1)/base[idx].mean(1)-1,[.025,.975]).tolist()
result=dict(n=len(rows),summary=summary,definition='Full image load, preprocessing, inference, optional verifier and mask conversion; no feature cache; excludes initial model load, switching experiment weights and disk export',rows=rows);(O/'runtime.json').write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
