"""Offline GT-only candidate ceiling diagnostic; never changes predictions."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image
if platform.node()!='cenara70hx':raise SystemExit('Remote only')
F=Path('results/training_free_fresh_20260914');G=Path('results/global_local_fresh_20260914')
items=json.loads((F/'manifest.json').read_text())['items'];rows=[]
def mask(p):return np.asarray(Image.open(p))>0
def iou(a,b):return float((a&b).sum()/max(1,(a|b).sum()))
def box_iou(a,b):
    x=max(0,min(a[2],b[2])-max(a[0],b[0]));y=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=x*y
    return float(inter/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter))
for i in items:
    stem=i['item_id']+'__'+i['prompt_id'];data=np.load(G/'proposals'/(stem+'.npz'));ms=data['masks'];boxes=data['boxes']
    selected=mask(G/'selected/masks'/(stem+'.png'));lisa=mask(F/'p1_masks'/(stem+'.png'))
    for targetpath in i['ground_truth_instances']:
        gt=mask(targetpath);yy,xx=np.where(gt);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];best_mask=max([iou(m,gt) for m in ms],default=0.);best_box=max([box_iou(b,box) for b in boxes],default=0.)
        rows.append(dict(key=i['key'],expression=i['expression'],target=Path(targetpath).name,n_proposals=len(ms),gt_area=int(gt.sum()),gt_height=box[3]-box[1],best_candidate_mask_iou=best_mask,best_candidate_box_iou_with_visible_gt_box=best_box,clip_selected_target_coverage=float((selected&gt).sum()/max(1,gt.sum())),lisa_target_coverage=float((lisa&gt).sum()/max(1,gt.sum()))))
summary=dict(n_targets=len(rows),n_positive_images=sum(bool(i['target_count']) for i in items),targets_with_candidate_mask_iou_ge_0_5=sum(r['best_candidate_mask_iou']>=.5 for r in rows),targets_with_candidate_box_iou_ge_0_5=sum(r['best_candidate_box_iou_with_visible_gt_box']>=.5 for r in rows),targets_with_candidate_mask_but_clip_coverage_below_0_5=sum(r['best_candidate_mask_iou']>=.5 and r['clip_selected_target_coverage']<.5 for r in rows),mean_best_candidate_mask_iou=float(np.mean([r['best_candidate_mask_iou'] for r in rows])),warning='GT-only diagnostic upper bound. Independent best matches can reuse a candidate, so this is not one-to-one recall/AP. Visible-GT-box IoU is diagnostic, not native detector AP. No prediction or method lock is changed.')
out=F/'scores';(out/'candidate_diagnostic.json').write_text(json.dumps(dict(summary=summary,targets=rows),indent=2));print(json.dumps(summary,indent=2))
