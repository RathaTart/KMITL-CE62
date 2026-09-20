"""Render frozen routing decisions on confirmation images without GT access."""
import hashlib,json,platform,re
from pathlib import Path
import numpy as np
from PIL import Image
from router_features import features,action_mask,ACTIONS
from router_model import load,decide
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code');F=R/'results/router_confirm_20260915';D=R/'results/router_dev_20260915';loaded=load();lock=loaded[0];assert hashlib.sha256((F/'manifest.json').read_bytes()).hexdigest()==lock['confirmation_manifest_sha256']
def lines(p):return {r['key']:r for r in [json.loads(s) for s in p.read_text().splitlines()]}
items=json.loads((F/'manifest.json').read_text())['items'];yr=lines(F/'yolo/p3_expression/grounding_boxes.jsonl');pr=lines(F/'qwen_presence.jsonl');lr=lines(F/'p1_rows.jsonl');out=[]
for i in items:
    name=i['item_id']+'__'+i['prompt_id'];r=pr[i['key']]['results'][0];i=dict(i,zoom_mask=str(F/'zoom/masks'/(name+'.png')),zoom_probability=str(F/'zoom/probabilities'/(name+'.npy')),presence_probability=r['yes_probability'],presence_logit=r['logit_yes_no']);f=features(i,yr[i['key']]);actions=decide(f,loaded);actions.update(LISA_cached=0,YOLO_SAM=1,ZoomNeXt=2)
    lisa=np.asarray(Image.open(F/'p1_masks'/(name+'.png')))>0;yolo=np.asarray(Image.open(F/'yolo/p3_expression/masks'/(name+'.png')))>0;zoom=np.asarray(Image.open(i['zoom_mask']))>0
    text=lr[i['key']]['answer'].split('ASSISTANT:')[-1].lower();valid=bool(lr[i['key']]['emitted_seg']) or bool(re.search(r'\bno (?:matching )?(?:person|people|man|woman|one)\b|not (?:present|visible)|\bnone\b',text))
    for method,action in actions.items():
        folder=F/'predictions'/method;folder.mkdir(parents=True,exist_ok=True);path=folder/(name+'.png');mask=action_mask(action,lisa,yolo,zoom);Image.fromarray(mask.astype('uint8')*255).save(path);out.append(dict(key=i['key'],method=method,action=ACTIONS[action],action_id=action,mask=str(path),valid=valid if action==0 else True,mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),features=f))
(F/'prediction_audit.json').write_text(json.dumps(out,indent=2));print('Rendered',len(out),'predictions')
