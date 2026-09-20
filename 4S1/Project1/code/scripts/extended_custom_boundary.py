"""Custom training-free boundary rules: component cleanup plus conservative SAM support."""
import json,platform
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes,distance_transform_edt
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');items=json.loads((out/'manifest.json').read_text())['items'];trials={}
def add(label,p,g,i,cfg):
    inter=int((p&g).sum());union=int((p|g).sum());trials.setdefault(label,dict(config=cfg,rows=[]))['rows'].append(dict(key=i['key'],positive=bool(g.any()),iou=inter/union if union else 1.,intersection=inter,union=union,pred_pixels=int(p.sum()),gt_pixels=int(g.sum())))
for i in items:
    lisa=np.asarray(Image.open(i['lisa_mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0;ms=np.load(i['proposals'])['masks'];coverage=(ms&lisa).sum((1,2))/np.maximum(ms.sum((1,2)),1)
    for cutoff in [.5,.75]:
        sam=ms[coverage>=cutoff].any(0) if len(ms) else np.zeros_like(g)
        for fraction in [.0005,.001,.005]:
            merged=lisa|sam;n,labels,stats,_=cv2.connectedComponentsWithStats(merged.astype('uint8'),8);keep=np.flatnonzero(stats[:,cv2.CC_STAT_AREA]>=fraction*g.size);keep=keep[keep!=0];p=np.isin(labels,keep)
            add(f'union_clean_{cutoff}_{fraction}',p,g,i,dict(family='union_clean',coverage=cutoff,fraction=fraction))
        for margin in [3,7,15,25]:
            support=cv2.dilate(sam.astype('uint8'),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(margin,margin)))>0
            for mincover in [.8,.9,.95]:
                allowed=(lisa&sam).sum()/max(lisa.sum(),1)>=mincover
                p=(lisa&support)|sam if allowed else lisa|sam
                add(f'trim_union_{cutoff}_{margin}_{mincover}',p,g,i,dict(family='trim_union',coverage=cutoff,margin=margin,mincover=mincover))
        if sam.any() and lisa.any():
            ld=distance_transform_edt(lisa)-distance_transform_edt(~lisa);sd=distance_transform_edt(sam)-distance_transform_edt(~sam)
            overlap=(sam&lisa).sum()/max((sam|lisa).sum(),1)
        else:ld=sd=None;overlap=0.
        for weight in [.25,.5,.75]:
            for minagreement in [.5,.75,.9]:
                p=((1-weight)*ld+weight*sd)>0 if overlap>=minagreement and ld is not None else lisa
                add(f'distance_blend_{cutoff}_{weight}_{minagreement}',p,g,i,dict(family='distance_blend',coverage=cutoff,weight=weight,minagreement=minagreement))
for t in trials.values():
    pos=[r for r in t['rows'] if r['positive']];neg=[r for r in t['rows'] if not r['positive']]
    t.update(positive_iou=float(np.mean([r['iou'] for r in pos])),overall_iou=float(np.mean([r['iou'] for r in t['rows']])),no_target_accuracy=float(np.mean([r['pred_pixels']==0 for r in neg])))
rank=sorted(trials,key=lambda k:trials[k]['positive_iou'],reverse=True)
(out/'custom_boundary_sweep.json').write_text(json.dumps(dict(status='development only',trials=trials,rank=rank),indent=2))
for k in rank[:8]:print(k,{s:trials[k][s] for s in ['positive_iou','overall_iou','no_target_accuracy']})
