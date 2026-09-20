"""Train and lock a conservative verifier on Custom A development outputs."""
import json,pickle,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from cohd_verifier_engine import model,C
O=C/'results/cohd_cctv_20260915';P=model.sem_seg_head.predictor;lock=json.loads((O/'customA_lock.json').read_text());state=torch.load(lock['checkpoint'],map_location='cuda',weights_only=True)
for name,weights in state.items():getattr(P,name).load_state_dict(weights,strict=True)
def extract(split):
 items=json.loads((O/(split+'_manifest.json')).read_text())['items'];index={r['key']:r['cache'] for r in json.loads((O/('cache_'+split)/'index.json').read_text())};xs=[];ys=[];raw=[];baseempty=[]
 with torch.inference_mode():
  for i in items:
   b=torch.load(index[i['key']],map_location='cpu',weights_only=True);q=b['queries'].cuda();lo=F.interpolate(P.dha([v.cuda() for v in b['attns']],list(q.unbind(0)),P.class_embed(P.mask_embed(q)),weights=P.weights)[-1],size=(480,480),mode='bilinear',align_corners=False)[0];margin=lo[1]-lo[0];prob=margin.sigmoid();fg=margin>0;stats=torch.stack([prob.mean(),prob.std(),fg.float().mean(),prob[fg].mean() if fg.any() else prob.new_zeros(()),prob.max(),margin.mean(),margin.std()]);x=torch.cat([b['nt'].cuda().flatten(),b['count'].cuda().flatten(),stats,q.mean(dim=(0,2)).flatten()]).cpu().numpy();xs.append(x);ys.append(i['target_count']==0);baseempty.append(bool(b['nt'].argmax()) or not bool(fg.any()))
   if 'ground_truth' in i:
    g=np.asarray(Image.open(i['ground_truth']))>0;m=np.asarray(Image.fromarray(fg.cpu().numpy()).resize((g.shape[1],g.shape[0]),Image.Resampling.NEAREST))>0;raw.append(float((m&g).sum()/max(1,(m|g).sum())))
   else:raw.append(1.)
 return np.array(xs),np.array(ys),np.array(raw),np.array(baseempty),items
x,y,_,_,fit=extract('fit');v,z,raw,empty,items=extract('validation');baseline=raw*(~empty);gref=np.array([i.get('domain','gref')=='gref' for i in items]);positive=~z;models={};rows=[]
for strength in [.01,.1]:
 m=make_pipeline(StandardScaler(),LogisticRegression(C=strength,class_weight={False:4.,True:1.},max_iter=2000,random_state=20260915));m.fit(x,y);models[strength]=m;probs=m.predict_proba(v)[:,1]
 for threshold in list(np.linspace(.50,.99,50))+[1.01]:
  rejection=probs>=threshold;score=raw*(~rejection);ok=bool(not np.any(rejection&positive&~empty) and score[gref&positive].mean()>=baseline[gref&positive].mean()-1e-12);rows.append(dict(C=strength,threshold=float(threshold),eligible=ok,negative_accuracy=float(rejection[gref&z].mean()),positive_iou=float(score[gref&positive].mean()),positive_empty=int(rejection[positive].sum())))
best=max([r for r in rows if r['eligible']],key=lambda r:(r['negative_accuracy'],r['threshold'],-r['C']));path=O/'customB.pkl';path.write_bytes(pickle.dumps(dict(model=models[best['C']],threshold=best['threshold'],dim=x.shape[1])));result=dict(selected=best,checkpoint=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),validation_candidates=rows,features=x.shape[1],positive_class_weight=4,absent_class_weight=1,test_used=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());assert not (O/'customB_lock.json').exists();(O/'customB_lock.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='validation_candidates'},indent=2))
