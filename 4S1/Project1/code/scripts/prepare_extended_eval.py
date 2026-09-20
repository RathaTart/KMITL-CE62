"""Lock new gRefCOCO-person evaluation images, excluding historical manifests."""
import hashlib,json,platform,random,re,time,urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2,numpy as np
from pycocotools.coco import COCO
if platform.node()!='cenara70hx':raise SystemExit('Remote only')
ROOT=Path('/home/osta/lisa-eval');OUT=ROOT/'code/results/training_free_extended_20260915';OUT.mkdir(exist_ok=True); assert not any(OUT.iterdir()), 'Output must be empty'
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
    if ref['split']!='testA' or ref['image_id'] in old:continue
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
rng=random.Random(2026091501);used=set();selected=[]
for kind in ['single_in_crowd','multi_target','no_target']:
    pool=candidates[kind];rng.shuffle(pool);chosen=[]
    for r in pool:
        imageid=r['ref']['image_id']
        if imageid in used:continue
        chosen.append(r);used.add(imageid)
        if len(chosen)==60:break
    if len(chosen)!=60:raise RuntimeError(f'Insufficient unique {kind}: {len(chosen)}')
    selected.extend(chosen)
# Sampling and annotation choices are locked before any model output exists.
write(OUT/'selection_lock.json',dict(seed=2026091501,official_split='testA',per_group=60,selected=[dict(image_id=r['ref']['image_id'],sent_id=r['sentence']['sent_id'],case_type=r['kind'],expression=r['sentence']['sent']) for r in selected],excluded_image_ids=sorted(old),historical_manifests=scanned,annotation_sha256={'grefs':sha(refs_path),'instances':sha(anns_path)},selection='person-only positive targets, at least two annotated people in image; negative starts with explicit person subject; one expression per unique image',status='New to this project evaluation, not guaranteed absent from foundation-model pretraining'))
def make(r):
    ref=r['ref'];s=r['sentence'];info=coco.imgs[ref['image_id']];fn=info['file_name'];p=OUT/'inputs/images'/fn;p.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(3):
        try:urllib.request.urlretrieve('http://images.cocodataset.org/train2014/'+fn,p);break
        except Exception:
            if attempt==2:raise
    if sha(p) in oldhash:raise RuntimeError('Historical image hash overlap: '+fn)
    im=cv2.imread(str(p));assert im is not None and im.shape[:2]==(info['height'],info['width'])
    ids=[k for k in ref['ann_id'] if k!=-1];masks=[coco.annToMask(coco.anns[k])>0 for k in ids];gt=np.logical_or.reduce(masks) if masks else np.zeros(im.shape[:2],bool)
    itemid=f'gref_{s["sent_id"]}';gtpath=OUT/'inputs/gt'/f'{itemid}.png';gtpath.parent.mkdir(parents=True,exist_ok=True);cv2.imwrite(str(gtpath),gt.astype('uint8')*255);ips=[]
    for j,m in enumerate(masks,1):
        ip=OUT/'inputs/instances'/f'{itemid}__{j}.png';ip.parent.mkdir(parents=True,exist_ok=True);cv2.imwrite(str(ip),m.astype('uint8')*255);ips.append(str(ip))
    return dict(key=itemid+'::expression',item_id=itemid,prompt_id='expression',image=str(p),image_id=ref['image_id'],image_sha256=sha(p),ground_truth=str(gtpath),ground_truth_instances=ips,expression=s['sent'],official_split='testA',case_type=r['kind'],target_count=len(ids),target_ann_ids=ids,lisa_instruction=s['sent']+' Please output segmentation mask.',blip2_instruction=s['sent'])
with ThreadPoolExecutor(max_workers=8) as pool:items=list(pool.map(make,selected))
items.sort(key=lambda i:i['image_id']);assert len({i['image_sha256'] for i in items})==180
write(OUT/'manifest.json',dict(dataset='grefcoco',dataset_label='Fresh gRefCOCO person subset',selection='180 unique images, official testA only, 60 single / 60 multi / 60 no-target; prior manifests and hashes excluded',status='Freeze methods using historical development before scoring this new subset',source='https://github.com/henghuiding/gRefCOCO',items=items))
print(json.dumps(dict(n=len(items),old_images_excluded=len(old),candidates={k:len(v) for k,v in candidates.items()},no_target_expressions=[i['expression'] for i in items if i['case_type']=='no_target']),indent=2))


