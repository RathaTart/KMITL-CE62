"""Remote development audit and training-free router sweep."""
import hashlib,itertools,json,platform
from pathlib import Path
import numpy as np
from PIL import Image
from router_features import features,action_mask,training_free_action,ACTIONS
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915'
def read(p):return json.loads(p.read_text())
items=read(D/'manifest.json')['items'];split=read(D/'split.json');cache={};rows=[]
for i in items:
    source=i['yolo_boxes']
    if source not in cache:cache[source]={r['key']:r for r in [json.loads(s) for s in Path(source).read_text().splitlines()]}
    f=features(i,cache[source][i['key']]);l=np.asarray(Image.open(i['lisa_mask']))>0;y=np.asarray(Image.open(i['yolo_mask']))>0;z=np.asarray(Image.open(i['zoom_mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0
    parent=Path(i['lisa_mask']).parent.parent
    if str(parent) not in cache:cache[str(parent)]={r['key']:r for r in [json.loads(s) for s in (parent/'p1_rows.jsonl').read_text().splitlines()]}
    lr=cache[str(parent)][i['key']];valid=lr['emitted_seg'] or any(x in lr['answer'].split('ASSISTANT:')[-1].lower() for x in ['no person','no people','no matching','not present','not visible','none'])
    scores=[]
    for action in range(len(ACTIONS)):
        m=action_mask(action,l,y,z);inter=int((m&g).sum());union=int((m|g).sum());scores.append((inter/union if union else 1.) if action!=0 or valid else 0.)
    rows.append(dict(key=i['key'],positive=bool(g.any()),case_type=i['case_type'],features=f,scores=scores))
(D/'features_labels.json').write_text(json.dumps(dict(feature_names=list(rows[0]['features']),actions=ACTIONS,rows=rows,feature_scope='Text, YOLO boxes, Zoom maps and frozen Qwen presence; no SAM or LISA inputs',zoom_caveat='Per-image normalized saliency ambiguity is not calibrated uncertainty'),indent=2))

def summary(actions,indices):
    rr=[rows[j] for j in indices];ss=np.array([rows[j]['scores'][actions[j]] for j in indices]);pos=np.array([r['positive'] for r in rr]);a=np.array([actions[j] for j in indices]);positive=float(ss[pos].mean());negative=float(ss[~pos].mean());fallback=float((a==0).mean());sam=float(np.isin(a,[1,3,4]).mean())
    return dict(n=len(rr),positive_iou=positive,no_target_accuracy=negative,balanced=(positive+negative)/2,overall=float(ss.mean()),lisa_fraction=fallback,sam_fraction=sam,warm_proxy_seconds=5.+13.7*fallback+5.0*sam)
indices={k:[j for j,r in enumerate(rows) if r['key'] in split[k]] for k in ['fit','validation']};baselines={k:summary([0]*len(rows),v) for k,v in indices.items()};oracle={k:summary([int(np.argmax(r['scores'])) for r in rows],v) for k,v in indices.items()}
configs=[]
for ambiguity,components,simple in itertools.product([.01,.025,.05,.1,.2,.4],[1,2,4,12],[False,True]):configs.append(dict(family='zoom',ambiguity=ambiguity,components=components,simple=simple,action=2))
for agreement,score,boxes,words,simple,empty in itertools.product([.1,.3,.5,.7,.9],[0.,.2,.4],[1,3,12],[5,100],[False,True],[False,True]):configs.append(dict(family='agreement',agreement=agreement,score=score,boxes=boxes,words=words,simple=simple,empty=empty,action=1))
trials=[]
for cfg in configs:
    aa=[training_free_action(r['features'],cfg) for r in rows];trials.append(dict(config=cfg,fit=summary(aa,indices['fit']),validation=summary(aa,indices['validation'])))
b=baselines['validation'];eligible=[t for t in trials if t['validation']['positive_iou']>=b['positive_iou']-.01 and t['validation']['balanced']>=b['balanced'] and t['validation']['warm_proxy_seconds']<=13.7*.8]
chosen=max(eligible,key=lambda t:(t['validation']['balanced'],-t['validation']['warm_proxy_seconds'])) if eligible else None
output=dict(baselines=baselines,oracle=oracle,n_trials=len(trials),chosen=chosen,training_free_joint_goal_met=bool(chosen and chosen['validation']['positive_iou']>=b['positive_iou']+.01),cost_note='Warm stage-cost proxy only: 1 s YOLO+Zoom, 5 s SAM, 13.7 s cached LISA; measure actual runtime separately',trials=trials)
(D/'training_free_sweep.json').write_text(json.dumps(output,indent=2));print(json.dumps({k:v for k,v in output.items() if k!='trials'},indent=2))
