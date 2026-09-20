"""Lock a fair training-free semantic control before fresh confirmation inference."""
import hashlib,json,platform,time
from pathlib import Path
import numpy as np
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915';p=D/'controls_lock.json';assert not p.exists()
rows=json.loads((D/'features_labels.json').read_text())['rows'];split=json.loads((D/'split.json').read_text());rr=[r for r in rows if r['key'] in split['validation']];pos=np.array([r['positive'] for r in rr]);base=np.array([r['scores'][0] for r in rr]);baseline=float(base[pos].mean());trials=[]
for threshold in [.01,.025,.05,.075,.1,.15,.2,.25,.3,.4,.5,.6,.7,.8,.9]:
    reject=np.array([r['features']['presence_probability']<threshold for r in rr]);scores=np.array([r['scores'][5 if q else 0] for r,q in zip(rr,reject)]);positive=float(scores[pos].mean());negative=float(scores[~pos].mean());trials.append(dict(threshold=threshold,positive_iou=positive,no_target_accuracy=negative,balanced=(positive+negative)/2,lisa_fraction=float((~reject).mean()),warm_proxy_seconds=4.+13.7*float((~reject).mean())))
eligible=[t for t in trials if t['positive_iou']>=baseline-.01];chosen=max(eligible,key=lambda t:(t['balanced'],t['positive_iou'],-t['threshold']))
record=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),presence_only=chosen,trials=trials,parent_lock_sha256=hashlib.sha256((D/'router_lock.json').read_bytes()).hexdigest(),cost_correction='Original geometry-only control needs no Qwen presence: overhead 1 s, not 5 s. Standalone LISA proxy 13.7 s has no routing overhead. This constant correction does not change selected geometry rule.',all_costs_proxies=True)
p.write_text(json.dumps(record,indent=2));print(json.dumps(chosen,indent=2))
