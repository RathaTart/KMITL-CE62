import json,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
p=Path('/home/osta/lisa-eval/code/results/cohd_cctv_20260915/source/uid_vid_00144.json');a=json.loads(p.read_text());print(json.dumps(a['metadata'],indent=2));print(json.dumps(a['entities'][:3],indent=2));print('unique labels', sorted({k for e in a['entities'] for k in e.get('labels',{})}))
