"""Two reused full-frame CCTV examples; qualitative only, no appearance GT."""
import json,platform,time,hashlib
from pathlib import Path
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915');O=R/'fullframe';assert not O.exists();O.mkdir()
lock=json.loads((R/'method_lock.json').read_text());manifest=json.loads(Path('/home/osta/lisa-eval/code/results/cohd_scale_20260915/confirmation_manifest.json').read_text())['items'];items=[]
for domain in ['MOTS','PersonPath22']:
 candidates=[x for x in manifest if x['domain']==domain]
 if not candidates and domain=='PersonPath22':candidates=[x for x in manifest if x['domain']!='MOTS']
 items.append(candidates[0])
(O/'lock.json').write_text(json.dumps(dict(items=items,selection='First existing scale-confirmation frame per source, no attribute-based selection',main_person=False,limit=8,native_attribute_ground_truth=False,timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())),indent=2))
from region_verifier_engine import RegionVerifier,cohd_predict
from PIL import Image
engine=RegionVerifier();rows=[]
for method in ['original','scale704_guard']:cohd_predict(items[0]['image'],'all people',method)
engine.predict(items[0]['image'],'hat',lock['selection'],main_person=False)
for item in items:
 for attribute in ['hat','black_coat']:
  key=item['item_id']+'_'+attribute;prompt='people wearing '+('hats' if attribute=='hat' else 'black coats')
  for method in ['original','scale704_guard','verified']:
   if method=='verified':mask,raw,meta=engine.predict(item['image'],attribute,lock['selection'],main_person=False)
   else:mask,meta=cohd_predict(item['image'],prompt,method)
   folder=O/method;folder.mkdir(exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(folder/(key+'.png'));rows.append(dict(key=key,image=item['image'],prompt=prompt,attribute=attribute,method=method,**meta));print(key,method,meta['request_s'],flush=True)
(O/'per_query.json').write_text(json.dumps(rows,indent=2))
