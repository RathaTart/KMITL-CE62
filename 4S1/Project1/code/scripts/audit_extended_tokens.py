import json,collections,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');result={}
for name in ['qwen_presence','qwen_lisa','qwen_candidate']:
    p=out/(name+'.jsonl');rows=[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
    scores=[v for r in rows for v in r['results']];result[name]={'n_images':len(rows),'n_scores':len(scores),'top_tokens':dict(collections.Counter(r['top_token'] for r in scores)),'total_model_seconds':sum(r['seconds'] for r in scores)}
print(json.dumps(result,indent=2));(out/'token_audit_interim.json').write_text(json.dumps(result,indent=2))
