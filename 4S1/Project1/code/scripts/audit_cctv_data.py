"""Audit source separation, native annotations and reproducible local scripts remotely."""
import json,hashlib,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_cctv_20260915';sets={k:json.loads((O/(k+'_manifest.json')).read_text())['items'] for k in ['fit','validation','test','regression']};groups={k:sorted({i['source_group'] for i in v if 'source_group' in i}) for k,v in sets.items()};hashes={k:{i['image_sha256'] if 'image_sha256' in i else hashlib.sha256(Path(i['image']).read_bytes()).hexdigest() for i in v} for k,v in sets.items()}
assert not set(groups['fit'])&set(groups['validation']);assert not set(groups['test'])&(set(groups['fit'])|set(groups['validation']))
assert not hashes['test']&(hashes['fit']|hashes['validation']);assert not hashes['regression']&(hashes['fit']|hashes['validation'])
stats={}
for k,items in sets.items():
 stats[k]=dict(expressions=len(items),unique_images=len(hashes[k]),sources=groups[k],native_mask_expressions=sum('ground_truth' in i for i in items),native_box_expressions=sum('boxes' in i for i in items),gt_person_observations=sum(i['target_count'] for i in items))
 for i in items:
  if i.get('domain')=='PersonPath22':assert abs(i['annotation_time_ms']-i['frame']/23.97*1000)<100
result=dict(splits=stats,source_group_overlap=0,test_image_overlap=0,regression_image_overlap=0,regression_status='Previously explored 300 images; not untouched evaluation',script_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (C/'scripts').glob('*cctv*.py')});(O/'data_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(stats,indent=2))
