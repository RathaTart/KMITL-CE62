"""Render fixed-frame examples plus zooms, no selection by model success."""
import json,platform
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_cctv_20260915';D=O/'examples';D.mkdir(exist_ok=True);items=json.loads((O/'test_manifest.json').read_text())['items'];rows=json.loads((O/'test_results/per_expression.json').read_text());by={k:{r['key']:r for r in v} for k,v in rows.items()};font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);record=[]
for group in sorted({i['source_group'] for i in items}):
 pool=[i for i in items if i['source_group']==group]
 for quant in [.25,.5,.75]:
  i=pool[int((len(pool)-1)*quant)];im=Image.open(i['image']).convert('RGB');w,h=im.size;boxes=[]
  if 'boxes' in i:boxes=[g['box'] for g in i['boxes']]
  else:
   for p in i['ground_truth_instances']:
    y,x=np.where(np.asarray(Image.open(p))>0)
    if len(x):boxes.append([int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1])
  eligible=[b for b in boxes if b[3]-b[1]>=12];b=min(eligible or boxes,key=lambda b:b[3]-b[1]);cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;side=max(100,(b[3]-b[1])*3);crop=(int(max(0,cx-side/2)),int(max(0,cy-side/2)),int(min(w,cx+side/2)),int(min(h,cy+side/2)))
  canvas=Image.new('RGB',(1600,720),'white');draw=ImageDraw.Draw(canvas);draw.text((12,6),group+' | '+i['item_id']+' | prompt: all people',font=font,fill='black');draw.text((12,32),'Fixed 25/50/75% sampled frame; zoom shows smallest annotated person >=12 px. Orange = model mask.',font=small,fill='black')
  for col,mode in enumerate(['ground_truth','original','customA','customB']):
   tile=im.copy();a=np.asarray(im).copy()
   if mode=='ground_truth':
    if 'ground_truth' in i:
     m=np.asarray(Image.open(i['ground_truth']))>0;a[m]=(a[m]*.5+np.array([0,230,60])*.5).astype('uint8');tile=Image.fromarray(a)
    else:
     dr=ImageDraw.Draw(tile)
     for box in boxes:dr.rectangle(box,outline='lime',width=2)
   else:
    m=np.asarray(Image.open(by[mode][i['key']]['mask']))>0;a[m]=(a[m]*.5+np.array([255,130,0])*.5).astype('uint8');tile=Image.fromarray(a)
   dr=ImageDraw.Draw(tile);dr.rectangle(crop,outline='cyan',width=2);full=tile.copy();full.thumbnail((395,300));canvas.paste(full,(col*400+(400-full.width)//2,85));zoom=tile.crop(crop);scale=min(395/zoom.width,290/zoom.height);zoom=zoom.resize((round(zoom.width*scale),round(zoom.height*scale)),Image.Resampling.NEAREST);canvas.paste(zoom,(col*400+(400-zoom.width)//2,415));draw.text((col*400+10,60),mode,font=font,fill='black');draw.text((col*400+10,390),'Same region, enlarged',font=small,fill='black')
  path=D/(i['item_id']+'.png');canvas.save(path);record.append(dict(key=i['key'],selection_quantile=quant,source=group,path=str(path),zoom_gt_box=b))
(D/'selection.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
