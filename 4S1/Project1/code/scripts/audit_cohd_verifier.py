"""Audit baseline reproducibility and deployed verifier agreement remotely."""
import json,platform,hashlib,pickle
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_upgrade_20260915'
old=C/'results/released_checkpoints_20260915/CoHD_Tiny/masks';new=O/'validation/masks';diff=[]
for p in new.glob('*.png'):
 a=np.asarray(Image.open(p));b=np.asarray(Image.open(old/p.name));assert a.shape==b.shape
 if np.any(a!=b):diff.append(p.name)
assert not diff,diff
lock=json.loads((O/'method_lock.json').read_text());s=lock['selected']['primary'];head=pickle.loads(Path(s['checkpoint']).read_bytes()) if 'checkpoint' in s else None
by={r['key']:r for r in map(json.loads,(O/'validation/rows.jsonl').read_text().splitlines())};items=json.loads((C/'results/router_confirm_20260915/manifest.json').read_text())['items'][:30];deploy=[]
for i in items:
 name=i['item_id']+'__expression.png';r=by[i['key']];x=np.load(r['features']);raw=np.asarray(Image.open(r['raw_mask']))>0
 score=head['model'].predict_proba(x[None,:head['dim']])[0,1] if head else x[1]/(x[0]+x[1]+1e-12)
 pred=np.zeros_like(raw) if score>=s['threshold'] else raw;actual=np.asarray(Image.open(O/'runtime/modified'/name))>0
 assert np.array_equal(pred,actual),name
 assert np.array_equal(np.asarray(Image.open(O/'runtime/baseline'/name)),np.asarray(Image.open(new/name))),name
 deploy.append(name)
result=dict(historical_baseline_masks_identical=len(list(new.glob('*.png'))),deployed_primary_masks_identical=len(deploy),checkpoint_hashes_verified={k:hashlib.sha256(Path(v['checkpoint']).read_bytes()).hexdigest()==v['sha256'] for k,v in lock['selected'].items() if 'checkpoint' in v})
assert all(result['checkpoint_hashes_verified'].values());(O/'reproduction_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
