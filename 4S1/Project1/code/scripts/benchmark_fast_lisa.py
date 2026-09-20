"""Remote runtime/equivalence benchmark on development images, no GT scoring."""
import json,platform,time
from pathlib import Path
import numpy as np
from PIL import Image
from fast_lisa_engine import FastLisaEngine
from lisa_engine import LisaEngine,read_image_rgb
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');O=R/'results/runtime_cache_retry_20260915';O.mkdir(exist_ok=True)
items=json.loads((R/'results/extended_dev_20260915/manifest.json').read_text())['items'][:6]
t=time.perf_counter();engine=FastLisaEngine(str(R/'weights/LISA-7B-v1'),str(R/'weights/clip-vit-large-patch14'),sam_encoder_device='cuda');load=time.perf_counter()-t
rows=[]
for j,i in enumerate(items):
    image=read_image_rgb(i['image']);instruction=i['lisa_instruction']
    modes=['baseline','cached'] if j==0 else ['cached']
    for mode in modes:
        start=time.perf_counter();result=(LisaEngine.segment if mode=='baseline' else FastLisaEngine.segment)(engine,image,instruction,max_new_tokens=16);wall=time.perf_counter()-start
        pred=np.zeros(image.shape[:2],bool)
        for mask in result['masks']:pred|=mask
        reference=np.asarray(Image.open(i['lisa_mask']))>0
        row=dict(key=i['key'],mode=mode,wall_seconds=wall,model_seconds=result['latency_s'],changed_pixels=int((pred!=reference).sum()),reference_pixels=int(reference.sum()),answer=result['text'],mask_equal=bool(np.array_equal(pred,reference)),peak_gib=engine.peak_vram_gb())
        Image.fromarray(pred.astype('uint8')*255).save(O/(i['item_id']+'_'+mode+'.png'));rows.append(row)
        (O/'benchmark.json').write_text(json.dumps(dict(load_seconds=load,rows=rows),indent=2));print(json.dumps(row),flush=True)
