"""Training-free LISA/SAM proposal agreement and enclosed-hole filling."""
import argparse,json,platform,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
def name(i):return f'{i["item_id"]}__{i["prompt_id"]}'
def mask(p):return np.asarray(Image.open(p))>0
def fill(m):
    n,lab,stats,_=cv2.connectedComponentsWithStats((~m).astype('uint8'),8);border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));out=m.copy()
    for j in range(1,n):
        if j not in border:out[lab==j]=True
    return out
def refine(l,ms,threshold):
    filled=fill(l)
    if not l.any() or threshold>1:return filled,[],0.
    keep=[j for j,m in enumerate(ms) if (m&l).sum()/max(1,m.sum())>=.6]
    union=ms[keep].any(0) if keep else np.zeros_like(l)
    agreement=(union&l).sum()/max(1,(union|l).sum())
    return (fill(union) if agreement>=threshold else filled),keep,float(agreement)
def run(a,threshold,folder):
    folder.mkdir(parents=True,exist_ok=True);rows=[]
    for i in read(a.source/'manifest.json')['items']:
        n=name(i);l=mask(a.source/'p1_masks'/f'{n}.png');ms=np.load(a.proposals/'proposals'/f'{n}.npz')['masks'];p,keep,agreement=refine(l,ms,threshold);Image.fromarray(p.astype('uint8')*255).save(folder/f'{n}.png');rows.append(dict(key=i['key'],candidate_indices=keep,agreement=agreement,proposal_used=agreement>=threshold,threshold=threshold))
    write(folder.parent/'selection.json',rows)
def choose(a):
    records=[]
    for threshold in [1.01,.95,.85,.75]:
        folder=a.out/f'threshold_{threshold}'/'masks';run(a,threshold,folder);positive=[]
        for i in read(a.source/'manifest.json')['items']:
            g=mask(Path(i['ground_truth']))
            if not g.any():continue
            p=mask(folder/f'{name(i)}.png');positive.append(float((p&g).sum()/max(1,(p|g).sum())))
        records.append(dict(threshold=threshold,positive_mean_iou=float(np.mean(positive))))
    chosen=max(records,key=lambda r:r['positive_mean_iou'])
    write(a.out/'method_lock.json',dict(chosen=chosen,trials=records,training=False,weights_modified=False,proposal_precision_min=.6,rule='select SAM proposals with >=60% foreground overlap in LISA; use union only when union/LISA IoU >= chosen threshold; otherwise retain LISA; fill enclosed holes',selection='30 historical development images only',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()));print(json.dumps(chosen))
if __name__=='__main__':
    if platform.node()!='cenara70hx':raise SystemExit('Remote only')
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['choose','render']);p.add_argument('--source',type=Path,default=Path('results/grefcoco_pilot_p1_p2'));p.add_argument('--proposals',type=Path,default=Path('results/global_local_dev_20260914'));p.add_argument('--out',type=Path,default=Path('results/agreement_dev_20260914'));p.add_argument('--lock',type=Path);a=p.parse_args()
    if a.stage=='choose':choose(a)
    else:
        run(a,read(a.lock)['chosen']['threshold'],a.out/'masks');write(a.out/'applied_lock.json',read(a.lock))
