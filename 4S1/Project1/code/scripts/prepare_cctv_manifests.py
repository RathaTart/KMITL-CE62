import json,platform,hashlib,cv2
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw
from pycocotools import mask as mu
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_cctv_20260915';M=C.parent/'dataset/mots/extracted/MOTSChallenge/train'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,a):path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a.astype('uint8')*255).save(path);return str(path)
sets={'fit':[],'validation':[],'test':[]}
for seq,split,stride in [('0009','fit',10),('0002','test',10)]:
 frames=defaultdict(list)
 for line in (M/'instances_txt'/(seq+'.txt')).read_text().splitlines():
  fr,ident,cat,h,w,rle=line.split();frames[int(fr)].append((int(ident),int(cat),mu.decode({'size':[int(h),int(w)],'counts':rle.encode()})>0)) if (int(fr)-1)%stride==0 else None
 for fr,anns in sorted(frames.items()):
  people=[(ident,m) for ident,cat,m in anns if cat==2];ignore=np.logical_or.reduce([m for _,cat,m in anns if cat==10]) if any(cat==10 for _,cat,m in anns) else np.zeros(anns[0][2].shape,bool)
  if not people:continue
  itemid=f'mots_{seq}_{fr:06d}';image=M/'images'/seq/f'{fr:06d}.jpg';base=O/'inputs'/itemid;gt=np.logical_or.reduce([m for _,m in people]);ips=[save(base/f'instance_{ident}.png',m) for ident,m in people]
  sets[split].append(dict(key=itemid+'::expression',item_id=itemid,prompt_id='expression',image=str(image),image_sha256=sha(image),expression='all people',ground_truth=save(base/'gt.png',gt),ignore=save(base/'ignore.png',ignore),ground_truth_instances=ips,target_count=len(people),case_type='multi_target',domain='MOTS',source_group='MOTS_'+seq,frame=fr))
for uid,group,split,number in [('uid_vid_00144','VIRAT_student_union','validation',20),('uid_vid_00149','VIRAT_student_union','validation',20),('uid_vid_00147','VIRAT_courtyard','test',60)]:
 a=json.loads((O/'source'/(uid+'.json')).read_text());frames=defaultdict(list)
 for e in a['entities']:
  if 'frame_idx' in e.get('blob',{}):frames[int(e['blob']['frame_idx'])].append(e)
 keys=sorted(frames);chosen=[keys[j] for j in np.linspace(0,len(keys)-1,number).astype(int)];cap=cv2.VideoCapture(str(O/'source'/(uid+'.mp4')))
 for fr in chosen:
  cap.set(cv2.CAP_PROP_POS_FRAMES,fr);ok,im=cap.read();assert ok;h,w=im.shape[:2];assert (w,h)==(int(a['metadata']['resolution']['width']),int(a['metadata']['resolution']['height']))
  itemid=uid+f'_{fr:06d}';base=O/'inputs'/itemid;base.mkdir(parents=True,exist_ok=True);p=base/'image.png';cv2.imwrite(str(p),im);gt=[];ign=[]
  for e in frames[fr]:
   x,y,bw,bh=e['bb'];box=[max(0,x),max(0,y),min(w,x+bw),min(h,y+bh)];labels=e['labels']
   if labels.get('person') and not any(labels.get(k) for k in ['crowd','person_in_background','person_in_vehicle']):gt.append(dict(box=box,track=e['id'],labels=labels))
   else:ign.append(box)
  times=[e['time'] for e in frames[fr]];assert max(abs(t-fr/float(a['metadata']['fps'])*1000) for t in times)<100
  sets[split].append(dict(key=itemid+'::expression',item_id=itemid,prompt_id='expression',image=str(p),image_sha256=sha(p),expression='all people',boxes=gt,ignore_boxes=ign,target_count=len(gt),domain='PersonPath22',case_type='multi_target' if len(gt)>1 else 'single_in_crowd' if gt else 'no_target',source_group=group,source_video=uid,frame=fr,annotation_time_ms=times[0]))
  if fr==chosen[len(chosen)//2]:
   tile=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));dr=ImageDraw.Draw(tile)
   for b in gt:dr.rectangle(b['box'],outline='lime',width=2)
   tile.save(O/'source'/(uid+'_gt_review.png'))
 cap.release()
sets['fit']+=json.loads((C/'results/router_dev_20260915/manifest.json').read_text())['items']
sets['validation']+=json.loads((C/'results/router_confirm_20260915/manifest.json').read_text())['items']
for split,items in sets.items():
 p=O/(split+'_manifest.json');assert not p.exists();p.write_text(json.dumps(dict(items=items,status='Locked before prediction',selection='Fixed stride MOTS; evenly spaced annotated PersonPath22 keyframes; all people prompt; no synthetic segmentation labels'),indent=2))
print(json.dumps({k:len(v) for k,v in sets.items()},indent=2))
(O/'camera_audit.json').write_text(json.dumps(dict(train=['MOTS_0009'],validation=['VIRAT_student_union'],test=['MOTS_0002','VIRAT_courtyard'],visual_review='10%, 50%, 90% contact sheets show fixed viewpoints. VIRAT 010200 and 010201 grouped together despite distinct IDs.',limitations='Two test viewpoints only; daytime and shadow/occlusion/size stress; no night-generalization claim.'),indent=2))
