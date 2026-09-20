"""Score the locked 180-image evaluation remotely, with paired uncertainty."""
import hashlib,json,platform,re,time
from pathlib import Path
import numpy as np
from PIL import Image
from pycocotools.coco import COCO
assert platform.node()=='cenara70hx'
ROOT=Path('/home/osta/lisa-eval/code');F=ROOT/'results/training_free_extended_20260915';T=ROOT/'results/extended_test_20260915';D=ROOT/'results/extended_dev_20260915';OUT=T/'scores';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def mask(p):return np.asarray(Image.open(p))>0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(F/'manifest.json');items=manifest['items'];selection=read(F/'selection_lock.json');lock=read(D/'method_lock.json');assert read(T/'applied_method_lock.json')==lock
assert sha(F/'manifest.json')==lock['fresh_manifest_sha256']
assert len(items)==180 and len({i['image_id'] for i in items})==180 and len({i['image_sha256'] for i in items})==180
assert not {i['image_id'] for i in items}&set(selection['excluded_image_ids'])
assert all(i['official_split']=='testA' and sha(Path(i['image']))==i['image_sha256'] for i in items)
assert not {Path(i['image']).name for i in items}&{Path(i['image']).name for i in read(D/'manifest.json')['items']}
first=OUT/'first_scoring_started.json'
if not first.exists():first.write_text(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),method_lock_sha256=sha(D/'method_lock.json')),indent=2))
else:assert read(first)['method_lock_sha256']==sha(D/'method_lock.json')
variants={'LISA':F/'p1_masks','YOLO_World_SAM':F/'yolo/p3_expression/masks','ZoomNeXt_vision_only':F/'zoom/masks'}
variants.update({method:T/'predictions'/method/'masks' for method in lock['variants']})
pa={(r['method'],r['key']):r for r in read(T/'prediction_audit.json')};lr={r['key']:r for r in [json.loads(s) for s in (F/'p1_rows.jsonl').read_text().splitlines()]}
coco=COCO('/home/osta/lisa-eval/dataset/grefcoco/instances.json');person=next(k for k,v in coco.cats.items() if v['name']=='person');allrows=[]
for i in items:
    name=i['item_id']+'__'+i['prompt_id']+'.png';g=mask(Path(i['ground_truth']));gtpersons=[(a['id'] in i['target_ann_ids'],coco.annToMask(a)>0) for a in coco.imgToAnns[i['image_id']] if a['category_id']==person and not a.get('iscrowd',0)]
    for method,folder in variants.items():
        p=mask(folder/name);assert p.shape==g.shape,(method,i['key']);valid=True
        if method=='LISA':
            r=lr[i['key']];answer=r['answer'].split('ASSISTANT:')[-1].lower();valid=bool(r['emitted_seg']) or bool(re.search(r'\bno (?:matching )?(?:person|people|man|woman|one)\b|not (?:present|visible)|\bnone\b',answer))
        elif method in lock['variants']:
            audit=pa[method,i['key']];valid=audit['valid'];assert sha(folder/name)==audit['mask_sha256']
        inter=int((p&g).sum());union=int((p|g).sum());targethit=targettotal=distractorhit=distractortotal=0
        for is_target,personmask in gtpersons:
            hit=bool((p&personmask).sum()/max(personmask.sum(),1)>=.5) and valid
            if is_target:targettotal+=1;targethit+=hit
            else:distractortotal+=1;distractorhit+=hit
        allrows.append(dict(key=i['key'],image_id=i['image_id'],variant=method,expression=i['expression'],case_type=i['case_type'],positive=bool(g.any()),iou=(inter/union if union else 1.) if valid else 0.,mask_iou=inter/union if union else 1.,response_valid=valid,intersection=inter if valid else 0,union=union,predicted_pixels=int(p.sum()),target_hit=targethit,target_total=targettotal,distractor_hit=distractorhit,distractor_total=distractortotal))
summary={}
for method in variants:
    rr=[r for r in allrows if r['variant']==method];summary[method]={}
    for group in ['all','positive','no_target','single_in_crowd','multi_target']:
        sub=[r for r in rr if group=='all' or group=='positive' and r['positive'] or r['case_type']==group]
        summary[method][group]=dict(n=len(sub),mean_iou=float(np.mean([r['iou'] for r in sub])),cumulative_iou=sum(r['intersection'] for r in sub)/max(1,sum(r['union'] for r in sub)),no_match_accuracy=float(np.mean([r['predicted_pixels']==0 and r['response_valid'] for r in sub])) if group=='no_target' else None,empty_prediction_rate=float(np.mean([r['predicted_pixels']==0 for r in sub])),invalid_response_rate=float(np.mean([not r['response_valid'] for r in sub])),target_coverage_recall=sum(r['target_hit'] for r in sub)/max(1,sum(r['target_total'] for r in sub)),distractor_coverage_rate=sum(r['distractor_hit'] for r in sub)/max(1,sum(r['distractor_total'] for r in sub)))
    summary[method]['balanced_score']=(summary[method]['positive']['mean_iou']+summary[method]['no_target']['no_match_accuracy'])/2
index={method:{r['key']:r for r in allrows if r['variant']==method} for method in variants};rng=np.random.default_rng(2026091501);paired={};comparisons=[]
for method in variants:
    if method!='LISA':comparisons.append((method,'LISA','exploratory' if method!=lock['primary'] else 'primary'))
for baseline in ['YOLO_World_SAM','ZoomNeXt_vision_only']:comparisons.append((lock['primary'],baseline,'primary'))
for method,baseline,status in comparisons:
    pos=np.array([index[method][i['key']]['iou']-index[baseline][i['key']]['iou'] for i in items if i['case_type']!='no_target']);neg=np.array([index[method][i['key']]['iou']-index[baseline][i['key']]['iou'] for i in items if i['case_type']=='no_target'])
    pb=rng.choice(pos,size=(10000,len(pos)),replace=True).mean(1);nb=rng.choice(neg,size=(10000,len(neg)),replace=True).mean(1);balanced=(pb+nb)/2;overall=(len(pos)*pb+len(neg)*nb)/(len(pos)+len(neg));key=method+'__vs__'+baseline
    paired[key]=dict(status=status,positive_mean_delta=float(pos.mean()),positive_bootstrap_95ci=np.quantile(pb,[.025,.975]).tolist(),positive_bonferroni_99_167ci=np.quantile(pb,[.05/12,1-.05/12]).tolist(),balanced_mean_delta=float((pos.mean()+neg.mean())/2),balanced_bootstrap_95ci=np.quantile(balanced,[.025,.975]).tolist(),balanced_bonferroni_99_167ci=np.quantile(balanced,[.05/12,1-.05/12]).tolist(),overall_mean_delta=float((len(pos)*pos.mean()+len(neg)*neg.mean())/(len(pos)+len(neg))),overall_bootstrap_95ci=np.quantile(overall,[.025,.975]).tolist(),n_positive=len(pos),n_negative=len(neg),improved=int((pos>1e-9).sum()),worse=int((pos < -1e-9).sum()),tied=int((abs(pos)<=1e-9).sum()),replicates=10000)
for fn,value in [('comparison.json',summary),('per_expression.json',allrows),('paired.json',paired)]: (OUT/fn).write_text(json.dumps(value,indent=2))
(OUT/'audit.json').write_text(json.dumps(dict(status='passed',host=platform.node(),n_unique_images=180,n_positive=120,n_negative=60,excluded_historical_images=len(selection['excluded_image_ids']),all_image_hashes_checked=True,development_image_disjoint=True,source_manifest_unchanged=True,method_lock_sha256=sha(D/'method_lock.json'),manifest_sha256=sha(F/'manifest.json'),script_sha256=sha(Path(__file__)),weights_updated=False,primary=lock['primary'],coverage_metric='>=50% visible GT-person mask coverage; diagnostic only, not one-to-one instance matching',uncertainty='Stratified paired image bootstrap, 10000 draws. Bonferroni intervals cover six primary comparisons: positive IoU and balanced score against three baselines. Other methods are exploratory.',scope='Project-held-out COCO language-selection experiment; foundation-model pretraining overlap possible; no new CCTV generalization claim.'),indent=2))
print(json.dumps(dict(summary={m:dict(positive=s['positive']['mean_iou'],no_target=s['no_target']['no_match_accuracy'],overall=s['all']['mean_iou'],balanced=s['balanced_score']) for m,s in summary.items()},primary_comparisons={k:v for k,v in paired.items() if v['status']=='primary'}),indent=2))
