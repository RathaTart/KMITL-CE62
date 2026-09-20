"""Remote audit and evidence figures; no threshold changes or inference."""
import json,platform,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915');C=R/'confirmation';F=R/'fullframe';V=R/'visuals';V.mkdir(exist_ok=True)
lock=json.loads((R/'method_lock.json').read_text());manifest=json.loads((C/'manifest.json').read_text());rows=json.loads((C/'per_query.json').read_text());summary=json.loads((C/'summary.json').read_text());full=json.loads((F/'per_query.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
methods=['original','scale704_guard','verified'];names=['Original image','CoHD original','Scale704','With verifier']
def figure(path,key,prompt,rr,folder,expected=None):
 im=Image.open(path).convert('RGB');arr=np.array(im);w,h=im.size;wide=w/h>2;pw=420 if wide else 270;ph=280 if wide else 340
 canvas=Image.new('RGB',(pw*4,ph+140),'#f3f6fc');d=ImageDraw.Draw(canvas);d.text((14,10),prompt,font=font,fill='#10213b');note='Qualitative full frame: NO attribute ground truth' if expected is None else 'Expected main-person presence: '+str(expected)+' | NOT mask IoU';d.text((14,35),note,font=small,fill='#485e7b')
 for col,method in enumerate(['input']+methods):
  rgb=arr.copy();r=None
  if method!='input':
   mask=np.array(Image.open(folder/method/(key+'.png')))>0;r=next(x for x in rr if x['method']==method);assert mask.shape==(h,w)
   rgb[mask]=(.52*rgb[mask]+.48*np.array([255,105,45])).astype('uint8')
  panel=Image.fromarray(rgb)
  if method=='verified':
   pd=ImageDraw.Draw(panel)
   for feature in r['features']:pd.rectangle(feature['region'],outline='#00cbea',width=max(1,round(w/350)))
  scale=min((pw-16)/w,ph/h);panel=panel.resize((round(w*scale),round(h*scale)),Image.Resampling.NEAREST);canvas.paste(panel,(col*pw+(pw-panel.width)//2,65+(ph-panel.height)//2));d.text((col*pw+10,ph+78),names[col],font=font,fill='#10213b')
  if r:d.text((col*pw+10,ph+104),f"{r['request_s']:.3f}s shared GPU"+(' | mask' if np.array(Image.open(folder/method/(key+'.png'))).any() else ' | empty'),font=small,fill='#485e7b')
 canvas.save(V/(key+'.jpg'),quality=94)
for q in manifest['queries']:
 rr=[r for r in rows if r['id']==q['id']];figure(q['path'],q['id'],q['prompt'],rr,C,q['expected'])
for key in dict.fromkeys(r['key'] for r in full):
 rr=[r for r in full if r['key']==key];figure(rr[0]['image'],key,rr[0]['prompt'],rr,F)
for name,sha in lock['hashes'].items():assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==sha
old=json.loads(Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915/selected.json').read_text());oldids={s['source']['id'] for s in old};newids={s['source']['id'] for s in manifest['samples']};assert not(oldids&newids)
for s in manifest['samples']:assert hashlib.sha256(Path(s['path']).read_bytes()).hexdigest()==s['sha256']
for r in rows:
 mask=np.array(Image.open(C/r['method']/(r['id']+'.png')))>0;assert bool(mask.any())==r['nonempty']
 if r['method']=='verified':
  raw=np.array(Image.open(C/'proposal_only'/(r['id']+'.png')))>0;assert not(mask&~raw).any()
  for feature in r['features']:assert feature['accepted']==(feature['margin']>lock['selection'][r['attribute']]['threshold'])
ss=summary['results'];fulltime={m:float(np.mean([r['request_s'] for r in full if r['method']==m])) for m in methods};metrics=dict(verified_vs_original_time_ratio=ss['verified']['mean_s']/ss['original']['mean_s'],verified_vs_scale_time_ratio=ss['verified']['mean_s']/ss['scale704_guard']['mean_s'],positive_preservation_pass=ss['verified']['all']['tp']>=ss['original']['all']['tp'],references='Assistant-reviewed, exploratory, not native absence or mask annotations',shared_gpu=True,fullframe_mean_s=fulltime,fullframe_verified_vs_scale_ratio=fulltime['verified']/fulltime['scale704_guard'],fullframe_verified_vs_original_ratio=fulltime['verified']/fulltime['original'])
audit=dict(input_hashes_verified=True,method_sources_unchanged=True,old_identity_overlap=0,confirmation_masks_checked=len(rows),verified_masks_subset_of_proposals=True,metrics=metrics)
(R/'audit.json').write_text(json.dumps(audit,indent=2));(R/'web-data.json').write_text(json.dumps(dict(lock=lock,manifest=manifest,rows=rows,summary=summary,fullframe=full,audit=audit),indent=2));print(json.dumps(dict(summary=summary,audit=audit),indent=2))
