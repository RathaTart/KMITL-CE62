"""Remote evidence rendering and prediction audit. No inference or fitting."""
import json,platform,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915');out=root/'diagnostic';lock=json.loads((out/'lock.json').read_text());rows=json.loads((out/'per_query.json').read_text());vis=out/'visuals';vis.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
audits=[]
for i,s in enumerate(lock['samples']):
 path=Path(s['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256']
 im=Image.open(path).convert('RGB');arr=np.array(im);w,h=im.size
 for kind in ['hat','black_coat','native']:
  q=next(x for x in lock['queries'] if x['sample_index']==i and x['kind']==kind)
  sheet=Image.new('RGB',(900,470),'#f3f6fc');d=ImageDraw.Draw(sheet)
  title={'hat':'Main person wearing a hat','black_coat':'Main person wearing a black coat','native':'Original dataset description'}[kind]
  d.text((15,12),title,font=font,fill='#10213b');d.text((15,38),'Expected: '+('present' if q['expected_presence'] else 'absent')+' | Exploratory presence check, not mask IoU',font=small,fill='#344866')
  for j,method in enumerate(['input','original','scale704_guard']):
   rgb=arr.copy();r=None
   if method!='input':
    mask=np.array(Image.open(out/method/(q['id']+'.png')))>0;assert mask.shape==(h,w);r=next(x for x in rows if x['id']==q['id'] and x['method']==method);assert bool(mask.any())==r['output_nonempty'];rgb[mask]=(.52*rgb[mask]+.48*np.array([255,105,45])).astype('uint8')
   factor=min(280/w,330/h);panel=Image.fromarray(rgb).resize((round(w*factor),round(h*factor)),Image.Resampling.NEAREST);sheet.paste(panel,(j*300+(300-panel.width)//2,76+(330-panel.height)//2))
   label={'input':'Original image','original':'CoHD original','scale704_guard':'Scale704 + guard'}[method];d.text((j*300+12,410),label,font=font,fill='#10213b')
   if r:d.text((j*300+12,438),f"{'Mask returned' if r['output_nonempty'] else 'Empty'} | {r['request_s']:.3f}s (shared GPU)",font=small,fill='#8c2929' if not r['presence_agreement'] else '#176944')
  sheet.save(vis/(q['id']+'.jpg'),quality=93)
 for method in lock['methods']:
  a=np.array(Image.open(out/method/f'{i:02d}_hat.png'))>0;b=np.array(Image.open(out/method/f'{i:02d}_black_coat.png'))>0
  audits.append(dict(sample=i,method=method,hat_vs_black_prediction_iou=float((a&b).sum()/max(1,(a|b).sum()))))
(out/'audit.json').write_text(json.dumps(dict(mask_count=len(rows),samples=len(lock['samples']),input_hashes_verified=True,prediction_overlap=audits,checkpoint='CoHD_CoHD_grefcoco_swin_tiny.pth',new_sample_training=False,pretraining_overlap='Not ruled out; different dataset from gRefCOCO checkpoint task, no general unseen-pretraining claim'),indent=2))
print(json.dumps(audits,indent=2))
