"""Use only the six previously explored images to select mode and thresholds."""
import json,platform,hashlib,time
from pathlib import Path
assert platform.node()=='cenara70hx'
from PIL import Image
from region_verifier_engine import RegionVerifier
R=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915');out=R/'development';assert not out.exists();out.mkdir()
old=json.loads(Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915/diagnostic/lock.json').read_text());engine=RegionVerifier();rows=[]
for s in old['samples']:
 mask,labels,ids,boxes,meta=engine.propose(s['path']);im=Image.open(s['path']).convert('RGB')
 for attribute in ['hat','black_coat']:
  features=engine.features(im,boxes,attribute,['region','whole']);rows.append(dict(path=s['path'],attribute=attribute,expected=s[attribute+'_reference'],features=features,boxes=boxes))
(out/'features.json').write_text(json.dumps(rows,indent=2));selection={};sweep=[]
for attribute in ['hat','black_coat']:
 candidates=[]
 for mode in ['region','whole']:
  for threshold in [-.02,-.01,0.,.01,.02]:
   rr=[r for r in rows if r['attribute']==attribute];pred=[any(f['margin']>threshold for f in r['features'] if f['mode']==mode) for r in rr]
   tp=sum(p and r['expected'] for p,r in zip(pred,rr));tn=sum(not p and not r['expected'] for p,r in zip(pred,rr));P=sum(r['expected'] for r in rr);N=len(rr)-P
   candidates.append(dict(attribute=attribute,mode=mode,threshold=threshold,tp=tp,tn=tn,positive=P,negative=N,balanced=.5*(tp/P+tn/N)))
 # Preserve every development positive when possible, then reject the most negatives.
 eligible=[c for c in candidates if c['tp']==c['positive']]
 if not eligible:eligible=candidates
 best=max(eligible,key=lambda c:(c['balanced'],c['mode']=='region',-abs(c['threshold'])))
 selection[attribute]=best;sweep+=candidates
(out/'sweep.json').write_text(json.dumps(sweep,indent=2))
lock=dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),selection=selection,training=False,development_ids=[s['source']['id'] for s in old['samples']],candidate_limit=1,main_person=True,threshold_grid=[-.02,-.01,0,.01,.02],criterion='Preserve all development positives if possible, maximize balanced presence score, prefer region then threshold closest to zero',hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ['region_verifier_engine.py','cohd_scale_engine.py','develop_region_verifier.py']},reference_limitation='Assistant-reviewed presence only, not native masks or independent human labels')
(R/'method_lock.json').write_text(json.dumps(lock,indent=2));print(json.dumps(lock,indent=2),flush=True)
