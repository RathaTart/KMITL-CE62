import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');F=C/'results/router_confirm_20260915';O=C/'results/released_checkpoints_20260915';items=json.loads((F/'manifest.json').read_text())['items'][:3];rows=[]
for i in items:
 n=i['item_id']+'__'+i['prompt_id']+'.png';p=np.asarray(Image.open(O/'SSP_SAM_224/masks'/n))>0;q=np.asarray(Image.open(C/'results/released_diagnostic_20260915/SSP_FP32/masks'/n))>0;g=np.asarray(Image.open(i['ground_truth']))>0
 rows.append(dict(key=i['key'],different_pixels=int((p!=q).sum()),half_iou=float((p&g).sum()/max(1,(p|g).sum())),float_iou=float((q&g).sum()/max(1,(q|g).sum()))))
(O/'ssp_precision_diagnostic.json').write_text(json.dumps(rows,indent=2));print(rows)
