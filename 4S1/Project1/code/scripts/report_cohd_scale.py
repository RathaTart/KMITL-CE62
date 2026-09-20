"""Remote-only numerical audit and deterministic saved-result visualizations."""
import json,platform,hashlib,textwrap
from pathlib import Path
assert platform.node()=='cenara70hx'
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from scipy.optimize import linear_sum_assignment
from cctv_eval_utils import components,box_iou
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_scale_20260915'
lock=json.loads((O/'method_lock.json').read_text());methods=['original']+lock['selected'];names={'original':'Original CoHD','scale768_guard':'Scale 768 + guard','scale704_guard':'Scale 704 + guard','center_guard':'Full + center crop'}
def read(p):return json.loads(p.read_text())
def size_scores(i,mask):
 boxes=[g['box'] for g in i['boxes']];comp,_=components(mask);scores=np.array([[box_iou(p,g) for g in boxes] for _,p in comp]).reshape(len(comp),len(boxes));matched=set()
 if scores.size:
  a,b=linear_sum_assignment(-scores);matched={int(y) for x,y in zip(a,b) if scores[x,y]>=.5}
 return {name:dict(gt=sum(low<=g[3]-g[1]<hi for g in boxes),tp=sum(j in matched and low<=g[3]-g[1]<hi for j,g in enumerate(boxes))) for name,low,hi in [('under32',0,32),('32to63',32,64),('64plus',64,100000)]}
summary={};allitems={};allresults={}
for stage,manifest in [('confirmation','confirmation_manifest.json'),('language','language_manifest.json')]:
 items=read(O/manifest)['items'];records=read(O/stage/'per_image.json');allitems[stage]=items;allresults[stage]=records;stage_out=dict(measured_summary=read(O/stage/'summary.json'),methods={})
 for method in methods:
  rows={r['key']:r for r in records[method]};size={};lang={}
  for i in items:
   r=rows[i['key']];mask=np.asarray(Image.open(r['mask']))>0
   if 'boxes' in i:
    for key,counts in size_scores(i,mask).items():
     dst=size.setdefault(key,dict(gt=0,tp=0))
     for f,value in counts.items():dst[f]+=value
   if stage=='language':
    g=lang.setdefault(i['attribute_group'],dict(n=0,ious=[],target_hit=0,target_total=0,distractor_hit=0,distractor_total=0,empty=0));g['n']+=1;g['ious'].append(r['metrics']['iou']);g['empty']+=not mask.any()
    for field in ['target','distractor']:
     paths=i['ground_truth_instances'] if field=='target' else i['distractor_instances']
     for path in paths:
      gt=np.asarray(Image.open(path))>0;g[field+'_hit']+=int((gt&mask).sum()/max(1,gt.sum())>=.5);g[field+'_total']+=1
  for g in lang.values():g['mean_iou']=float(np.mean(g.pop('ious')))
  stage_out['methods'][method]=dict(size=size,language=lang)
 base={r['key']:r for r in records['original']};rng=np.random.default_rng(2026091517);n=len(items);indices=rng.integers(0,n,(10000,n));b=np.array([base[i['key']]['request_s'] for i in items])
 stage_out['paired_runtime']={}
 for method in methods[1:]:
  rr={r['key']:r for r in records[method]};x=np.array([rr[i['key']]['request_s'] for i in items]);stage_out['paired_runtime'][method]=dict(relative_overhead=float(x.mean()/b.mean()-1),image_bootstrap_ci95=np.quantile(x[indices].mean(1)/b[indices].mean(1)-1,[.025,.975]).tolist(),note='Within-run timing uncertainty only, not independent-camera inference')
 summary[stage]=stage_out
# Original baseline audit against the historical masks on development.
historical=read(C/'results/cohd_cctv_20260915/test_results/per_expression.json')['original'];historical={r['key']:r for r in historical};development=read(O/'dev_adapt/per_image.json')['original'];equal=[]
for r in development:
 old=historical[r['key']];equal.append(np.array_equal(np.asarray(Image.open(old['mask'])),np.asarray(Image.open(r['mask']))))
summary['audit']=dict(original_development_masks_equal=sum(equal),original_development_masks_checked=len(equal),language_upstream_train_overlap=sum(i['in_upstream_gref_train'] for i in allitems['language']),confirmation_hash_overlap_with_dev=len({i['image_sha256'] for i in read(O/'dev_manifest.json')['items']}&{i['image_sha256'] for i in allitems['confirmation']}),warning='Confirmation uses previously unscored frames from explored fixed-camera videos; language diagnostic uses reused COCO images. No unseen-camera or CCTV-hat claim.')
(O/'analysis.json').write_text(json.dumps(summary,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16);bold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
E=O/'examples';E.mkdir(exist_ok=True);example_rows=[]
def overlay(im,mask,color):
 arr=np.asarray(im).copy();arr[mask]=(arr[mask]*.55+np.asarray(color)*.45).astype('uint8');return Image.fromarray(arr)
def panel(image,width=390,height=260):
 copy=image.copy();copy.thumbnail((width,height));dest=Image.new('RGB',(width,height),'#102034');dest.paste(copy,((width-copy.width)//2,(height-copy.height)//2));return dest
for stage in ['confirmation','language']:
 items=allitems[stage];chosen=[]
 if stage=='confirmation':
  for domain in ['MOTS','PersonPath22']:
   group=[i for i in items if i['domain']==domain];chosen.extend(group[int((len(group)-1)*q)] for q in [.25,.5,.75])
 else:
  for attr in ['hat','clothing','absent']:
   group=[i for i in items if i['attribute_group']==attr];chosen.extend([group[0],group[len(group)//2]])
 for i in chosen:
  im=Image.open(i['image']).convert('RGB');w,h=im.size;gt=np.asarray(Image.open(i['ground_truth']))>0 if 'ground_truth' in i else None;reference=overlay(im,gt,(0,220,120)) if gt is not None else im.copy();rd=ImageDraw.Draw(reference);boxes=[g['box'] for g in i.get('boxes',[])]
  if gt is None:
   for b in boxes:rd.rectangle(b,outline='#00dc78',width=2)
  if not boxes:
   for p in i.get('ground_truth_instances',[]):
    ys,xs=np.where(np.asarray(Image.open(p))>0)
    if len(ys):boxes.append([int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)])
  eligible=[b for b in boxes if b[3]-b[1]>=12];b=min(eligible,key=lambda b:(b[3]-b[1])*(b[2]-b[0])) if eligible else [w*.3,h*.3,w*.7,h*.7];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;ww=max(40,(b[2]-b[0])*2);hh=max(40,(b[3]-b[1])*2);crop=(max(0,int(cx-ww/2)),max(0,int(cy-hh/2)),min(w,int(cx+ww/2)),min(h,int(cy+hh/2)))
  cols=[('Human reference',reference,'GT mask / visible-person boxes')];scores={}
  for method in methods:
   r=next(r for r in allresults[stage][method] if r['key']==i['key']);mask=np.asarray(Image.open(r['mask']))>0;met=r['metrics'];score=f'IoU {met["iou"]*100:.2f}%' if 'iou' in met else f'TP {met["tp"]}/{met["gt"]} | FP {met["fp"]} | FN {met["fn"]}';score+=f' | {r["request_s"]:.3f}s';cols.append((names.get(method,method),overlay(im,mask,(255,112,45)),score));scores[method]=dict(metrics=met,request_s=r['request_s'])
  canvas=Image.new('RGB',(390*len(cols),650),'white');draw=ImageDraw.Draw(canvas);title=i['expression'];draw.text((12,8),stage.upper()+' | '+i['item_id'],fill='black',font=bold)
  for j,line in enumerate(textwrap.wrap(title,140)[:2]):draw.text((12,35+j*19),line,fill='#203650',font=font)
  for j,(label,img,score) in enumerate(cols):
   x=j*390;draw.text((x+10,80),label,fill='black',font=bold);marked=img.copy();ImageDraw.Draw(marked).rectangle(crop,outline='#00bcd4',width=2);canvas.paste(panel(marked),(x,108));zoom=img.crop(crop);zoom.thumbnail((390,210)) if zoom.width>390 or zoom.height>210 else None
   # Enlarge the crop for inspection; this does not change inference or scoring.
   scale=min(390/zoom.width,210/zoom.height);zoom=zoom.resize((max(1,round(zoom.width*scale)),max(1,round(zoom.height*scale))),Image.Resampling.NEAREST);canvas.paste(panel(zoom,390,210),(x,380))
   for k,line in enumerate(textwrap.wrap(score,42)):draw.text((x+8,600+k*19),line,fill='#12304f',font=font)
  name=i['item_id']+'.png';canvas.save(E/name);example_rows.append(dict(stage=stage,item_id=i['item_id'],expression=i['expression'],file=name,scores=scores,selection='Fixed quantile CCTV frames; first and middle native expressions per language group. Cyan GT-selected zoom is visualization only.'))
(O/'examples.json').write_text(json.dumps(example_rows,indent=2));print(json.dumps(summary,indent=2),flush=True)
