"""Remote-only LISA coarse-mask -> SAM boundary refinement development study.

Inspired by mask-prompt refinement literature, not an implementation of SAMRefiner.
GT is accessed only by score. Connected components supply boxes and interior points.
"""
import argparse, hashlib, json, platform, time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def read(p): return json.loads(Path(p).read_text())
def write(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2))
def name(i): return f'{i["item_id"]}__{i["prompt_id"]}.png'

def infer(a):
    import torch
    from transformers import SamModel, SamProcessor
    m=read(a.source/'manifest.json')
    proc=SamProcessor.from_pretrained('facebook/sam-vit-huge',local_files_only=True)
    model=SamModel.from_pretrained('facebook/sam-vit-huge',torch_dtype=torch.float16,local_files_only=True).cuda().eval()
    write(a.out/'manifest.json',m)
    write(a.out/'protocol.json',dict(status=m.get('status','reused development pilot'),dense_prompt=a.dense,component_min_pixels=64,component_min_fraction=.002,box_padding=.05,selection='SAM predicted IoU; guard requires overlap with coarse mask >=0.5',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    for variant in ['refined','guarded']:(a.out/variant).mkdir(parents=True,exist_ok=True)
    rows=[]
    for i in m['items']:
        coarse=np.asarray(Image.open(a.source/'p1_masks'/name(i)))>0
        h,w=coarse.shape; merged=np.zeros_like(coarse); boxes=[]; points=[]
        n,lab,stats,_=cv2.connectedComponentsWithStats(coarse.astype('uint8'),8)
        for c in range(1,n):
            x,y,bw,bh,area=stats[c]
            if area<max(64,coarse.sum()*.002):continue
            region=(lab==c).astype('uint8')
            dist=cv2.distanceTransform(region,cv2.DIST_L2,5)
            py,px=np.unravel_index(dist.argmax(),dist.shape)
            boxes.append([max(0,float(x-bw*.05)),max(0,float(y-bh*.05)),min(w-1,float(x+bw+bw*.05)),min(h-1,float(y+bh+bh*.05))]);points.append([[int(px),int(py)]])
        started=time.perf_counter(); scores=[]
        if boxes:
            inp=proc(images=Image.open(i['image']).convert('RGB'),input_boxes=[boxes],input_points=[points],input_labels=[[[1]]*len(points)],return_tensors='pt')
            inp={k:v.cuda().half() if v.is_floating_point() else v.cuda() for k,v in inp.items()}
            if a.dense:
                rh,rw=inp['reshaped_input_sizes'][0].tolist()
                pad=np.zeros((1024,1024),dtype='float32')
                pad[:rh,:rw]=cv2.resize(coarse.astype('float32'),(rw,rh),interpolation=cv2.INTER_LINEAR)
                dense=cv2.resize(pad,(256,256),interpolation=cv2.INTER_LINEAR)*8-4
                inp['input_masks']=torch.from_numpy(dense)[None,None].cuda().half()
            with torch.inference_mode():o=model(**inp,multimask_output=True)
            masks=proc.image_processor.post_process_masks(o.pred_masks.cpu(),inp['original_sizes'].cpu(),inp['reshaped_input_sizes'].cpu())[0].numpy()
            quality=o.iou_scores[0].float().cpu().numpy()
            for j in range(len(boxes)):
                choice=int(quality[j].argmax());merged|=masks[j,choice]>0;scores.append(float(quality[j,choice]))
        overlap=float((merged&coarse).sum()/max(1,(merged|coarse).sum()))
        guarded=merged if overlap>=.5 else coarse
        for variant,mask in [('refined',merged),('guarded',guarded)]:Image.fromarray(mask.astype('uint8')*255).save(a.out/variant/name(i))
        rows.append(dict(key=i['key'],boxes=boxes,points=points,sam_quality=scores,coarse_agreement_iou=overlap,refinement_wall_s=time.perf_counter()-started))
        write(a.out/'inference.json',rows);print(i['key'],round(overlap,3),flush=True)

def score(a):
    m=read(a.out/'manifest.json');result={};allrows=[]
    for variant,folder in [('LISA',a.source/'p1_masks'),('refined',a.out/'refined'),('guarded',a.out/'guarded')]:
        rows=[]
        for i in m['items']:
            p=np.asarray(Image.open(folder/name(i)))>0;g=np.asarray(Image.open(i['ground_truth']))>0
            inter=int((p&g).sum());union=int((p|g).sum())
            rows.append(dict(key=i['key'],variant=variant,positive=bool(g.any()),iou=inter/union if union else 1.,intersection=inter,union=union))
        result[variant]={}
        for group,rr in [('all',rows),('positive',[r for r in rows if r['positive']]),('no_target',[r for r in rows if not r['positive']])]:
            result[variant][group]=dict(n=len(rr),miou=float(np.mean([r['iou'] for r in rr])),ciou=sum(r['intersection'] for r in rr)/max(1,sum(r['union'] for r in rr)))
        allrows+=rows
    write(a.out/'comparison.json',result);write(a.out/'per_expression.json',allrows);print(json.dumps(result,indent=2))

if __name__=='__main__':
    if platform.node()!='cenara70hx':raise SystemExit('Run experiments on cenara70hx only')
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['infer','score']);p.add_argument('--source',type=Path,default=Path('results/grefcoco_pilot_p1_p2'));p.add_argument('--out',type=Path,default=Path('results/lisa_refinement_20260914'));p.add_argument('--dense',action='store_true');a=p.parse_args()
    (infer if a.stage=='infer' else score)(a)
