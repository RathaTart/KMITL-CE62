import json,platform
from pathlib import Path
import numpy as np
from cctv_eval_utils import metrics
assert platform.node()=='cenara70hx'
a=np.zeros((50,60),bool);a[5:15,5:15]=1;a[25:40,35:45]=1;i=dict(boxes=[{'box':[5,5,15,15]},{'box':[35,25,45,40]}],ignore_boxes=[])
r=metrics(i,a);assert (r['tp'],r['fp'],r['fn'])==(2,0,0),r
r=metrics(i,np.zeros_like(a));assert (r['tp'],r['fp'],r['fn'])==(0,0,2),r
a[2:5,50:53]=1;r=metrics(i,a);assert (r['tp'],r['fp'],r['fn'])==(2,1,0),r
i['ignore_boxes']=[[49,1,54,6]];r=metrics(i,a);assert (r['tp'],r['fp'],r['fn'])==(2,0,0),r
result=dict(exact_matches=True,empty_predictions=True,false_component=True,ignore_suppression=True);p=Path('/home/osta/lisa-eval/code/results/cohd_cctv_20260915/metric_checks.json');p.write_text(json.dumps(result,indent=2));print(result)
