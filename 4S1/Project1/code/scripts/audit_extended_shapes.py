"""Verify final transformation implementation reproduces development evidence."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from extended_shapes import shape_mask
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');items=json.loads((out/'manifest.json').read_text())['items'];checked=[]
for fn in ['geometry_sweep.json','custom_boundary_sweep.json','guided_sweep.json']:
    data=json.loads((out/fn).read_text());chosen=data['rank'][:3]
    if fn=='geometry_sweep.json':chosen+=['lisa','agreement_intersect_0.5','remove_small_0.005']
    for label in chosen:
        trial=data['trials'][label];expected={r['key']:r for r in trial['rows']}
        for i in items:
            lisa=np.asarray(Image.open(i['lisa_mask']))>0;ms=np.load(i['proposals'])['masks'];image=np.asarray(Image.open(i['image']).convert('RGB'));g=np.asarray(Image.open(i['ground_truth']))>0
            p=shape_mask(lisa,ms,trial['config'],image);e=expected[i['key']]
            assert int(p.sum())==e['pred_pixels'],(label,i['key'],'pixels')
            assert int((p&g).sum())==e['intersection'] and int((p|g).sum())==e['union'],(label,i['key'],'score')
        checked.append(label)
(out/'shape_implementation_audit.json').write_text(json.dumps(dict(status='passed',checked=checked,n_images=len(items),test='Byte-count/intersection/union reproduction for final renderer versus separately implemented development sweeps'),indent=2));print('PASS',len(checked),'configurations x',len(items),'images')
