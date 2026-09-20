"""Assemble explored router development evidence and deterministic fit/validation split."""
import json,hashlib,platform,random,re
from pathlib import Path
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');D=R/'results/router_dev_20260915';D.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
items=[]
for source in ['extended_dev_20260915','extended_test_20260915']:
    presence={r['key']:r['results'][0] for r in [json.loads(line) for line in (R/'results'/source/'qwen_presence.jsonl').read_text().splitlines()]}
    for old in read(R/'results'/source/'manifest.json')['items']:
        i=dict(old)
        i['presence_probability']=presence[i['key']]['yes_probability']
        i['presence_logit']=presence[i['key']]['logit_yes_no']
        i.setdefault('image_id',int(re.search(r'COCO_(?:train|val)2014_(\d+)',Path(i['image']).name)[1]))
        if source=='extended_test_20260915':base=R/'results/training_free_extended_20260915';yolo=base/'yolo/p3_expression';zoom=base/'zoom'
        elif i['development_source']=='grefcoco_pilot_p1_p2':yolo=R/'results/attribute_pilot_20260914/yolo/p3_expression';zoom=R/'results/lisa_refinement_20260914/zoom'
        else:base=R/'results/training_free_fresh_20260914';yolo=base/'yolo/p3_expression';zoom=base/'zoom'
        name=i['item_id']+'__'+i['prompt_id']
        i.update(yolo_mask=str(yolo/'masks'/(name+'.png')),yolo_boxes=str(yolo/'grounding_boxes.jsonl'),zoom_mask=str(zoom/'masks'/(name+'.png')),zoom_probability=str(zoom/'probabilities'/(name+'.npy')))
        for k in ['lisa_mask','yolo_mask','zoom_mask','zoom_probability','ground_truth']:assert Path(i[k]).exists(),(k,i[k])
        items.append(i)
assert len(items)==270 and len({i['image_id'] for i in items})==270
rng=random.Random(2026091507);train=[];validation=[]
for kind in ['single_in_crowd','multi_target','no_target']:
    group=[i['key'] for i in items if i['case_type']==kind];rng.shuffle(group);n=round(len(group)*2/3);train+=group[:n];validation+=group[n:]
manifest=dict(items=items,status='All 270 images are now explored router development; previous 180-image report remains historical, not a new untouched test')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2));(D/'split.json').write_text(json.dumps(dict(seed=2026091507,fit=train,validation=validation,scope='Internal development validation only'),indent=2))
print(json.dumps(dict(n=len(items),fit=len(train),validation=len(validation)),indent=2))
