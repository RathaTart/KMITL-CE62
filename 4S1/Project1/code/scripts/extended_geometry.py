"""Development-only sweep of frozen mask geometry and proposal agreement."""
import json,platform,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');out=root/'results/extended_dev_20260915'
m=json.loads((out/'manifest.json').read_text());trials={}
def metric(p,g):
    inter=int((p&g).sum());union=int((p|g).sum());return inter/union if union else 1.
def add(label,p,g,i,config):
    trials.setdefault(label,dict(config=config,rows=[]))['rows'].append(dict(key=i['key'],positive=bool(g.any()),iou=metric(p,g),pred_pixels=int(p.sum()),gt_pixels=int(g.sum()),intersection=int((p&g).sum()),union=int((p|g).sum())))
for i in m['items']:
    p=np.asarray(Image.open(i['lisa_mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0
    add('lisa',p,g,i,dict(family='baseline'))
    add('fill_holes',binary_fill_holes(p),g,i,dict(family='fill_holes'))
    for size in [3,5,7,11]:
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size))
        for op in ['open','close','dilate','erode','median']:
            u=p.astype('uint8')
            if op=='median':q=cv2.medianBlur(u,size)>0
            elif op=='dilate':q=cv2.dilate(u,kernel)>0
            elif op=='erode':q=cv2.erode(u,kernel)>0
            else:q=cv2.morphologyEx(u,cv2.MORPH_OPEN if op=='open' else cv2.MORPH_CLOSE,kernel)>0
            add(f'{op}_{size}',q,g,i,dict(family=op,size=size))
    n,labels,stats,_=cv2.connectedComponentsWithStats(p.astype('uint8'),8)
    for fraction in [.0001,.0005,.001,.005,.01]:
        keep=np.flatnonzero(stats[:,cv2.CC_STAT_AREA]>=fraction*p.size);keep=keep[keep!=0];q=np.isin(labels,keep)
        add(f'remove_small_{fraction}',q,g,i,dict(family='remove_small',fraction=fraction))
    data=np.load(i['proposals']);ms=data['masks'];ints=(ms&p).sum((1,2));areas=ms.sum((1,2));coverage=ints/np.maximum(areas,1)
    for cutoff in [.25,.5,.75,.9]:
        q=ms[coverage>=cutoff].any(0) if len(ms) else np.zeros_like(p)
        for op in ['sam','intersect','union','vote']:
            r=q if op=='sam' else p&q if op=='intersect' else p|q if op=='union' else (p.astype('int32')+ms[coverage>=cutoff].sum(0)>=2 if len(ms) else p)
            add(f'agreement_{op}_{cutoff}',r,g,i,dict(family='agreement',op=op,coverage=cutoff))
for t in trials.values():
    rows=t['rows'];pos=[r for r in rows if r['positive']];neg=[r for r in rows if not r['positive']]
    t['positive_iou']=float(np.mean([r['iou'] for r in pos]));t['overall_iou']=float(np.mean([r['iou'] for r in rows]));t['no_target_accuracy']=float(np.mean([r['pred_pixels']==0 for r in neg]));t['ciou']=sum(r['intersection'] for r in pos)/max(1,sum(r['union'] for r in pos))
rank=sorted(trials,key=lambda k:trials[k]['positive_iou'],reverse=True)
result=dict(status='Development only, not evidence of held-out superiority',trials=trials,rank=rank,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'geometry_sweep.json').write_text(json.dumps(result,indent=2))
for k in rank[:12]:print(k,{s:trials[k][s] for s in ['positive_iou','no_target_accuracy','overall_iou']})
