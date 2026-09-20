"""Remote diagnostic, frozen methods; no native mask/absence GT available."""
import platform,json,hashlib,time,subprocess,shutil
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915')
out=root/'diagnostic';assert not out.exists(),'Refuse overwrite';out.mkdir()
selected=json.loads((root/'selected.json').read_text())
indices=[0,2,8,9,11,12]
samples=[]
for i in indices:
 s=selected[i];s['hat_reference']=i in [0,2];s['black_coat_reference']=i not in [0,2];samples.append(s)
queries=[]
for i,s in enumerate(samples):
 for kind,prompt,expected in [('hat','the main person wearing a hat',s['hat_reference']),('black_coat','the main person wearing a black coat',s['black_coat_reference']),('native',s['native_caption'],True)]:
  queries.append(dict(id=f'{i:02d}_{kind}',sample_index=i,path=s['path'],prompt=prompt,kind=kind,expected_presence=expected))
def gpu():return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
lock=dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source='https://github.com/NjtechCVLab/RSTPReid-Dataset',samples=samples,queries=queries,methods=['original','scale704_guard'],training=False,selection='First matching test identities, then assistant visual audit before predictions; indices 0,2,8,9,11,12. Other candidates excluded for hood/hat or color ambiguity.',reference='Positive native captions cross-checked visually; negative short prompts assigned by assistant visual review, not official absence annotations or independent human labels.',metric='Nonempty output versus expected main-person presence ONLY, not mask IoU or verified instance selection.',gpu_before=gpu(),timing='Resident request; model load excluded; shared GPU, not comparable to prior idle measurements.',hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('cohd_scale_engine.py'),Path(__file__).with_name('cohd_verifier_engine.py')]})
(out/'lock.json').write_text(json.dumps(lock,indent=2));shutil.copy(__file__,out/'run_source.py')
from cohd_scale_engine import predict
from PIL import Image
import numpy as np
for method in lock['methods']:
 for _ in range(2):predict(samples[0]['path'],'the person',method)
rows=[]
for j,q in enumerate(queries):
 for method in lock['methods'][j%2:]+lock['methods'][:j%2]:
  mask,meta=predict(q['path'],q['prompt'],method);folder=out/method;folder.mkdir(exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(folder/(q['id']+'.png'))
  rows.append(dict(**q,method=method,output_nonempty=bool(mask.any()),presence_agreement=bool(mask.any())==q['expected_presence'],mask_fraction=float(mask.mean()),**meta));print(q['id'],method,bool(mask.any()),round(meta['request_s'],3),flush=True)
 (out/'per_query.json').write_text(json.dumps(rows,indent=2))
summary={}
for method in lock['methods']:
 r=[x for x in rows if x['method']==method];d={}
 for kind in ['hat','black_coat','native']:
  a=[x for x in r if x['kind']==kind];pos=[x for x in a if x['expected_presence']];neg=[x for x in a if not x['expected_presence']]
  d[kind]=dict(n=len(a),positive_n=len(pos),positive_nonempty=sum(x['output_nonempty'] for x in pos),negative_n=len(neg),negative_empty=sum(not x['output_nonempty'] for x in neg),agreement=sum(x['presence_agreement'] for x in a))
 d['mean_resident_s']=float(np.mean([x['request_s'] for x in r]));summary[method]=d
(out/'summary.json').write_text(json.dumps(dict(results=summary,gpu_after=gpu(),limitations=lock['reference']+' '+lock['metric']+' '+lock['timing']),indent=2));print(json.dumps(summary,indent=2))
