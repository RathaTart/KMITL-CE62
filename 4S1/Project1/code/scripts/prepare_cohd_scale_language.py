"""Lock an explicitly reused native-language diagnostic; never invent attribute GT."""
import json,re,hashlib,platform
from pathlib import Path
import numpy as np
from PIL import Image
from pycocotools.coco import COCO
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_scale_20260915';D=C.parent/'dataset/grefcoco';refs=json.loads((D/'grefs(unc).json').read_text());coco=COCO(str(D/'instances.json'));images={}
for folder in ['router_dev_20260915','router_confirm_20260915','cohd_upgrade_test_20260915','training_free_extended_test_20260915','training_free_test_20260914']:
 for p in (C/'results'/folder).glob('*manifest.json'):
  data=json.loads(p.read_text())
  for i in data.get('items',[]):
   im=Path(i['image']);im=im if im.is_absolute() else C/im
   match=re.search(r'COCO_(?:train|val)2014_(\d+)',im.name)
   if match and im.is_file():images[int(match[1])]=im
person=next(k for k,v in coco.cats.items() if v['name']=='person');pools={k:[] for k in ['hat','clothing','absent']};trainids={r['image_id'] for r in refs if r['split']=='train'}
for r in refs:
 if r['split']!='testA' or r['image_id'] not in images:continue
 ids=r['ann_id'] if isinstance(r['ann_id'],list) else [r['ann_id']];anns=[coco.anns[k] for k in ids if k!=-1]
 if anns and any(a['category_id']!=person or a.get('iscrowd',0) for a in anns):continue
 if len([a for a in coco.imgToAnns[r['image_id']] if a['category_id']==person and not a.get('iscrowd',0)])<2:continue
 for s in r['sentences']:
  text=s['sent'].strip()
  if not anns and re.match(r'^(the |a |an |all |both |two )?(person|people|man|men|woman|women|boy|girl|guy|lady|kid)\b',text,re.I):kind='absent'
  elif anns and re.search(r'\b(hat|cap|beanie)\b',text,re.I):kind='hat'
  elif anns and re.search(r'\b(shirt|jacket|coat|dress|shorts)\b',text,re.I):kind='clothing'
  else:continue
  pools[kind].append((r,s,ids))
selected=[];used=set()
for kind,required in [('hat',12),('clothing',12),('absent',8)]:
 count=0
 for r,s,ids in sorted(pools[kind],key=lambda x:(x[0]['image_id'],x[1]['sent_id'])):
  if r['image_id'] in used:continue
  used.add(r['image_id']);selected.append((kind,r,s,ids));count+=1
  if count==required:break
print('selected',len(selected),{k:sum(x[0]==k for x in selected) for k in pools},flush=True)
items=[]
def save(p,mask):p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(p);return str(p)
for kind,r,s,ids in selected:
 ident='language_'+str(s['sent_id']);image=images[r['image_id']];info=coco.imgs[r['image_id']];masks=[coco.annToMask(coco.anns[k])>0 for k in ids if k!=-1];gt=np.logical_or.reduce(masks) if masks else np.zeros((info['height'],info['width']),bool);base=O/'language_inputs'/ident;ips=[save(base/f'instance_{j}.png',m) for j,m in enumerate(masks)]
 distractors=[save(base/f'distractor_{a["id"]}.png',coco.annToMask(a)>0) for a in coco.imgToAnns[r['image_id']] if a['category_id']==person and not a.get('iscrowd',0) and a['id'] not in ids]
 items.append(dict(key=ident+'::expression',item_id=ident,image=str(image),image_id=r['image_id'],image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),ground_truth=save(base/'gt.png',gt),ground_truth_instances=ips,distractor_instances=distractors,target_count=len(masks),expression=s['sent'],case_type='no_target' if not masks else 'multi_target' if len(masks)>1 else 'single_in_crowd',domain='gref',source_group='gref_'+str(r['image_id']),attribute_group=kind,official_split='testA',in_upstream_gref_train=r['image_id'] in trainids))
p=O/'language_manifest.json';assert not p.exists();p.write_text(json.dumps(dict(items=items,status='Reused gRefCOCO imagery, new fixed attribute-focused diagnostic, not new held-out nor CCTV attribute validation',selection='First unique cached official testA person image per hat/clothing/absent group, native human expression and COCO instance mask; no model output used',source='https://github.com/henghuiding/gRefCOCO'),indent=2))
print('language locked',len(items),flush=True)
