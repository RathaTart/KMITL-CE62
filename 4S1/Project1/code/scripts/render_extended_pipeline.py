"""Render locked pipelines without reading ground-truth masks."""
import argparse,hashlib,json,platform,re,time
from pathlib import Path
import numpy as np
from PIL import Image
from extended_pipeline import pipeline_mask
assert platform.node()=='cenara70hx'
ROOT=Path('/home/osta/lisa-eval/code');p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results/extended_test_20260915');p.add_argument('--lock',type=Path,default=ROOT/'results/extended_dev_20260915/method_lock.json');a=p.parse_args();lock=json.loads(a.lock.read_text());manifest=json.loads((a.out/'manifest.json').read_text())
for fn,digest in lock['script_sha256'].items():assert hashlib.sha256((ROOT/'scripts'/fn).read_bytes()).hexdigest()==digest,('Script changed after freeze',fn)
records={}
for source in ['qwen_presence','qwen_lisa','qwen_candidate','blip_presence','rexseek','rexseek_clauses']:
    path=a.out/(source+'.jsonl')
    if path.exists():records[source]={r['key']:r for r in [json.loads(s) for s in path.read_text().splitlines() if s]}
basevalid={};parents={Path(i['lisa_mask']).parent.parent for i in manifest['items']}
for folder in parents:
    for line in (folder/'p1_rows.jsonl').read_text().splitlines():
        r=json.loads(line);answer=r['answer'].split('ASSISTANT:')[-1].lower();basevalid[r['key']]=bool(r['emitted_seg']) or bool(re.search(r'\bno (?:matching )?(?:person|people|man|woman|one)\b|not (?:present|visible)|\bnone\b',answer))
applied=a.out/'applied_method_lock.json'
if applied.exists():assert json.loads(applied.read_text())==lock,'Different existing lock'
else:applied.write_text(a.lock.read_text())
rows=[]
for method,cfg in lock['variants'].items():
    folder=a.out/'predictions'/method/'masks';folder.mkdir(parents=True,exist_ok=True)
    for i in manifest['items']:
        start=time.perf_counter();lisa=np.asarray(Image.open(i['lisa_mask']))>0;ms=np.load(i['proposals'])['masks'];im=np.asarray(Image.open(i['image']).convert('RGB'));pred,valid,audit=pipeline_mask(i,lisa,ms,cfg,records,im)
        if not cfg.get('selector') and not audit.get('replaced_lisa') and not audit.get('rejected'):valid=valid and basevalid[i['key']]
        path=folder/(i['item_id']+'__'+i['prompt_id']+'.png')
        if path.exists():assert np.array_equal(np.asarray(Image.open(path))>0,pred),('Output differs',method,i['key'])
        else:Image.fromarray(pred.astype('uint8')*255).save(path)
        rows.append(dict(key=i['key'],method=method,mask=str(path),valid=valid,decisions=audit,render_seconds=time.perf_counter()-start,mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print('rendered',method,len(manifest['items']),flush=True)
(a.out/'prediction_audit.json').write_text(json.dumps(rows,indent=2))

