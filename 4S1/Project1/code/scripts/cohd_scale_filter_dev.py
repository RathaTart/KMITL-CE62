"""Development-only shape-filter controls and size diagnostics, remote."""
import json,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
import cv2,numpy as np
from PIL import Image
from cctv_eval_utils import metrics,aggregate,components,box_iou
from scipy.optimize import linear_sum_assignment
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_scale_20260915';items=json.loads((O/'dev_manifest.json').read_text())['items'];old=json.loads((O/'dev_adapt/per_image.json').read_text());rules=[(12,.8),(12,1.2),(20,.8),(20,1.2)]
def filter_mask(mask,minheight,ratio):
 n,labels,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8);keep=np.zeros(n,bool)
 for j,(x,y,w,h,area) in enumerate(stats):
  if not j:continue
  keep[j]=area>=4096 or (h>=minheight and w/max(1,h)<=ratio)
 return keep[labels]
def sizes(item,mask):
 boxes=[g['box'] for g in item['boxes']];comps,_=components(mask);scores=np.array([[box_iou(p,g) for g in boxes] for _,p in comps]).reshape(len(comps),len(boxes));matched=set()
 if scores.size:
  a,b=linear_sum_assignment(-scores);matched={int(y) for x,y in zip(a,b) if scores[x,y]>=.5}
 return {str(cut):dict(gt=sum(g[3]-g[1]<cut for g in boxes),tp=sum(j in matched and g[3]-g[1]<cut for j,g in enumerate(boxes))) for cut in [32,64]}
out={};index={i['key']:i for i in items}
for method in ['original','amp_480','adapt_amp640','adapt_amp768','full_center_amp480']:
 for rule in [None]+rules:
  name=method if rule is None else method+f'_shape{rule[0]}_{rule[1]}'
  rows=[];small={str(c):dict(gt=0,tp=0) for c in [32,64]}
  for r in old[method]:
   i=index[r['key']]
   if i['domain']!='PersonPath22':continue
   mask=np.asarray(Image.open(r['mask']))>0
   if rule:mask=filter_mask(mask,*rule)
   rows.append(dict(domain=i['domain'],target_count=i['target_count'],metrics=metrics(i,mask)))
   for c,v in sizes(i,mask).items():
    for field,n in v.items():small[c][field]+=n
  out[name]=dict(box=aggregate(rows),small=small,rule=rule)
(O/'filter_development.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
