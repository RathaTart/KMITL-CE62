"""Reproduce the locked primary and aggressive development scores from saved PNGs."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');lock=json.loads((out/'method_lock.json').read_text());sweep=json.loads((out/'composition_sweep.json').read_text());items=json.loads((out/'manifest.json').read_text())['items'];audit={(r['method'],r['key']):r for r in json.loads((out/'prediction_audit.json').read_text())};checks={}
for method,label in [('Custom_primary',lock['primary_development_label']),('Custom_aggressive',sweep['aggressive'])]:
    expected={r['key']:r for r in sweep['trials'][label]['rows']};rows=[]
    for i in items:
        p=np.asarray(Image.open(out/'predictions'/method/'masks'/(i['item_id']+'__'+i['prompt_id']+'.png')))>0;g=np.asarray(Image.open(i['ground_truth']))>0;inter=int((p&g).sum());union=int((p|g).sum());valid=audit[method,i['key']]['valid'];iou=(inter/union if union else 1.) if valid else 0.
        assert abs(iou-expected[i['key']]['iou'])<1e-12,(method,i['key']);assert int(p.sum())==expected[i['key']]['pred_pixels']
        rows.append(iou)
    checks[method]=dict(n=len(rows),overall_iou=float(np.mean(rows)),status='exact reproduction')
(out/'locked_dev_reproduction.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2));print(json.dumps(checks,indent=2))
