"""Development evaluation of proposal verifiers and conservative custom corrections."""
import json,platform,re
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915');items=json.loads((out/'manifest.json').read_text())['items'];trials={}
def add(label,p,g,i,cfg,valid=True):
    inter=int((p&g).sum());union=int((p|g).sum());trials.setdefault(label,dict(config=cfg,rows=[]))['rows'].append(dict(key=i['key'],positive=bool(g.any()),iou=(inter/union if union else 1.) if valid else 0.,intersection=inter,union=union,pred_pixels=int(p.sum()),gt_pixels=int(g.sum()),valid=valid))
qpath=out/'qwen_candidate.jsonl';qrows=[json.loads(s) for s in qpath.read_text().splitlines() if s] if qpath.exists() else [];q={r['key']:r for r in qrows} if len(qrows)==90 else {}
rex_sources={}
for source in ['rexseek','rexseek_clauses']:
    rpath=out/(source+'.jsonl');rrows=[json.loads(s) for s in rpath.read_text().splitlines() if s] if rpath.exists() else []
    if len(rrows)==90:rex_sources[source]={r['key']:r for r in rrows}
for i in items:
    data=np.load(i['proposals']);ms=data['masks'];g=np.asarray(Image.open(i['ground_truth']))>0;lisa=np.asarray(Image.open(i['lisa_mask']))>0
    if q:
        scores=np.array([r['yes_probability'] for r in q[i['key']]['results']]);assert len(scores)==len(ms)
        for threshold in [.3,.4,.5,.6,.7,.8,.9]:
            for mode in ['all','grammar']:
                keep=np.flatnonzero(scores>=threshold)
                plural=bool(re.search(r'\b(all|both|people|men|women|boys|girls|kids|players)\b|\band\b',i['expression'],re.I))
                if mode=='grammar' and len(keep) and not plural:keep=np.array([int(scores.argmax())])
                pred=ms[keep].any(0) if len(keep) else np.zeros_like(g)
                add(f'qwen_{mode}_{threshold}',pred,g,i,dict(family='qwen_candidate',mode=mode,threshold=threshold))
                for agreement in [.25,.5,.75]:
                    inter=(pred&lisa).sum();union=(pred|lisa).sum();iou=inter/max(union,1)
                    # Replace only when a confident nonempty candidate substantially disagrees.
                    corrected=pred if len(keep) and iou<agreement else lisa
                    add(f'correct_{mode}_{threshold}_{agreement}',corrected,g,i,dict(family='qwen_correction',mode=mode,threshold=threshold,agreement=agreement))
    for family,rex in rex_sources.items():
        r=rex[i['key']];keep=r['selected_indices'];pred=ms[keep].any(0) if keep else np.zeros_like(g)
        add(family,pred,g,i,dict(family=family),valid=r['valid'])
        for agreement in [.25,.5,.75]:
            overlap=(pred&lisa).sum()/max((pred|lisa).sum(),1);corrected=pred if keep and r['valid'] and overlap<agreement else lisa
            add(f'{family}_correction_{agreement}',corrected,g,i,dict(family=family+'_correction',agreement=agreement))
for t in trials.values():
    pos=[r for r in t['rows'] if r['positive']];neg=[r for r in t['rows'] if not r['positive']]
    t.update(positive_iou=float(np.mean([r['iou'] for r in pos])),overall_iou=float(np.mean([r['iou'] for r in t['rows']])),no_target_accuracy=float(np.mean([r['pred_pixels']==0 and r['valid'] for r in neg])))
rank=sorted(trials,key=lambda k:trials[k]['positive_iou'],reverse=True)
(out/'candidate_sweep.json').write_text(json.dumps(dict(status='development only',trials=trials,rank=rank),indent=2))
for k in rank[:8]:print(k,{s:trials[k][s] for s in ['positive_iou','overall_iou','no_target_accuracy']})

