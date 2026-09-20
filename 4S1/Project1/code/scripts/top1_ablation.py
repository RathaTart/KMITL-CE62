"""Query-independent top detection control. Reuse a SAM mask only for identical boxes."""
import argparse
import shutil
from pathlib import Path
import torch
from torchvision.ops import nms
from attribute_pilot import read, write, lines, jsonl
from run_blip2_grounded_sam import phase_sam, DEFAULT_SAM

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a=p.parse_args()
folder=a.out/'top1'
manifest=read(a.out/'candidates/manifest.json')
write(folder/'manifest.json', manifest)
context={r['key']:r for r in lines(a.out/'context/grounding_boxes.jsonl')}
timings={r['key']:r for r in lines(a.out/'context/sam_timings.jsonl')}
items={i['key']:i for i in manifest['items']}
rows, reused=[],[]
(folder/'masks').mkdir(exist_ok=True)
for r in lines(a.out/'candidates/grounding_boxes.jsonl'):
    keep=nms(torch.tensor(r['boxes'],dtype=torch.float32).reshape(-1,4),torch.tensor(r['scores']),.5).tolist()[:1]
    row=dict(r, boxes=[r['boxes'][j] for j in keep],scores=[r['scores'][j] for j in keep],labels=['person']*len(keep))
    rows.append(row)
    if row['boxes']==context[r['key']]['boxes']:
        i=items[r['key']]
        name=f'{i["item_id"]}__{i["prompt_id"]}.png'
        shutil.copy2(a.out/'context/masks'/name,folder/'masks'/name)
        reused.append(dict(timings[r['key']],reused_from='context: exact same image and boxes'))
jsonl(folder/'grounding_boxes.jsonl',rows)
jsonl(folder/'sam_timings.jsonl',reused)
if len(reused)<len(rows):
    phase_sam(folder,DEFAULT_SAM,0)
write(folder/'ablation.json',dict(query_independent=True, n=len(rows), same_boxes_as_context=len(reused),
    note='SAM artifacts reused only for identical boxes on the same image. No fresh latency claim for reused masks.'))
print('Context equals top-1 boxes:',len(reused),'/',len(rows))
