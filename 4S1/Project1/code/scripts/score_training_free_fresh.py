"""Score frozen training-free methods on the newly selected 60-image subset."""
import hashlib,json,platform,re
from pathlib import Path
import numpy as np
from PIL import Image
from pycocotools.coco import COCO
from proposal_agreement import fill
if platform.node()!='cenara70hx':raise SystemExit('Remote only')
R=Path('results');F=R/'training_free_fresh_20260914';G=R/'global_local_fresh_20260914';OUT=F/'scores'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
def mask(p):return np.asarray(Image.open(p))>0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(F/'manifest.json');items=manifest['items'];lock=read(F/'selection_lock.json')
assert len(items)==60 and len({i['image_sha256'] for i in items})==60
assert not {i['image_id'] for i in items}&set(lock['excluded_image_ids'])
assert all(i['official_split']=='testA' and sha(Path(i['image']))==i['image_sha256'] for i in items)
# Verify fresh runs applied exactly the development-selected scalar rules.
assert read(G/'applied_lock.json')==read(R/'global_local_dev_20260914/method_lock.json')
assert read(F/'agreement/applied_lock.json')==read(R/'agreement_dev_20260914/method_lock.json')
coco=COCO('/home/osta/lisa-eval/dataset/grefcoco/instances.json');person=next(k for k,v in coco.cats.items() if v['name']=='person')
(F/'fill_holes/masks').mkdir(parents=True,exist_ok=True)
for i in items:
    n=f'{i["item_id"]}__{i["prompt_id"]}.png';Image.fromarray(fill(mask(F/'p1_masks'/n)).astype('uint8')*255).save(F/'fill_holes/masks'/n)
variants={'LISA':F/'p1_masks','LISA_fill_holes':F/'fill_holes/masks','LISA_proposal_agreement':F/'agreement/masks','CLIP_global_local_selected':G/'selected/masks','YOLO_World_SAM':F/'yolo/p3_expression/masks','ZoomNeXt_vision_only':F/'zoom/masks'}
lisa_rows={r['key']:r for r in [json.loads(s) for s in (F/'p1_rows.jsonl').read_text().splitlines() if s]};allrows=[];summary={}
for method,folder in variants.items():
    rr=[]
    for i in items:
        n=f'{i["item_id"]}__{i["prompt_id"]}.png';p=mask(folder/n);g=mask(Path(i['ground_truth']));assert p.shape==g.shape
        valid=True
        if method.startswith('LISA'):
            lr=lisa_rows[i['key']];answer=lr['answer'].split('ASSISTANT:')[-1].lower()
            valid=bool(lr['emitted_seg']) or bool(re.search(r'\bno (?:matching )?(?:person|people|man|woman|one)\b|not (?:present|visible)|\bnone\b',answer))
        inter=int((p&g).sum());union=int((p|g).sum());iou=inter/union if union else 1.
        targethit=0;targettotal=0;distractorhit=0;distractortotal=0
        for ann in coco.imgToAnns[i['image_id']]:
            if ann['category_id']!=person or ann.get('iscrowd',0):continue
            personmask=coco.annToMask(ann)>0;hit=bool((p&personmask).sum()/max(1,personmask.sum())>=.5) and valid
            if ann['id'] in i['target_ann_ids']:targettotal+=1;targethit+=hit
            else:distractortotal+=1;distractorhit+=hit
        rr.append(dict(key=i['key'],image_id=i['image_id'],variant=method,expression=i['expression'],case_type=i['case_type'],positive=bool(g.any()),iou=iou if valid else 0.,mask_iou=iou,response_valid=valid,intersection=inter,union=union,predicted_pixels=int(p.sum()),target_hit=targethit,target_total=targettotal,distractor_hit=distractorhit,distractor_total=distractortotal))
    summary[method]={}
    for group in ['all','positive','no_target','single_in_crowd','multi_target']:
        sub=[r for r in rr if group=='all' or group=='positive' and r['positive'] or r['case_type']==group]
        summary[method][group]=dict(n=len(sub),mean_iou=float(np.mean([r['iou'] for r in sub])),cumulative_iou=sum(r['intersection'] for r in sub)/max(1,sum(r['union'] for r in sub)),no_match_accuracy=float(np.mean([r['predicted_pixels']==0 and r['response_valid'] for r in sub])) if group=='no_target' else None,invalid_response_rate=float(np.mean([not r['response_valid'] for r in sub])),target_coverage_recall=sum(r['target_hit'] for r in sub)/max(1,sum(r['target_total'] for r in sub)),distractor_coverage_rate=sum(r['distractor_hit'] for r in sub)/max(1,sum(r['distractor_total'] for r in sub)))
    allrows+=rr
base={r['key']:r for r in allrows if r['variant']=='LISA'};paired={};rng=np.random.default_rng(2026091402)
for method in variants:
    if method=='LISA':continue
    rows=[r for r in allrows if r['variant']==method and r['positive']];deltas=np.array([r['iou']-base[r['key']]['iou'] for r in rows]);boots=np.mean(rng.choice(deltas,size=(5000,len(deltas)),replace=True),axis=1)
    paired[method]=dict(positive_mean_delta=float(deltas.mean()),bootstrap_95ci=np.quantile(boots,[.025,.975]).tolist(),n_positive_images=len(deltas),improved=int((deltas>1e-9).sum()),worse=int((deltas < -1e-9).sum()),tied=int((abs(deltas)<=1e-9).sum()),replicates=5000)
write(OUT/'comparison.json',summary);write(OUT/'per_expression.json',allrows);write(OUT/'paired.json',paired)
write(OUT/'audit.json',dict(status='passed',host=platform.node(),n_unique_images=60,excluded_historical_ids=len(lock['excluded_image_ids']),official_split='testA',image_hashes_checked=True,development_locks_match=True,weights_trained=False,coverage_metric='A GT person is covered when >=50% of its visible mask is predicted. This is not one-to-one instance matching.',script_sha256=sha(Path(__file__)),manifest_sha256=sha(F/'manifest.json'),method_locks={'clip':sha(R/'global_local_dev_20260914/method_lock.json'),'agreement':sha(R/'agreement_dev_20260914/method_lock.json')}))
print(json.dumps(dict(summary=summary,paired=paired),indent=2))
