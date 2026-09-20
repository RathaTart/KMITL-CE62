"""Run only the frozen finalists' required verifier/selector stages, serially."""
import json,platform,subprocess,time
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');out=root/'results/extended_test_20260915';lock=json.loads((root/'results/extended_dev_20260915/method_lock.json').read_text());assert (out/'manifest.json').exists();required=set();python='/home/osta/blip2-qformer-eval/.venv/bin/python'
for cfg in lock['variants'].values():
    if 'verifier' in cfg:required.update(cfg['verifier'].get('sources') or [cfg['verifier']['source']])
    choice=cfg.get('selector') or cfg.get('correction')
    if choice:required.add('qwen_candidate' if choice['family'].startswith('qwen') else 'rexseek_clauses' if choice['family'].startswith('rexseek_clauses') else 'rexseek')
for source in sorted(required):
    while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():time.sleep(10)
    if source.startswith('qwen_'):cmd=[python,'scripts/extended_training_free.py','qwen','--view',source.removeprefix('qwen_'),'--out',str(out)]
    elif source=='blip_presence':cmd=[python,'scripts/extended_blip.py','--out',str(out)]
    elif source=='rexseek_clauses':cmd=[python,'scripts/extended_rexseek_clauses.py','--out',str(out)]
    else:cmd=[python,'scripts/extended_rexseek.py','--out',str(out)]
    print('Running',source,flush=True)
    with (out/(source+'.log')).open('a') as log:subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
(out/'required_stages.json').write_text(json.dumps(dict(required=sorted(required),method_lock_sha256=__import__('hashlib').sha256((root/'results/extended_dev_20260915/method_lock.json').read_bytes()).hexdigest()),indent=2))


