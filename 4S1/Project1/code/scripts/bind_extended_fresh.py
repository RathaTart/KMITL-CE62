"""Bind immutable fresh inputs to saved frozen-stage predictions without reading GT."""
import json,hashlib,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');src=root/'results/training_free_extended_20260915';props=root/'results/global_local_extended_20260915';out=root/'results/extended_test_20260915';out.mkdir(exist_ok=True)
m=json.loads((src/'manifest.json').read_text())
for i in m['items']:
    n=i['item_id']+'__'+i['prompt_id'];i['lisa_mask']=str(src/'p1_masks'/(n+'.png'));i['proposals']=str(props/'proposals'/(n+'.npz'))
    assert Path(i['lisa_mask']).exists() and Path(i['proposals']).exists()
m.update(source_manifest=str(src/'manifest.json'),source_manifest_sha256=hashlib.sha256((src/'manifest.json').read_bytes()).hexdigest(),status='Fresh prediction workspace; source selection manifest unchanged')
(out/'manifest.json').write_text(json.dumps(m,indent=2));print('Bound',len(m['items']))
