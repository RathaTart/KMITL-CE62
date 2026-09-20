"""New identities, predeclared visual references, locked no-training verifier."""
import platform,json,hashlib,time,subprocess
from pathlib import Path
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915');O=R/'confirmation';assert not O.exists();O.mkdir()
lock=json.loads((R/'method_lock.json').read_text())
for name,sha in lock['hashes'].items():assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==sha,name
# References assigned from original contact sheets BEFORE any confirmation inference.
# null = attribute ambiguous; retain image but omit that query from measured endpoints.
reference={1:[True,None],2:[None,True],3:[True,False],6:[None,True],8:[True,False],9:[False,True],10:[True,False],11:[True,None],12:[True,False],13:[True,False],14:[True,None],15:[True,False],16:[False,False],17:[False,True],18:[False,True],20:[False,True],21:[False,False],24:[False,False],26:[False,False],27:[False,None],28:[False,False],29:[False,None],30:[False,None],31:[False,False]}
candidates=json.loads((R/'candidates.json').read_text());samples=[];queries=[]
for idx,refs in reference.items():
 s=candidates[idx];assert s['source']['id'] not in lock['development_ids'];assert hashlib.sha256(Path(s['path']).read_bytes()).hexdigest()==s['sha256'];samples.append(dict(**s,candidate_index=idx,reference=dict(zip(['hat','black_coat'],refs))))
 for attribute,expected in zip(['hat','black_coat'],refs):
  if expected is not None:queries.append(dict(id=f'{idx:02d}_{attribute}',path=s['path'],attribute=attribute,expected=expected,identity=s['source']['id'],prompt='the main person wearing '+('a hat' if attribute=='hat' else 'a black coat')))
def gpu():return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True)
manifest=dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),method_lock_sha256=hashlib.sha256((R/'method_lock.json').read_bytes()).hexdigest(),samples=samples,queries=queries,gpu_before=gpu(),reference='Assistant-reviewed main-person presence, not independent human/native absence annotations. Null excludes ambiguous attribute only. Selected diagnostic, no masks GT, not full-frame evaluation.',runtime='Shared GPU. Warm resident full request; fixed verifier text embeddings cached; no image features cached.',criteria='Exploratory: more negative rejections without losing positives; timing reported with load caveat; no retuning after confirmation.',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(O/'manifest.json').write_text(json.dumps(manifest,indent=2))
from region_verifier_engine import RegionVerifier,cohd_predict
from PIL import Image
import numpy as np
engine=RegionVerifier()
for _ in range(2):
 for method in ['original','scale704_guard']:cohd_predict(queries[0]['path'],queries[0]['prompt'],method)
 engine.predict(queries[0]['path'],queries[0]['attribute'],lock['selection'])
rows=[];methods=['original','scale704_guard','verified']
for j,q in enumerate(queries):
 for method in methods[j%3:]+methods[:j%3]:
  if method=='verified':
   mask,raw,meta=engine.predict(q['path'],q['attribute'],lock['selection']);d=O/'proposal_only';d.mkdir(exist_ok=True);Image.fromarray(raw.astype('uint8')*255).save(d/(q['id']+'.png'))
   rows.append(dict(**q,method='proposal_only',nonempty=bool(raw.any()),request_s=meta['proposal_request_s'],timing_scope='CoHD portion inside verified request'))
  else:mask,meta=cohd_predict(q['path'],q['prompt'],method)
  d=O/method;d.mkdir(exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(d/(q['id']+'.png'));rows.append(dict(**q,method=method,nonempty=bool(mask.any()),**meta));print(q['id'],method,bool(mask.any()),round(meta['request_s'],3),flush=True)
 (O/'per_query.json').write_text(json.dumps(rows,indent=2))
summary={}
for method in methods+['proposal_only']:
 rr=[r for r in rows if r['method']==method];v={}
 for attr in ['hat','black_coat','all']:
  a=[r for r in rr if attr=='all' or r['attribute']==attr];P=[r for r in a if r['expected']];N=[r for r in a if not r['expected']];tp=sum(r['nonempty'] for r in P);tn=sum(not r['nonempty'] for r in N)
  v[attr]=dict(positive=len(P),negative=len(N),tp=tp,tn=tn,fn=len(P)-tp,fp=len(N)-tn,presence_agreement=(tp+tn)/len(a),balanced_presence=.5*(tp/len(P)+tn/len(N)))
 v['mean_s']=float(np.mean([r['request_s'] for r in rr]));v['p95_s']=float(np.percentile([r['request_s'] for r in rr],95));summary[method]=v
summary['verified']['mean_verification_and_overhead_s']=float(np.mean([r['verification_and_overhead_s'] for r in rows if r['method']=='verified']))
(O/'summary.json').write_text(json.dumps(dict(results=summary,gpu_after=gpu(),query_count=len(queries),image_count=len(samples),limitation=manifest['reference']+' '+manifest['runtime']),indent=2));print(json.dumps(summary,indent=2),flush=True)
