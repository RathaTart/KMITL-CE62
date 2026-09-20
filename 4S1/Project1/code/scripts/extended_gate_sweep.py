"""Dev-only likelihood gate search; never reads fresh test outputs."""
import json,platform
from pathlib import Path
import numpy as np
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915')
geometries=json.loads((out/'geometry_sweep.json').read_text())['trials'];base=geometries['lisa']['positive_iou'];trials={}
for family in ['qwen_presence','qwen_lisa','blip_presence']:
    p=out/(family+'.jsonl')
    if not p.exists():continue
    rows=[json.loads(s) for s in p.read_text().splitlines() if s]
    if len(rows)!=90:continue
    scores={r['key']:r['results'][0]['yes_probability'] if 'results' in r else r['yes_probability'] for r in rows}
    for shape in ['lisa','agreement_union_0.5','remove_small_0.005','fill_holes','median_11']:
        for threshold in [0.,.01,.025,.05,.075,.1,.125,.15,.175,.2,.25,.3,.4,.5,.6,.7,.8,.9]:
            result=[]
            for r in geometries[shape]['rows']:
                reject=scores[r['key']]<threshold;row=dict(r,rejected=reject)
                if reject:row.update(iou=0. if r['positive'] else 1.,pred_pixels=0,intersection=0,union=r['gt_pixels'])
                result.append(row)
            pos=[r for r in result if r['positive']];neg=[r for r in result if not r['positive']];piou=float(np.mean([r['iou'] for r in pos]));acc=float(np.mean([r['pred_pixels']==0 for r in neg]))
            trials[f'{family}_{shape}_{threshold}']=dict(config=dict(family=family,shape=shape,threshold=threshold),rows=result,positive_iou=piou,no_target_accuracy=acc,overall_iou=float(np.mean([r['iou'] for r in result])),balanced_score=(piou+acc)/2,positive_false_rejection=float(np.mean([r['rejected'] for r in pos])),eligible=piou>=base-.01)
rank=sorted(trials,key=lambda k:(trials[k]['eligible'],trials[k]['balanced_score'],trials[k]['positive_iou']),reverse=True)
(out/'gate_sweep.json').write_text(json.dumps(dict(status='Development-only interim search, not final method lock',baseline_positive_iou=base,trials=trials,rank=rank),indent=2))
print('baseline positive IoU',base)
for k in rank[:8]:print(k,{s:trials[k][s] for s in ['positive_iou','no_target_accuracy','positive_false_rejection','eligible']})
