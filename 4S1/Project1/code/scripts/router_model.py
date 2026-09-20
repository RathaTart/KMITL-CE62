"""Shared locked decision logic; no ground truth or LISA outputs used by gate."""
import hashlib,json
from pathlib import Path
import joblib,numpy as np
from router_features import features,training_free_action
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915'
def read(p):return json.loads(p.read_text())
def load():
    lock=read(D/'router_lock.json');controls=read(D/'controls_lock.json');ablation=read(D/'ablation_lock.json');assert hashlib.sha256((R/'scripts/router_features.py').read_bytes()).hexdigest()==lock['feature_sha256']
    models={}
    for label,path,digest in [('learned',lock['model_path'],lock['model_sha256']),('accuracy',lock['secondary_model_path'],lock['secondary_model_sha256']),('no_zoom',ablation['model_path'],ablation['model_sha256'])]:
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest;models[label]=joblib.load(path)
    return lock,controls,ablation,models

def decide(f,loaded):
    lock,c,a,models=loaded;out={'TF_Zoom':training_free_action(f,lock['training_free']['config']),'TF_presence':5 if f['presence_probability']<c['presence_only']['threshold'] else 0}
    for key,label,cfg,names in [('Learned_primary','learned',lock['primary'],lock['feature_names']),('Learned_accuracy','accuracy',lock['accuracy_secondary'],lock['feature_names']),('Learned_no_zoom','no_zoom',a,a['feature_names'])]:
        pred=models[label].predict([[f[n] for n in names]])[0];adjusted=pred+cfg['bonus']*(13.7-np.array(lock['costs'][1:]))/13.7;best=int(adjusted.argmax());out[key]=best+1 if adjusted[best]>=cfg['margin'] else 0
    return out
