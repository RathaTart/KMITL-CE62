import json,platform
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/released_checkpoints_20260915';F=C/'results/router_confirm_20260915';items=json.loads((F/'manifest.json').read_text())['items'];selected=[next(i for i in items if i['case_type']==c) for c in ['single_in_crowd','multi_target','no_target']];canvas=Image.new('RGB',(1200,3*280),'white');d=ImageDraw.Draw(canvas)
for row,i in enumerate(selected):
 name=i['item_id']+'__'+i['prompt_id']+'.png';rgb=np.asarray(Image.open(i['image']).convert('RGB'));paths=[('Ground truth',Path(i['ground_truth'])),('LISA',F/'p1_masks'/name),('CoHD Tiny',O/'CoHD_Tiny/masks'/name),('SSP SAM 224',O/'SSP_SAM_224_AMP/masks'/name)]
 d.text((8,row*280+3),i['expression'][:150],fill='black')
 for col,(label,path) in enumerate(paths):
  mask=np.asarray(Image.open(path))>0;vis=rgb.copy();vis[mask]=(vis[mask]*.5+np.array([255,110,20])*.5).astype('uint8');im=Image.fromarray(vis);im.thumbnail((295,240));canvas.paste(im,(col*300,row*280+40));d.text((col*300+8,row*280+22),label,fill='black')
canvas.save(O/'examples.png')
(O/'examples.json').write_text(json.dumps(dict(selection='First manifest example from each case type, selected without considering scores',keys=[i['key'] for i in selected]),indent=2))

