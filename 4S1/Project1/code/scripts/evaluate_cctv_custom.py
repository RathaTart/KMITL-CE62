import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from PIL import Image
from cctv_engine import CCTVEngine,O
from cctv_eval_utils import metrics,aggregate
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--out',required=True);a=p.parse_args();D=Path(a.out);assert not D.exists();D.mkdir(parents=True);engine=CCTVEngine();items=json.loads(Path(a.manifest).read_text())['items'];results={k:[] for k in ['original','customA','customB']}
for j,i in enumerate(items):
 for mode in ['original','customA']:
  mask,meta,x,raw=engine.predict(i['image'],i['expression'],mode,features=mode=='customA');folder=D/mode;folder.mkdir(exist_ok=True);path=folder/(i['item_id']+'__expression.png');Image.fromarray(mask.astype('uint8')*255).save(path);r=dict(key=i['key'],source_group=i.get('source_group',str(i.get('image_id',i['item_id']))),domain=i.get('domain','gref'),target_count=i['target_count'],metrics=metrics(i,mask),mask=str(path),mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**meta);results[mode].append(r)
  if mode=='customA':
   score=float(engine.head['model'].predict_proba(x[None])[0,1]);nt=score>=engine.head['threshold'];bmask=np.zeros_like(raw) if nt else raw;folder=D/'customB';folder.mkdir(exist_ok=True);path=folder/(i['item_id']+'__expression.png');Image.fromarray(bmask.astype('uint8')*255).save(path);results['customB'].append(dict(key=i['key'],source_group=r['source_group'],domain=r['domain'],target_count=i['target_count'],metrics=metrics(i,bmask),mask=str(path),mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),verifier_score=score,no_target=nt,reused_customA_forward=True))
 with (D/'progress.json').open('w') as f:json.dump(dict(done=j+1,total=len(items)),f)
 print(j+1,len(items),flush=True)
summary={k:aggregate(v) for k,v in results.items()};(D/'per_expression.json').write_text(json.dumps(results,indent=2));(D/'summary.json').write_text(json.dumps(summary,indent=2));(D/'provenance.json').write_text(json.dumps(dict(manifest=a.manifest,manifest_sha256=hashlib.sha256(Path(a.manifest).read_bytes()).hexdigest(),customA_lock_sha256=hashlib.sha256((O/'customA_lock.json').read_bytes()).hexdigest(),customB_lock_sha256=hashlib.sha256((O/'customB_lock.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),timing='Diagnostic runs export features. Use separate paired deployment timing; CustomB masks reuse identical CustomA forward.'),indent=2));print(json.dumps(summary,indent=2))
