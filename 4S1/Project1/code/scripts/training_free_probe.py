"""Training-free mask postprocessing. No optimizer or learned weights.

Select a fixed rule on reused development data, then evaluate that one rule on
the previously inspected 120-expression set. This is exploratory, not fresh test.
"""
import json,platform,hashlib,time
from pathlib import Path
import cv2,numpy as np
from PIL import Image
if platform.node()!='cenara70hx':raise SystemExit('Remote experiments only')
R=Path('results');OUT=R/'training_free_20260914';OUT.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
def name(i):return f'{i["item_id"]}__{i["prompt_id"]}.png'
def mask(p):return np.asarray(Image.open(p))>0
def apply(m,rule,i,dev):
    u=m.astype('uint8')
    if rule=='identity':return m
    if rule.startswith('close'):
        k=int(rule[-1]);return cv2.morphologyEx(u,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k)))>0
    if rule=='median3':return cv2.medianBlur(u,3)>0
    if rule.startswith('fill'):
        count,labels,stats,_=cv2.connectedComponentsWithStats(1-u,8)
        border=set(np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]])))
        out=m.copy()
        for j in range(1,count):
            if j not in border and (rule=='fill_all' or stats[j,cv2.CC_STAT_AREA]<=max(16,int(m.sum()*.005))):out[labels==j]=True
        return out
    if rule=='agreement_vote':
        ref=R/('lisa_dense_refinement_20260914' if dev else 'upgrade_test_20260914')/'refined'/name(i)
        y=R/('attribute_pilot_20260914/yolo/p3_expression/masks' if dev else 'upgrade_test_20260914/yolo/p3_expression/masks')/name(i)
        z=R/('lisa_refinement_20260914/zoom/masks' if dev else 'upgrade_test_20260914/zoom/masks')/name(i)
        return (u*2+mask(ref).astype('uint8')+mask(y).astype('uint8')+mask(z).astype('uint8'))>=3
    raise ValueError(rule)

def run(source,tag,rules):
    m=read(source/'manifest.json');rows=[];summary={}
    for rule in rules:
        folder=OUT/tag/rule/'masks';folder.mkdir(parents=True)
        for i in m['items']:
            pred=mask(source/'p1_masks'/name(i));start=time.perf_counter();pred=apply(pred,rule,i,tag=='development');elapsed=time.perf_counter()-start
            Image.fromarray(pred.astype('uint8')*255).save(folder/name(i))
            # GT is used after producing and saving the prediction, for scoring only.
            gt=mask(i['ground_truth']);inter=int((pred&gt).sum());union=int((pred|gt).sum())
            rows.append(dict(key=i['key'],image=Path(i['image']).name,variant=rule,positive=bool(gt.any()),case_type=i['case_type'],iou=inter/union if union else 1.,intersection=inter,union=union,predicted_pixels=int(pred.sum()),postprocess_s=elapsed))
        summary[rule]={}
        for group in ['all','positive','no_target','single_in_crowd','multi_target']:
            rr=[r for r in rows if r['variant']==rule and (group=='all' or group=='positive' and r['positive'] or r['case_type']==group)]
            if rr:summary[rule][group]=dict(n=len(rr),mean_iou=float(np.mean([r['iou'] for r in rr])),cumulative_iou=sum(r['intersection'] for r in rr)/max(1,sum(r['union'] for r in rr)),no_match_accuracy=float(np.mean([r['predicted_pixels']==0 for r in rr])) if group=='no_target' else None)
    write(OUT/tag/'comparison.json',summary);write(OUT/tag/'per_expression.json',rows);write(OUT/tag/'manifest.json',m)
    return summary,rows

rules=['identity','fill_small','fill_all','close3','close5','median3','agreement_vote']
write(OUT/'protocol.json',dict(training=False,optimizer=None,weights_modified=False,candidates=rules,selection='highest development positive mean IoU, including identity fallback',small_hole_limit='max(16, 0.005 * LISA mask area) pixels',ensemble='2*LISA + SAM + YOLO-SAM + Zoom binary masks >= 3',evaluation_status='120 previously inspected expressions; exploratory repeated evaluation, NOT untouched test',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
summary,_=run(R/'grefcoco_pilot_p1_p2','development',rules)
chosen=max(rules,key=lambda r:summary[r]['positive']['mean_iou'])
write(OUT/'selection_lock.json',dict(chosen=chosen,development_scores={k:v['positive']['mean_iou'] for k,v in summary.items()},note='Saved before evaluating the selected rule on 120 images. Those images were already inspected in prior research.'))
summary,rows=run(R/'upgrade_reserved_20260914','reused_evaluation',list(dict.fromkeys(['identity',chosen])))
base={r['key']:r for r in rows if r['variant']=='identity'};groups={}
for r in rows:
    if r['variant']==chosen and r['positive']:groups.setdefault(r['image'],[]).append(r['iou']-base[r['key']]['iou'])
groups=list(groups.values());rng=np.random.default_rng(20260914);samples=[]
for _ in range(5000):
    indices=rng.integers(0,len(groups),size=len(groups));samples.append(float(np.mean([v for j in indices for v in groups[j]])))
paired=dict(chosen=chosen,positive_mean_delta=float(np.mean([v for g in groups for v in g])),bootstrap_95ci=np.quantile(samples,[.025,.975]).tolist(),note='Descriptive interval on previously inspected data; not independent confirmation of a newly selected hypothesis.')
write(OUT/'reused_evaluation/paired.json',paired)
print(json.dumps(dict(selection=read(OUT/'selection_lock.json'),evaluation=summary,paired=paired),indent=2))
