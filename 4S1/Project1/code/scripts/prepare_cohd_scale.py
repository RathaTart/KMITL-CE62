import json,hashlib,platform
from pathlib import Path
from collections import defaultdict
import cv2,numpy as np
from PIL import Image
from pycocotools import mask as mu
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');OLD=C/'results/cohd_cctv_20260915';OUT=C/'results/cohd_scale_20260915';OUT.mkdir(exist_ok=True)
old=json.loads((OLD/'test_manifest.json').read_text())['items']
dev=[i for domain in ['MOTS','PersonPath22'] for i in [x for x in old if x['domain']==domain][::5]]
def write(p,d):assert not p.exists();p.write_text(json.dumps(d,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,a):p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a.astype('uint8')*255).save(p);return str(p)
write(OUT/'dev_manifest.json',dict(items=dev,status='24 reused historical frames for method development only'))
print('dev locked',len(dev),flush=True)
M=C.parent/'dataset/mots/extracted/MOTSChallenge/train';frames=defaultdict(list);oldhash={i['image_sha256'] for i in old};oldkeys={i['key'] for i in old};items=[]
for line in (M/'instances_txt/0002.txt').read_text().splitlines():
 fr,ident,cat,h,w,rle=line.split();fr=int(fr)
 if (fr-5)%10==0:frames[fr].append((int(ident),int(cat),mu.decode({'size':[int(h),int(w)],'counts':rle.encode()})>0))
for fr,anns in sorted(frames.items()):
 people=[(ident,m) for ident,cat,m in anns if cat==2]
 if not people:continue
 ignore=np.logical_or.reduce([m for _,cat,m in anns if cat==10]) if any(cat==10 for _,cat,m in anns) else np.zeros(anns[0][2].shape,bool)
 ident=f'mots_0002_{fr:06d}';image=M/'images/0002'/f'{fr:06d}.jpg';base=OUT/'inputs'/ident;ips=[save(base/f'instance_{k}.png',m) for k,m in people]
 item=dict(key=ident+'::expression',item_id=ident,image=str(image),image_sha256=sha(image),expression='all people',ground_truth=save(base/'gt.png',np.logical_or.reduce([m for _,m in people])),ignore=save(base/'ignore.png',ignore),ground_truth_instances=ips,target_count=len(people),case_type='multi_target',domain='MOTS',source_group='MOTS_0002',frame=fr)
 assert item['key'] not in oldkeys and item['image_sha256'] not in oldhash
 items.append(item)
uid='uid_vid_00147';annotation=json.loads((OLD/'source'/(uid+'.json')).read_text());groups=defaultdict(list)
for e in annotation['entities']:
 if 'frame_idx' in e.get('blob',{}):groups[int(e['blob']['frame_idx'])].append(e)
oldframes={i['frame'] for i in old if i['domain']=='PersonPath22'};eligible=[k for k in sorted(groups) if k not in oldframes];chosen=[eligible[j] for j in np.linspace(0,len(eligible)-1,60).astype(int)];cap=cv2.VideoCapture(str(OLD/'source'/(uid+'.mp4')))
for fr in chosen:
 cap.set(cv2.CAP_PROP_POS_FRAMES,fr);ok,im=cap.read();assert ok;h,w=im.shape[:2];ident=uid+f'_{fr:06d}';base=OUT/'inputs'/ident;base.mkdir(parents=True,exist_ok=True);image=base/'image.png';cv2.imwrite(str(image),im);boxes=[];ignore=[]
 for e in groups[fr]:
  x,y,bw,bh=e['bb'];b=[max(0,x),max(0,y),min(w,x+bw),min(h,y+bh)];labels=e['labels']
  if labels.get('person') and not any(labels.get(k) for k in ['crowd','person_in_background','person_in_vehicle']):boxes.append(dict(box=b,track=e['id'],labels=labels))
  else:ignore.append(b)
 item=dict(key=ident+'::expression',item_id=ident,image=str(image),image_sha256=sha(image),expression='all people',boxes=boxes,ignore_boxes=ignore,target_count=len(boxes),domain='PersonPath22',case_type='multi_target' if len(boxes)>1 else 'single_in_crowd',source_group='VIRAT_courtyard',frame=fr)
 assert item['key'] not in oldkeys and item['image_sha256'] not in oldhash
 items.append(item)
cap.release();assert len({i['image_sha256'] for i in items})==len(items)
write(OUT/'confirmation_manifest.json',dict(items=items,status='Previously unscored frames, locked before inference; same explored camera views, temporally correlated, not unseen-camera test',exclusions='All prior test frame IDs and image hashes',sources={'MOTS':sha(M/'instances_txt/0002.txt'),'VIRAT':sha(OLD/'source'/(uid+'.json'))}))
print('confirmation locked',len(items),flush=True)
