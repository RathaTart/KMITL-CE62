"""Executable custom training-free pipeline from frozen model outputs."""
import re
import numpy as np
from extended_shapes import shape_mask

def candidate_selection(expression,scores,cfg):
    scores=np.array(scores);keep=np.flatnonzero(scores>=cfg['threshold'])
    plural=bool(re.search(r'\b(all|both|people|men|women|boys|girls|kids|players)\b|\band\b',expression,re.I))
    if cfg['mode']=='grammar' and len(keep) and not plural:keep=np.array([int(scores.argmax())])
    return keep.tolist()

def pipeline_mask(item,lisa,ms,cfg,records,image=None):
    key=item['key'];seed=lisa.copy();valid=True;audit={}
    selection=cfg.get('selector') or cfg.get('correction')
    if selection:
        family=selection['family']
        if family.startswith('qwen'):
            scores=[r['yes_probability'] for r in records['qwen_candidate'][key]['results']]
            keep=candidate_selection(item['expression'],scores,selection);selection_valid=True
        elif family.startswith('rexseek'):
            r=records['rexseek_clauses' if family.startswith('rexseek_clauses') else 'rexseek'][key];keep=r['selected_indices'];selection_valid=r['valid']
        else:raise ValueError(selection)
        candidate=ms[keep].any(0) if keep else np.zeros_like(lisa)
        if cfg.get('selector'):
            seed=candidate;valid=selection_valid
        else:
            overlap=(candidate&seed).sum()/max((candidate|seed).sum(),1)
            replace=bool(keep) and selection_valid and overlap<selection['agreement']
            if replace:seed=candidate
            audit.update(replaced_lisa=replace,proposal_lisa_iou=float(overlap))
        audit.update(selected_indices=keep,selector_valid=selection_valid)
    pred=shape_mask(seed,ms,cfg.get('shape',{'family':'baseline'}),image)
    verifier=cfg.get('verifier')
    if verifier:
        sources=verifier.get('sources') or [verifier['source']];values=[]
        for source in sources:
            row=records[source][key];values.append(row['results'][0]['yes_probability'] if 'results' in row else row['yes_probability'])
        reduction=verifier.get('reduce','mean');score=float({'min':np.min,'max':np.max,'mean':np.mean,'median':np.median}[reduction](values))
        audit['verification_sources']=dict(zip(sources,values))
        rejected=score<verifier['threshold']
        if rejected:pred=np.zeros_like(lisa);valid=True
        audit.update(rejected=rejected,verification_score=score)
    return pred,valid,audit


