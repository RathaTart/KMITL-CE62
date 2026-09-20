"""Remote confirmation scores and measured model-stage cost accounting."""
import hashlib,json,platform,time
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');F=R/'results/router_confirm_20260915';D=R/'results/router_dev_20260915';O=F/'scores';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def lines(p):return {r['key']:r for r in [json.loads(s) for s in p.read_text().splitlines()]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock=read(D/'router_lock.json');manifest=read(F/'manifest.json');items=manifest['items'];assert sha(F/'manifest.json')==lock['confirmation_manifest_sha256'];assert len(items)==90 and len({i['image_id'] for i in items})==90
excluded=set(read(F/'selection_lock.json')['excluded_image_ids']);assert all(i['image_id'] not in excluded and sha(Path(i['image']))==i['image_sha256'] for i in items)
assert not {i['image_id'] for i in items}&{i['image_id'] for i in read(D/'manifest.json')['items']}
audit=read(F/'prediction_audit.json');y=lines(F/'yolo/p3_expression/grounding_boxes.jsonl');sam=lines(F/'yolo/p3_expression/sam_timings.jsonl');l=lines(F/'p1_rows.jsonl');p=lines(F/'qwen_presence.jsonl');z={r['key']:r for r in read(F/'zoom/provenance.json')['rows']};im={i['key']:i for i in items};rows=[]
for r in audit:
    i=im[r['key']];pred=np.asarray(Image.open(r['mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0;assert sha(Path(r['mask']))==r['mask_sha256'];inter=int((pred&g).sum());union=int((pred|g).sum());score=(inter/union if union else 1.) if r['valid'] else 0.;key=r['key'];a=r['action_id'];method=r['method'];yt=y[key]['latency_s'];zt=z[key]['model_s'];pt=p[key]['results'][0]['seconds'];st=sam[key]['latency_s'];lt=l[key]['latency_s']
    if method=='LISA_cached':cost=lt
    elif method=='YOLO_SAM':cost=yt+st
    elif method=='ZoomNeXt':cost=zt
    else:
        cost=pt if method=='TF_presence' else yt+zt if method=='TF_Zoom' else yt+pt+(zt if method!='Learned_no_zoom' or a in [2,3,4] else 0.)
        cost+=lt if a==0 else st if a in [1,3,4] else 0.
    rows.append(dict(key=key,method=method,action=r['action'],iou=score,positive=bool(g.any()),case_type=i['case_type'],valid=r['valid'],predicted_pixels=int(pred.sum()),intersection=inter if r['valid'] else 0,union=union,model_stage_seconds=float(cost)))
methods=list(dict.fromkeys(r['method'] for r in rows));summary={}
for method in methods:
    rr=[r for r in rows if r['method']==method];s={}
    for group in ['all','positive','no_target','single_in_crowd','multi_target']:
        sub=[r for r in rr if group=='all' or group=='positive' and r['positive'] or r['case_type']==group];s[group]=dict(n=len(sub),mean_iou=float(np.mean([r['iou'] for r in sub])),cumulative_iou=sum(r['intersection'] for r in sub)/max(1,sum(r['union'] for r in sub)),no_match_accuracy=float(np.mean([r['valid'] and r['predicted_pixels']==0 for r in sub])) if group=='no_target' else None)
    s.update(balanced_score=(s['positive']['mean_iou']+s['no_target']['no_match_accuracy'])/2,mean_model_stage_seconds=float(np.mean([r['model_stage_seconds'] for r in rr])),lisa_calls=sum(r['action']=='LISA' for r in rr),action_counts={a:sum(r['action']==a for r in rr) for a in set(r['action'] for r in rr)});summary[method]=s
index={m:{r['key']:r for r in rows if r['method']==m} for m in methods};rng=np.random.default_rng(2026091507);paired={};poskeys=[i['key'] for i in items if i['case_type']!='no_target'];negkeys=[i['key'] for i in items if i['case_type']=='no_target']
for method in methods:
    if method=='LISA_cached':continue
    delta=np.array([index[method][k]['iou']-index['LISA_cached'][k]['iou'] for k in poskeys]);neg=np.array([index[method][k]['iou']-index['LISA_cached'][k]['iou'] for k in negkeys]);pd=rng.choice(delta,(10000,len(delta))).mean(1);nd=rng.choice(neg,(10000,len(neg))).mean(1);balanced=(pd+nd)/2;timed=np.array([index['LISA_cached'][i['key']]['model_stage_seconds']-index[method][i['key']]['model_stage_seconds'] for i in items]);td=rng.choice(timed,(10000,len(timed))).mean(1)
    paired[method]=dict(positive_delta=float(delta.mean()),positive_95ci=np.quantile(pd,[.025,.975]).tolist(),positive_adjusted_98_333ci=np.quantile(pd,[.05/6,1-.05/6]).tolist(),balanced_delta=float((delta.mean()+neg.mean())/2),balanced_95ci=np.quantile(balanced,[.025,.975]).tolist(),balanced_adjusted_98_333ci=np.quantile(balanced,[.05/6,1-.05/6]).tolist(),model_stage_seconds_saved=float(timed.mean()),stage_time_95ci=np.quantile(td,[.025,.975]).tolist(),stage_time_adjusted_98_333ci=np.quantile(td,[.05/6,1-.05/6]).tolist(),primary=method=='Learned_primary')
for name,obj in [('comparison.json',summary),('paired.json',paired),('per_expression.json',rows)]: (O/name).write_text(json.dumps(obj,indent=2))
(O/'audit.json').write_text(json.dumps(dict(status='passed',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),unique_images=90,positive=60,no_target=30,image_hashes_verified=True,development_disjoint=True,method_lock_sha256=sha(D/'router_lock.json'),controls_lock_sha256=sha(D/'controls_lock.json'),ablation_lock_sha256=sha(D/'ablation_lock.json'),timing_scope='Sum of measured model-stage times under each route; excludes model loading, interprocess overhead, gate feature extraction and scheduling. Not end-to-end latency or measured cascade throughput.',uncertainty='Three primary comparisons against LISA: positive IoU, balanced score, model-stage time. Bonferroni 98.333% intervals; other methods exploratory.',foundation_weights_updated=False,small_router_trained=True,pretraining_overlap_possible=True),indent=2))
print(json.dumps(dict(summary={m:{k:v for k,v in s.items() if k in ['balanced_score','mean_model_stage_seconds','lisa_calls','action_counts']}|dict(positive=s['positive']['mean_iou'],negative=s['no_target']['no_match_accuracy']) for m,s in summary.items()},primary=paired['Learned_primary']),indent=2))
