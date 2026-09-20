"""Fit small supervised routing layers; foundation model weights remain frozen."""
import hashlib,json,platform,time
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import ExtraTreesRegressor,RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915';M=D/'models';M.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
data=read(D/'features_labels.json');rows=data['rows'];names=data['feature_names'];X=np.array([[r['features'][n] for n in names] for r in rows]);scores=np.array([r['scores'] for r in rows]);Y=scores[:,1:]-scores[:,[0]];positive=np.array([r['positive'] for r in rows]);split=read(D/'split.json');fit=np.array([j for j,r in enumerate(rows) if r['key'] in split['fit']]);val=np.array([j for j,r in enumerate(rows) if r['key'] in split['validation']]);basepos=float(scores[val,0][positive[val]].mean());basebal=(basepos+float(scores[val,0][~positive[val]].mean()))/2
costs=np.array([0.,5.,0.,5.,5.,0.]);trials=[];models={}

def evaluate(a,ids):
    ss=scores[ids,a[ids]];pp=positive[ids];pos=float(ss[pp].mean());neg=float(ss[~pp].mean());fraction=float((a[ids]==0).mean());sam=float(np.isin(a[ids],[1,3,4]).mean());return dict(positive_iou=pos,no_target_accuracy=neg,balanced=(pos+neg)/2,lisa_fraction=fraction,sam_fraction=sam,warm_proxy_seconds=5.+13.7*fraction+5*sam,n=len(ids))

def choose(pred,margin,bonus):
    adjusted=pred+bonus*(13.7-costs[1:])/13.7;best=adjusted.argmax(1);accept=adjusted[np.arange(len(pred)),best]>=margin;return np.where(accept,best+1,0)

for kind in ['extra','forest','ridge']:
    settings=[(depth,leaf) for depth in [3,5,None] for leaf in [3,8,15]] if kind!='ridge' else [(a,0) for a in [.1,10.,100.]]
    for depth,leaf in settings:
        label=f'{kind}_{depth}_{leaf}'
        model=make_pipeline(StandardScaler(),Ridge(alpha=depth)) if kind=='ridge' else (ExtraTreesRegressor if kind=='extra' else RandomForestRegressor)(n_estimators=120,max_depth=depth,min_samples_leaf=leaf,random_state=2026091507,n_jobs=4)
        model.fit(X[fit],Y[fit]);models[label]=model;pred=model.predict(X)
        for margin in [-.1,-.05,0.,.025,.05,.1,.2,.3,.5,.75,1.0]:
            for bonus in [0.,.025,.05,.1]:
                a=choose(pred,margin,bonus);trials.append(dict(model=label,margin=margin,bonus=bonus,fit=evaluate(a,fit),validation=evaluate(a,val)))
        joblib.dump(model,M/(label+'.joblib'))

eligible=[t for t in trials if t['validation']['positive_iou']>=basepos-.01 and t['validation']['balanced']>=basebal and t['validation']['warm_proxy_seconds']<=13.7*.8]
quality=[t for t in trials if t['validation']['positive_iou']>=basepos-.01 and t['validation']['balanced']>=basebal]
primary=max(eligible,key=lambda t:(t['validation']['balanced'],t['validation']['positive_iou'],-t['validation']['warm_proxy_seconds'])) if eligible else max(quality,key=lambda t:(t['validation']['balanced'],t['validation']['positive_iou'],-t['validation']['warm_proxy_seconds'])) if quality else None
accuracy=max(trials,key=lambda t:(t['validation']['positive_iou'],t['validation']['balanced']))
tf=read(D/'training_free_sweep.json');tfq=[t for t in tf['trials'] if t['validation']['positive_iou']>=basepos-.01 and t['validation']['balanced']>=basebal];tfselected=min(tfq,key=lambda t:(t['validation']['warm_proxy_seconds'],-t['validation']['balanced'])) if tfq else dict(config=dict(family='agreement',agreement=2,score=2,boxes=0,words=0,action=1),validation=tf['baselines']['validation'])
result=dict(primary=primary,accuracy_secondary=accuracy,training_free=tfselected,n_trained_models=len(models),n_configurations=len(trials),joint_speed_quality_eligible=len(eligible),baseline_positive=basepos,baseline_balanced=basebal,trials=trials)
(D/'trained_sweep.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='trials'},indent=2))
assert primary is not None,'No acceptable trained router; report failure without inventing improvement'
lockpath=D/'router_lock.json';assert not lockpath.exists()
modelpath=M/(primary['model']+'.joblib');secondarypath=M/(accuracy['model']+'.joblib');manifest=R/'results/router_confirm_20260915/manifest.json';assert manifest.exists()
lock=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),primary=primary,accuracy_secondary=accuracy,training_free=tfselected,feature_names=names,actions=data['actions'],model_path=str(modelpath),model_sha256=hashlib.sha256(modelpath.read_bytes()).hexdigest(),secondary_model_path=str(secondarypath),secondary_model_sha256=hashlib.sha256(secondarypath.read_bytes()).hexdigest(),feature_sha256=hashlib.sha256((R/'scripts/router_features.py').read_bytes()).hexdigest(),fit_count=len(fit),validation_count=len(val),confirmation_count=90,confirmation_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),policy='Validation selection: positive IoU within 1 percentage point of LISA, balanced score >= LISA, proxy warm cost at least 20% lower if feasible; maximize balanced then positive IoU. If infeasible select highest balanced quality-eligible; no speed gain promised. Accuracy secondary maximizes validation positive IoU. No refitting on validation.',trained_layer_only=True,foundation_weights_updated=False,costs=[0.,5.,0.,5.,5.,0.])
lockpath.write_text(json.dumps(lock,indent=2))
