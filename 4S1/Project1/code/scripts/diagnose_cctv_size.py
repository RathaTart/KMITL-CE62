import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment
from cctv_eval_utils import components,box_iou
assert platform.node()=='cenara70hx'
O=Path('/home/osta/lisa-eval/code/results/cohd_cctv_20260915');items=json.loads((O/'test_manifest.json').read_text())['items'];results=json.loads((O/'test_results/per_expression.json').read_text());report={}
for method,rows in results.items():
 by={r['key']:r for r in rows};bins={k:dict(gt=0,tp=0) for k in ['height_lt32','height_32to63','height_ge64']};identical=0
 for i in items:
  if i.get('domain')!='PersonPath22':continue
  mask=np.asarray(Image.open(by[i['key']]['mask']))>0;comps,_=components(mask);gt=[x['box'] for x in i['boxes']];scores=np.array([[box_iou(b,g) for g in gt] for _,b in comps]).reshape(len(comps),len(gt));matched=set()
  if scores.size:
   a,b=linear_sum_assignment(-scores);matched={int(y) for x,y in zip(a,b) if scores[x,y]>=.5}
  for j,g in enumerate(gt):
   height=g[3]-g[1];kind='height_lt32' if height<32 else 'height_32to63' if height<64 else 'height_ge64';bins[kind]['gt']+=1;bins[kind]['tp']+=j in matched
 for b in bins.values():b['recall']=b['tp']/max(1,b['gt'])
 report[method]=bins
by={m:{r['key']:r for r in rows} for m,rows in results.items()};same=sum(np.array_equal(np.asarray(Image.open(by['customA'][i['key']]['mask'])),np.asarray(Image.open(by['customB'][i['key']]['mask']))) for i in items)
out=dict(posthoc_descriptive_only=True,PersonPath22_height_bins=report,customA_customB_identical_test_masks=same,test_images=len(items));(O/'size_diagnostic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
