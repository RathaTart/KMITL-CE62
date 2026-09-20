import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from cctv_engine import CCTVEngine,O,C,model
engine=CCTVEngine();P=model.sem_seg_head.predictor;items={i['key']:i for i in json.loads((O/'validation_manifest.json').read_text())['items']};idx={r['key']:r['cache'] for r in json.loads((O/'cache_validation/index.json').read_text())};runtime=json.loads((O/'runtime.json').read_text());checked=0
with torch.inference_mode():
 for r in runtime['rows']:
  i=items[r['key']];b=torch.load(idx[i['key']],map_location='cpu',weights_only=True);w,h=Image.open(i['image']).size;name=i['item_id']+'__expression.png';engine.prepare_mode('customA',False);q=b['queries'].cuda();lo=F.interpolate(P.dha([v.cuda() for v in b['attns']],list(q.unbind(0)),P.class_embed(P.mask_embed(q)),weights=P.weights)[-1],size=(480,480),mode='bilinear',align_corners=False)[0]
  margin=lo[1]-lo[0];prob=margin.sigmoid();fg=margin>0;stats=torch.stack([prob.mean(),prob.std(),fg.float().mean(),prob[fg].mean() if fg.any() else prob.new_zeros(()),prob.max(),margin.mean(),margin.std()]);x=torch.cat([b['nt'].cuda().flatten(),b['count'].cuda().flatten(),stats,q.mean(dim=(0,2)).flatten()]).cpu().numpy();score=engine.head['model'].predict_proba(x[None])[0,1]
  for mode in ['original','customA','customB']:
   native=(b['teacher'] if mode=='original' else lo.cpu()).argmax(0).byte().numpy();mask=np.asarray(Image.fromarray(native).resize((w,h),Image.Resampling.NEAREST))>0;nt=bool(b['nt'].argmax()) if mode!='customB' else score>=engine.head['threshold']
   if nt:mask=np.zeros_like(mask)
   actual=np.asarray(Image.open(O/'runtime'/mode/name))>0;assert np.array_equal(mask,actual),(i['key'],mode,int((mask!=actual).sum()));checked+=1
old=C/'results/cohd_upgrade_20260915/test/baseline/masks';new=O/'regression_results/original';count=0
for p in new.glob('*.png'):
 assert np.array_equal(np.asarray(Image.open(p)),np.asarray(Image.open(old/p.name))),p.name;count+=1
assert count==300
result=dict(integrated_vs_cached_prediction_masks_identical=checked,historical_original_masks_identical=count,customA_checkpoint_sha256=hashlib.sha256(Path(engine.a['checkpoint']).read_bytes()).hexdigest(),customB_checkpoint_sha256=hashlib.sha256(Path(engine.b['checkpoint']).read_bytes()).hexdigest());assert result['customA_checkpoint_sha256']==engine.a['sha256'];assert result['customB_checkpoint_sha256']==engine.b['sha256'];(O/'execution_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
