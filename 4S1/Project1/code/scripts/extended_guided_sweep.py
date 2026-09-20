"""Guided-filter ablation using the original image as grayscale guidance."""
import json,platform
from pathlib import Path
import cv2,numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');items=json.loads((out/'manifest.json').read_text())['items'];trials={}
for i in items:
    p=np.asarray(Image.open(i['lisa_mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0;guide=np.asarray(Image.open(i['image']).convert('L')).astype('float32')/255
    for radius in [2,4,8,16]:
        size=(2*radius+1,)*2
        mean=lambda v:cv2.boxFilter(v,-1,size,normalize=True,borderType=cv2.BORDER_REFLECT)
        mi=mean(guide);mp=mean(p.astype('float32'));var=mean(guide*guide)-mi*mi;cov=mean(guide*p)-mi*mp
        for eps in [.0001,.001,.01]:
            a=cov/(var+eps);b=mp-a*mi;filtered=mean(a)*guide+mean(b)
            for threshold in [.4,.5,.6]:
                pred=filtered>=threshold;inter=int((pred&g).sum());union=int((pred|g).sum());label=f'guided_{radius}_{eps}_{threshold}'
                trials.setdefault(label,dict(config=dict(family='guided',radius=radius,eps=eps,threshold=threshold),rows=[]))['rows'].append(dict(key=i['key'],positive=bool(g.any()),iou=inter/union if union else 1.,intersection=inter,union=union,pred_pixels=int(pred.sum()),gt_pixels=int(g.sum())))
for t in trials.values():
    pos=[r for r in t['rows'] if r['positive']];neg=[r for r in t['rows'] if not r['positive']]
    t.update(positive_iou=float(np.mean([r['iou'] for r in pos])),overall_iou=float(np.mean([r['iou'] for r in t['rows']])),no_target_accuracy=float(np.mean([r['pred_pixels']==0 for r in neg])))
rank=sorted(trials,key=lambda k:trials[k]['positive_iou'],reverse=True)
(out/'guided_sweep.json').write_text(json.dumps(dict(status='development only',reference='https://people.csail.mit.edu/kaiming/eccv10/index.html',implementation='Grayscale local-linear guided filter, reflection borders, binary-mask input, scalar threshold',trials=trials,rank=rank),indent=2))
for k in rank[:6]:print(k,{s:trials[k][s] for s in ['positive_iou','overall_iou','no_target_accuracy']})
