"""Matched no-Zoom ablation, fixed primary hyperparameters and threshold."""
import hashlib,json,platform,time
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import ExtraTreesRegressor
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915';lock=json.loads((D/'router_lock.json').read_text());assert lock['primary']['model']=='extra_5_15'
data=json.loads((D/'features_labels.json').read_text());rows=data['rows'];split=json.loads((D/'split.json').read_text());names=[n for n in data['feature_names'] if 'zoom' not in n and n!='area_ratio'];X=np.array([[r['features'][n] for n in names] for r in rows]);s=np.array([r['scores'] for r in rows]);fit=[j for j,r in enumerate(rows) if r['key'] in split['fit']]
m=ExtraTreesRegressor(n_estimators=120,max_depth=5,min_samples_leaf=15,random_state=2026091507,n_jobs=4).fit(X[fit],s[fit,1:]-s[fit,[0]][:,None]);p=D/'models/no_zoom.joblib';joblib.dump(m,p)
record=dict(feature_names=names,model_path=str(p),model_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),margin=lock['primary']['margin'],bonus=lock['primary']['bonus'],parent_lock_sha256=hashlib.sha256((D/'router_lock.json').read_bytes()).hexdigest(),created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),scope='Exploratory ablation; primary hyperparameters unchanged, no validation retuning')
(D/'ablation_lock.json').write_text(json.dumps(record,indent=2))
print('No-Zoom ablation locked',len(names))
