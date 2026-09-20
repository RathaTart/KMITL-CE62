"""Compose and freeze a primary training-free system using development only."""
import argparse,hashlib,itertools,json,platform,time
from pathlib import Path
import numpy as np
from PIL import Image
from extended_pipeline import pipeline_mask
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--rex-unavailable',action='store_true');a=p.parse_args()
root=Path('/home/osta/lisa-eval/code');out=root/'results/extended_dev_20260915';items=json.loads((out/'manifest.json').read_text())['items'];records={};missing=[]
for source in ['qwen_presence','qwen_lisa','qwen_candidate','blip_presence','rexseek','rexseek_clauses']:
    f=out/(source+'.jsonl');rows=[json.loads(s) for s in f.read_text().splitlines() if s] if f.exists() else []
    if len(rows)==90:records[source]={r['key']:r for r in rows}
    elif not source.startswith('rexseek') or not a.rex_unavailable:missing.append(source)
if a.freeze:assert not missing,missing
shapes={'lisa':{'family':'baseline'}}
for fn,label in [('geometry_sweep.json','geometry'),('custom_boundary_sweep.json','custom_boundary'),('guided_sweep.json','guided')]:
    data=json.loads((out/fn).read_text());shapes[label]=data['trials'][data['rank'][0]]['config']
corrections={'none':None};standalone={}
cpath=out/'candidate_sweep.json'
if cpath.exists():
    cs=json.loads(cpath.read_text())['trials']
    for family in ['qwen_correction','rexseek_correction','rexseek_clauses_correction']:
        eligible=[t for t in cs.values() if t['config']['family']==family]
        if eligible and max(t['positive_iou'] for t in eligible)>json.loads((out/'geometry_sweep.json').read_text())['trials']['lisa']['positive_iou']+.005:corrections[family]=max(eligible,key=lambda t:t['positive_iou'])['config']
    for family in ['qwen_candidate','rexseek','rexseek_clauses']:
        eligible=[t for t in cs.values() if t['config']['family']==family]
        if eligible and max(t['positive_iou'] for t in eligible)>=json.loads((out/'geometry_sweep.json').read_text())['trials']['lisa']['positive_iou']-.05:standalone[family]={'selector':max(eligible,key=lambda t:t['positive_iou'])['config'],'shape':{'family':'baseline'}}
configs={}
for shape,scfg in shapes.items():
    for correction,ccfg in corrections.items():
        cfg={'shape':scfg}
        if ccfg:cfg['correction']=ccfg
        configs[shape+'_'+correction]=cfg
configs.update(standalone);base_trials={}
for label,cfg in configs.items():
    rows=[]
    for i in items:
        lisa=np.asarray(Image.open(i['lisa_mask']))>0;g=np.asarray(Image.open(i['ground_truth']))>0;ms=np.load(i['proposals'])['masks'];image=np.asarray(Image.open(i['image']).convert('RGB'))
        pred,valid,audit=pipeline_mask(i,lisa,ms,cfg,records,image);inter=int((pred&g).sum());union=int((pred|g).sum())
        rows.append(dict(key=i['key'],positive=bool(g.any()),iou=(inter/union if union else 1.) if valid else 0.,intersection=inter,union=union,pred_pixels=int(pred.sum()),gt_pixels=int(g.sum()),valid=valid,rejected=False))
    base_trials[label]=dict(config=cfg,rows=rows)
trials={}
def record(label,cfg,rows):
    pos=[r for r in rows if r['positive']];neg=[r for r in rows if not r['positive']];piou=float(np.mean([r['iou'] for r in pos]));acc=float(np.mean([r['pred_pixels']==0 and r['valid'] for r in neg]));reject=float(np.mean([r['rejected'] for r in pos]));complexity=int(cfg.get('shape',{}).get('family')!='baseline')+(len(cfg['verifier'].get('sources') or [cfg['verifier']['source']]) if 'verifier' in cfg else 0)+int('correction' in cfg)+int('selector' in cfg)
    trials[label]=dict(config=cfg,rows=rows,positive_iou=piou,no_target_accuracy=acc,overall_iou=float(np.mean([r['iou'] for r in rows])),balanced_score=(piou+acc)/2,positive_false_rejection=reject,complexity=complexity)
available=[s for s in ['qwen_presence','qwen_lisa','blip_presence'] if s in records]
verifiers=[(s,dict(source=s)) for s in available]
for n in [2,3]:
    for sources in itertools.combinations(available,n):
        for reduction in (['min','max','mean'] if n==2 else ['min','max','mean','median']):verifiers.append((reduction+'_'+'+'.join(sources),dict(sources=list(sources),reduce=reduction)))
for label,t in base_trials.items():
    record(label,t['config'],t['rows'])
    for verifier_label,vcfg in verifiers:
        sources=vcfg.get('sources') or [vcfg['source']];reduction=vcfg.get('reduce','mean');scores={}
        for r in t['rows']:
            values=[]
            for source in sources:
                v=records[source][r['key']];values.append(v['results'][0]['yes_probability'] if 'results' in v else v['yes_probability'])
            scores[r['key']]=float({'min':np.min,'max':np.max,'mean':np.mean,'median':np.median}[reduction](values))
        for threshold in [.01,.025,.05,.075,.1,.125,.15,.175,.2,.25,.3,.4,.5,.6,.7,.8,.9]:
            rows=[]
            for r in t['rows']:
                row=dict(r)
                if scores[r['key']]<threshold:row.update(iou=0. if r['positive'] else 1.,pred_pixels=0,intersection=0,union=r['gt_pixels'],valid=True,rejected=True)
                rows.append(row)
            record(f'{label}_{verifier_label}_{threshold}',dict(t['config'],verifier=dict(vcfg,threshold=threshold)),rows)
base=trials['lisa_none']['positive_iou'];primary_pool=[k for k,t in trials.items() if t['positive_iou']>=base-1e-12 and t['positive_false_rejection']==0]
rank=sorted(primary_pool,key=lambda k:(trials[k]['balanced_score'],trials[k]['positive_iou'],-trials[k]['complexity']),reverse=True)
aggressive=max([k for k,t in trials.items() if t['positive_iou']>=base-.01],key=lambda k:(trials[k]['balanced_score'],trials[k]['positive_iou'],-trials[k]['complexity']))
selected=rank[0];result=dict(status='Frozen' if a.freeze else 'Development interim',primary=selected,aggressive=aggressive,baseline_positive_iou=base,missing=missing,trials=trials,rank=rank)
(out/'composition_sweep.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:{s:trials[k][s] for s in ['config','positive_iou','no_target_accuracy','positive_false_rejection','overall_iou']} for k in [selected,aggressive]},indent=2))
if a.freeze:
    lockpath=out/'method_lock.json';assert not lockpath.exists(),'Never overwrite a frozen lock'
    final={'Custom_primary':trials[selected]['config'],'Custom_aggressive':trials[aggressive]['config'],'LISA_custom_boundary':{'shape':shapes['custom_boundary']},'LISA_union':{'shape':shapes['geometry']},'LISA_guided':{'shape':shapes['guided']}}
    if 'verifier' in trials[selected]['config']:final['LISA_verifier_only']={'shape':{'family':'baseline'},'verifier':trials[selected]['config']['verifier']}
    final.update({k+'_SAM':v for k,v in standalone.items()})
    script_names=['extended_pipeline.py','extended_shapes.py','extended_training_free.py','extended_blip.py','extended_rexseek.py','extended_rexseek_clauses.py','freeze_extended_pipeline.py','render_extended_pipeline.py','score_extended_pipeline.py','run_extended_selected_models.py']
    lock=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),primary='Custom_primary',primary_development_label=selected,variants=final,development_summary={k:{s:t[s] for s in ['positive_iou','no_target_accuracy','overall_iou']} for k,t in trials.items() if k in [selected,aggressive]},selection_policy='Maximize balanced mean of positive IoU and no-target accuracy among development configurations with no positive verifier rejection and positive IoU >= LISA. Tie break by positive IoU then fewer stages. Aggressive secondary allows at most 1 percentage point positive IoU loss. Correction stages require at least 0.5 percentage point development positive-IoU improvement; standalone selector finalists must be within 5 points of LISA. Single-source, pairwise min/max/mean and three-source min/max/mean/median verifier reductions are development candidates. All other variants exploratory ablations.',n_development=90,n_test=180,n_compositions=len(trials),weights_updated=False,pretraining_caveat='Public pretrained checkpoints may have seen COCO; this is project-held-out evaluation, not pretraining-clean zero-shot.',fresh_manifest_sha256=hashlib.sha256((root/'results/training_free_extended_20260915/manifest.json').read_bytes()).hexdigest(),script_sha256={n:hashlib.sha256((root/'scripts'/n).read_bytes()).hexdigest() for n in script_names})
    lockpath.write_text(json.dumps(lock,indent=2))




