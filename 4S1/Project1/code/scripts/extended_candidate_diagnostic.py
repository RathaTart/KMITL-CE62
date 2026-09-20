"""Development candidate ceiling diagnostics; annotations never drive deployed selection."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');items=json.loads((out/'manifest.json').read_text())['items'];rows=[]
for i in items:
    ms=np.load(i['proposals'])['masks'];gts=[np.asarray(Image.open(p))>0 for p in i['ground_truth_instances']]
    if not gts:continue
    ious=np.array([[(p&g).sum()/max((p|g).sum(),1) for g in gts] for p in ms]).reshape(len(ms),len(gts));matches={}
    for threshold in [.5,.75]:
        if len(ms):a,b=linear_sum_assignment(-(ious>=threshold).astype(float)*1000000-ious);hit=sum(ious[x,y]>=threshold for x,y in zip(a,b))
        else:hit=0
        matches[str(threshold)]=int(hit)
    rows.append(dict(key=i['key'],targets=len(gts),proposals=len(ms),matched_targets=matches))
summary={t:dict(matched=sum(r['matched_targets'][t] for r in rows),total=sum(r['targets'] for r in rows)) for t in ['0.5','0.75']}
for r in summary.values():r['recall']=r['matched']/max(r['total'],1)
(out/'candidate_matching_diagnostic.json').write_text(json.dumps(dict(scope='Explored 90-image development only',definition='Maximum-cardinality one-to-one matching of candidate SAM masks to target GT masks at each IoU threshold, IoU sum breaks ties. This assesses proposal availability, not deployed language-selection accuracy.',summary=summary,rows=rows),indent=2));print(json.dumps(summary,indent=2))
