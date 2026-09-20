"""Development-only selector ablations and combined gate/refinement candidates."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from global_local_selector import selected
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');out=root/'results/extended_dev_20260915';items=json.loads((out/'manifest.json').read_text())['items']
clips={}
for src in ['global_local_dev_20260914','global_local_fresh_20260914']:
    clips.update({r['key']:r for r in json.loads((root/'results'/src/'clip_scores.json').read_text())})
trials={}
def add(label,p,g,i,cfg):
    inter=int((p&g).sum());union=int((p|g).sum());trials.setdefault(label,dict(config=cfg,rows=[]))['rows'].append(dict(key=i['key'],positive=bool(g.any()),iou=inter/union if union else 1.,intersection=inter,union=union,pred_pixels=int(p.sum()),gt_pixels=int(g.sum())))
for i in items:
    data=np.load(i['proposals']);ms=data['masks'];g=np.asarray(Image.open(i['ground_truth']))>0;r=clips[i['key']]
    for mode in ['local','hybrid','spatial']:
        for contrast in [0.,.5,1.]:
            modified=dict(r)
            for field in ['local','global_context']:
                a=np.array(r[field]);a=a.reshape(0,len(r['clauses'])+1) if not len(a) else a; a[:,:-1]-=contrast*a[:,-1:];modified[field]=a.tolist()
            for floor in ([-1.,.2,.25,.3] if contrast==0 else [-1.,-.1,-.05,0.,.05,.1,.15]):
                keep,_=selected(modified,mode,floor);p=ms[keep].any(0) if keep else np.zeros_like(g)
                add(f'clip_{mode}_contrast{contrast}_floor{floor}',p,g,i,dict(family='clip',mode=mode,contrast=contrast,floor=floor))
for t in trials.values():
    pos=[r for r in t['rows'] if r['positive']];neg=[r for r in t['rows'] if not r['positive']]
    t.update(positive_iou=float(np.mean([r['iou'] for r in pos])),overall_iou=float(np.mean([r['iou'] for r in t['rows']])),no_target_accuracy=float(np.mean([r['pred_pixels']==0 for r in neg])))
rank=sorted(trials,key=lambda k:trials[k]['overall_iou'],reverse=True)
(out/'clip_sweep.json').write_text(json.dumps(dict(status='development only',trials=trials,rank=rank),indent=2))
for k in rank[:6]:print(k,{s:trials[k][s] for s in ['positive_iou','overall_iou','no_target_accuracy']})

