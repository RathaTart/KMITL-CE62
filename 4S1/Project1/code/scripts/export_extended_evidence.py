"""Package completed remote evidence for the existing local EN/TH portal."""
import json,platform,shutil,hashlib
from pathlib import Path
assert platform.node()=='cenara70hx'
ROOT=Path('/home/osta/lisa-eval/code');F=ROOT/'results/training_free_extended_20260915';T=ROOT/'results/extended_test_20260915';D=ROOT/'results/extended_dev_20260915';O=ROOT/'results/extended_public_20260915';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def copy(src,dest):
    dst=O/dest;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);return 'extended-assets/'+str(dest)
summary=read(T/'scores/comparison.json');paired=read(T/'scores/paired.json');lock=read(D/'method_lock.json');manifest=read(F/'manifest.json');rows={(r['variant'],r['key']):r for r in read(T/'scores/per_expression.json')};audits={(r['method'],r['key']):r for r in read(T/'prediction_audit.json')};items=[]
folders={'LISA':F/'p1_masks','YOLO_World_SAM':F/'yolo/p3_expression/masks','ZoomNeXt_vision_only':F/'zoom/masks'};folders.update({method:T/'predictions'/method/'masks' for method in lock['variants']})
for i in manifest['items']:
    stem=i['item_id']+'__'+i['prompt_id'];preds={}
    for method,folder in folders.items():
        r=rows[method,i['key']];preds[method]=dict(src=copy(folder/(stem+'.png'),f'masks/{method}/{stem}.png'),iou=r['iou'],response_valid=r['response_valid'],target_hit=r['target_hit'],target_total=r['target_total'],distractor_hit=r['distractor_hit'],distractor_total=r['distractor_total'],decisions=audits.get((method,i['key']),{}).get('decisions'))
    items.append(dict(key=i['key'],item_id=i['item_id'],image_id=i['image_id'],expression=i['expression'],case_type=i['case_type'],image=copy(Path(i['image']),f'images/{i["item_id"]}.jpg'),gt=copy(Path(i['ground_truth']),f'gt/{i["item_id"]}.png'),predictions=preds))
development={};total=0
for fn in ['geometry_sweep.json','custom_boundary_sweep.json','guided_sweep.json','clip_sweep.json','gate_sweep.json','candidate_sweep.json','composition_sweep.json']:
    data=read(D/fn);trials=data['trials'];total+=len(trials);best_positive=max(trials,key=lambda k:trials[k]['positive_iou']) if trials else None;best_overall=max(trials,key=lambda k:trials[k]['overall_iou']) if trials else None
    development[fn.removesuffix('.json')]=dict(n_configurations=len(trials),best_positive=best_positive,best_overall=best_overall,trials={k:{s:v for s,v in r.items() if s!='rows'} for k,r in trials.items()})
copy(D/'method_lock.json','method_lock.json');copy(F/'selection_lock.json','selection_lock.json')
for fn in ['comparison.json','paired.json','per_expression.json','audit.json']:copy(T/'scores'/fn,fn)
for fn in ['availability.json','environment_audit.json','shape_implementation_audit.json','candidate_matching_diagnostic.json','rexseek_quantization_audit.json','rexseek_loading.json','locked_dev_reproduction.json']:copy(D/fn,fn)
(O/'development.json').write_text(json.dumps(development,indent=2))
primary=lock['primary'];s=summary[primary];p=paired[primary+'__vs__LISA'];delta=p['positive_mean_delta']*100;lo,hi=[v*100 for v in p['positive_bootstrap_95ci']];positive_reliable=p['positive_bonferroni_99_167ci'][0]>0;balanced_reliable=p['balanced_bonferroni_99_167ci'][0]>0
note=dict(en=f'180 project-held-out testA images. Primary positive IoU difference vs LISA: {delta:+.2f} points (95% CI {lo:+.2f} to {hi:+.2f}). '+('The multiplicity-adjusted interval supports a positive-IoU improvement.' if positive_reliable else 'A reliable positive-IoU improvement is not established by the multiplicity-adjusted interval.')+' New to project evaluation does not mean absent from model pretraining; this does not establish CCTV generalization.',th=f'ภาพ testA ใหม่ต่อการประเมินของโครงการ 180 ภาพ วิธีหลักมี IoU เมื่อมีเป้าหมายต่างจาก LISA {delta:+.2f} จุด (95% CI {lo:+.2f} ถึง {hi:+.2f}) '+('ช่วงความเชื่อมั่นที่ปรับการเปรียบเทียบหลายครั้งสนับสนุนว่า IoU เป้าหมายจริงดีขึ้น' if positive_reliable else 'ช่วงความเชื่อมั่นที่ปรับการเปรียบเทียบหลายครั้งยังไม่ยืนยันว่า IoU เป้าหมายจริงดีขึ้น')+' ภาพใหม่ต่อโครงการไม่ได้หมายความว่าไม่เคยอยู่ในการฝึกโมเดล และยังไม่ใช่หลักฐานการใช้งานทั่วไปบน CCTV')
data=dict(items=items,summary=summary,paired=paired,note=note,primary=primary,method_lock=lock,download='extended-assets/comparison.json',intervals='extended-assets/paired.json',protocol='extended-assets/method_lock.json',development_download='extended-assets/development.json',development_summary={k:{f:v[f] for f in ['n_configurations','best_positive','best_overall']} for k,v in development.items()},n_development_configurations=total,headline=dict(positive_reliable=positive_reliable,balanced_reliable=balanced_reliable,all_three_positive_reliable=all(paired[primary+'__vs__'+b]['positive_bonferroni_99_167ci'][0]>0 for b in ['LISA','YOLO_World_SAM','ZoomNeXt_vision_only']),all_three_balanced_reliable=all(paired[primary+'__vs__'+b]['balanced_bonferroni_99_167ci'][0]>0 for b in ['LISA','YOLO_World_SAM','ZoomNeXt_vision_only'])),availability=read(D/'availability.json'))
(O/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps(dict(images=len(items),methods=len(folders),development_configurations=total,output=str(O)),indent=2))


