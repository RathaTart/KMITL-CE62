"""Remote runtime/equivalence benchmark on development images, no GT scoring."""
import json,platform,time
from pathlib import Path
import numpy as np
from PIL import Image
from fast_lisa_engine import FastLisaEngine
from lisa_engine import LisaEngine,read_image_rgb
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');O=R/'results/runtime_cache_paired_20260915';O.mkdir(exist_ok=True)
pool=json.loads((R/'results/extended_dev_20260915/manifest.json').read_text())['items']
items=[next(i for i in pool if i['case_type']==k) for k in ['single_in_crowd','multi_target','no_target']]
t=time.perf_counter();engine=FastLisaEngine(str(R/'weights/LISA-7B-v1'),str(R/'weights/clip-vit-large-patch14'),sam_encoder_device='cuda');load=time.perf_counter()-t
rows=[]
for j,i in enumerate(items):
    image=read_image_rgb(i['image']);instruction=i['lisa_instruction']
    modes=['baseline','cached']
    for mode in modes:
        start=time.perf_counter();result=(LisaEngine.segment if mode=='baseline' else FastLisaEngine.segment)(engine,image,instruction,max_new_tokens=16);wall=time.perf_counter()-start
        pred=np.zeros(image.shape[:2],bool)
        for mask in result['masks']:pred|=mask
        reference=np.asarray(Image.open(i['lisa_mask']))>0
        row=dict(key=i['key'],mode=mode,wall_seconds=wall,model_seconds=result['latency_s'],changed_pixels=int((pred!=reference).sum()),reference_pixels=int(reference.sum()),answer=result['text'],mask_equal=bool(np.array_equal(pred,reference)),peak_gib=engine.peak_vram_gb())
        Image.fromarray(pred.astype('uint8')*255).save(O/(i['item_id']+'_'+mode+'.png'));rows.append(row)
        (O/'benchmark.json').write_text(json.dumps(dict(load_seconds=load,rows=rows),indent=2));print(json.dumps(row),flush=True)

paired=[]
for i in items:
    a=np.asarray(Image.open(O/(i['item_id']+'_baseline.png')));b=np.asarray(Image.open(O/(i['item_id']+'_cached.png')))
    r=[r for r in rows if r['key']==i['key']];base,fast=r
    paired.append(dict(key=i['key'],case_type=i['case_type'],mask_equal=bool(np.array_equal(a,b)),changed_pixels=int((a!=b).sum()),answer_equal=base['answer']==fast['answer'],baseline_seconds=base['wall_seconds'],fast_seconds=fast['wall_seconds'],speedup=base['wall_seconds']/fast['wall_seconds']))
(O/'paired.json').write_text(json.dumps(dict(pairs=paired,scope='Three paired development cases: single, multiple and absent target; no GT accuracy re-evaluation'),indent=2));print(json.dumps(paired),flush=True)
