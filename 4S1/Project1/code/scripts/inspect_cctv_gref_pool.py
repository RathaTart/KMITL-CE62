"""Lock new gRefCOCO-person evaluation images, excluding historical manifests."""
import hashlib,json,platform,random,re,time,urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2,numpy as np
from pycocotools.coco import COCO
if platform.node()!='cenara70hx':raise SystemExit('Remote only')
ROOT=Path('/home/osta/lisa-eval');OUT=ROOT/'code/results/cohd_cctv_gref_test_20260915';OUT.mkdir(exist_ok=True); assert not any(OUT.iterdir()), 'Output must be empty'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
old=set();oldhash=set();scanned=[]
for root in [ROOT/'code/results',Path('/home/osta/Yolo_World/results')]:
    for p in root.rglob('manifest.json'):
        if OUT in p.parents:continue
        try:items=json.loads(p.read_text()).get('items',[])
        except (ValueError,AttributeError):continue
        added=0
        for i in items:
            path=Path(i.get('image',''));found=re.search(r'COCO_(?:train|val)2014_(\d+)',path.name)
            if found:
                old.add(int(found[1]));added+=1
                if not path.is_absolute():path=ROOT/'code'/path
                if path.is_file():oldhash.add(sha(path))
        if added:scanned.append(dict(path=str(p),items=added,sha256=sha(p)))
refs_path=ROOT/'dataset/grefcoco/grefs(unc).json';anns_path=ROOT/'dataset/grefcoco/instances.json';refs=json.loads(refs_path.read_text());coco=COCO(str(anns_path))
person=next(k for k,v in coco.cats.items() if v['name']=='person');candidates=defaultdict(list)
person_subject=re.compile(r'^(?:the |a |an |all |both |two |three |four )?(?:person|people|man|men|woman|women|boy|boys|girl|girls|kid|kids|child|children|guy|guys|lady|ladies|player|players)\b',re.I)
for ref in refs:
    if ref['split']!='val' or ref['image_id'] in old:continue
    ids=ref['ann_id'] if isinstance(ref['ann_id'],list) else [ref['ann_id']]
    anns=[coco.anns[k] for k in ids if k!=-1]
    persons=[v for v in coco.imgToAnns[ref['image_id']] if v['category_id']==person and not v.get('iscrowd',0)]
    if len(persons)<2:continue
    if ids==[-1]:kind='no_target'
    elif anns and all(v['category_id']==person and not v.get('iscrowd',0) for v in anns):kind='multi_target' if len(anns)>1 else 'single_in_crowd'
    else:continue
    for s in ref['sentences']:
        text=s['sent'].strip()
        if not text or kind=='no_target' and not person_subject.search(text):continue
        candidates[kind].append(dict(ref=ref,sentence=s,kind=kind))

print({k:len({r['ref']['image_id'] for r in v}) for k,v in candidates.items()})
