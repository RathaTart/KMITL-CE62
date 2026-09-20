"""Train small CoHD verifier using frozen features; never reads fresh test data."""
import json,platform,hashlib,time,pickle
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_upgrade_20260915'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dataset(folder,manifest):
 items=json.loads(manifest.read_text())['items']; by={r['key']:r for r in map(json.loads,(folder/'rows.jsonl').read_text().splitlines())}
 assert len(by)==len(items)
 x=[];y=[];raw=[];base=[]
 for i in items:
  r=by[i['key']];x.append(np.load(r['features']));y.append(i['target_count']==0)
  g=np.asarray(Image.open(i['ground_truth']))>0;m=np.asarray(Image.open(r['raw_mask']))>0
  assert g.shape==m.shape
  score=float((g&m).sum()/max(1,(g|m).sum()))
  raw.append(score);base.append(score*(not r['no_target']) if g.any() else float(r['no_target'] or not m.any()))
 return np.asarray(x),np.asarray(y),np.asarray(raw),np.asarray(base),items
fitman=C/'results/router_dev_20260915/manifest.json';valman=C/'results/router_confirm_20260915/manifest.json'
x,y,raw,b,fi=dataset(O/'fit',fitman);v,z,vr,vb,vi=dataset(O/'validation',valman)
assert not {i['image_id'] for i in fi}&{i['image_id'] for i in vi}
basepos=vb[~z].mean();baseneg=vb[z].mean()
def metrics(p):
 vals=vr*(~p);pos=float(vals[~z].mean());neg=float(p[z].mean());return dict(positive_iou=pos,no_target_accuracy=neg,balanced=(pos+neg)/2,positive_rejected=int(p[~z].sum()))
models={};candidates=[]
# Fixed family: threshold-only control and regularized linear verifiers.
probs={'threshold':v[:,1]/(v[:,0]+v[:,1]+1e-12)}
summary_dim=x.shape[1]-256
for features,dim in [('summary',summary_dim),('embedding',x.shape[1])]:
 for strength in [.01,.1,1.]:
  name=f'{features}_C{strength}'
  model=make_pipeline(StandardScaler(),LogisticRegression(C=strength,class_weight='balanced',max_iter=2000,random_state=20260915))
  model.fit(x[:,:dim],y);models[name]=(model,dim);probs[name]=model.predict_proba(v[:,:dim])[:,1]
for name,prob in probs.items():
 for threshold in np.linspace(.05,.95,91):
  m=metrics(prob>=threshold);candidates.append(dict(name=name,threshold=float(threshold),eligible=bool(m['positive_iou']>=basepos-.01),**m))
eligible=[r for r in candidates if r['eligible']]
best=max(eligible,key=lambda r:(r['balanced'],-r['positive_rejected'],r['threshold']))
control=max([r for r in eligible if r['name']=='threshold'],key=lambda r:r['balanced'])
learned=max([r for r in eligible if r['name']!='threshold'],key=lambda r:r['balanced'])
# Freeze one primary winner, retain threshold and best learned as disclosed controls.
selected={n:r for n,r in [('primary',best),('threshold_control',control),('learned_control',learned)]}
for tag,row in selected.items():
 if row['name']!='threshold':
  model,dim=models[row['name']];p=O/(tag+'.pkl');p.write_bytes(pickle.dumps(dict(model=model,dim=dim,threshold=row['threshold'])));row['checkpoint']=str(p);row['sha256']=digest(p)
lock=dict(selected=selected,fit_images=len(fi),validation_images=len(vi),feature_dim=x.shape[1],summary_dim=summary_dim,baseline_validation=dict(positive_iou=float(basepos),no_target_accuracy=float(baseneg)),candidates=candidates,fit_manifest_sha256=digest(fitman),validation_manifest_sha256=digest(valman),script_sha256=digest(Path(__file__)),test_read=False,selection='Max validation balanced score subject to <=1pp positive IoU loss; 6 linear verifiers and threshold-only, each 91 thresholds. No refitting after validation.')
p=O/'method_lock.json';assert not p.exists();p.write_text(json.dumps(lock,indent=2));print(json.dumps({k:v for k,v in lock.items() if k!='candidates'},indent=2))

