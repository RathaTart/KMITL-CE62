"""Drop-in fast LISA stage for the opt-in runtime CLI; no GT is read."""
import argparse,json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from fast_lisa_engine import FastLisaEngine
from lisa_engine import read_image_rgb
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--max-new-tokens',type=int,default=16);p.add_argument('--phase');p.add_argument('--sam-encoder-device',default='cuda');p.add_argument('--save-vis');a=p.parse_args()
R=Path('/home/osta/lisa-eval/code');engine=FastLisaEngine(str(R/'weights/LISA-7B-v1'),str(R/'weights/clip-vit-large-patch14'),sam_encoder_device=a.sam_encoder_device)
folder=a.out_dir/'p1_masks';folder.mkdir(exist_ok=True);rows=a.out_dir/'p1_rows.jsonl';assert not rows.exists()
for i in json.loads((a.out_dir/'manifest.json').read_text())['items']:
    image=read_image_rgb(i['image']);result=engine.segment(image,i['lisa_instruction'],max_new_tokens=a.max_new_tokens);mask=np.zeros(image.shape[:2],bool)
    for m in result['masks']:mask|=m
    dest=folder/(i['item_id']+'__'+i['prompt_id']+'.png');Image.fromarray(mask.astype('uint8')*255).save(dest)
    row=dict(key=i['key'],item_id=i['item_id'],prompt_id=i['prompt_id'],instruction=i['lisa_instruction'],answer=result['text'],emitted_seg=result['emitted_seg'],n_seg=len(result['masks']),latency_s=result['latency_s'],mask=str(dest),runtime='KV-cache generation plus full-prefix replay')
    with rows.open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True)
