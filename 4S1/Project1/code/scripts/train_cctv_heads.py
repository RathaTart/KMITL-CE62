"""Tune existing CoHD prediction layers with frozen cached inputs."""
import json,copy,hashlib,random,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from cohd_verifier_engine import model,C
from cctv_eval_utils import metrics,aggregate
O=C/'results/cohd_cctv_20260915';P=model.sem_seg_head.predictor
for p in model.parameters():p.requires_grad_(False)
modules=['mask_embed','class_embed','dha'];params=[]
for name in modules:
 for p in getattr(P,name).parameters():p.requires_grad_(True);params.append(p)
initial={name:copy.deepcopy(getattr(P,name).state_dict()) for name in modules};torch.manual_seed(20260915);rng=random.Random(20260915)
def load(split):
 items=json.loads((O/(split+'_manifest.json')).read_text())['items'];idx={r['key']:r['cache'] for r in json.loads((O/('cache_'+split)/'index.json').read_text())};return [(i,torch.load(idx[i['key']],map_location='cpu',weights_only=True)) for i in items]
fit=load('fit');val=load('validation')
def logits(b):
 q=b['queries'].cuda();attns=[v.cuda() for v in b['attns']];kernels=P.class_embed(P.mask_embed(q));return F.interpolate(P.dha(attns,list(q.unbind(0)),kernels,weights=P.weights)[-1],size=(480,480),mode='bilinear',align_corners=False)[0]
def evaluate(tag,baseline=False):
 rows=[]
 with torch.no_grad():
  for i,b in val:
   lo=b['teacher'] if baseline else logits(b).cpu();native=lo.argmax(0).byte().numpy();w,h=Image.open(i['image']).size;mask=np.asarray(Image.fromarray(native).resize((w,h),Image.Resampling.NEAREST))>0
   if bool(b['nt'].argmax()):mask[:]=False
   rows.append(dict(key=i['key'],domain=i.get('domain','gref'),target_count=i['target_count'],metrics=metrics(i,mask)))
 return dict(tag=tag,summary=aggregate(rows),rows=rows)
base=evaluate('baseline',True);results=[base];opt=torch.optim.AdamW(params,lr=1e-5,weight_decay=.01);steps=0
for epoch in range(1,5):
 rng.shuffle(fit);losses=[];opt.zero_grad()
 for j,(i,b) in enumerate(fit):
  lo=logits(b);g=np.asarray(Image.open(i['ground_truth']).resize((480,480),Image.Resampling.NEAREST))>0;target=torch.from_numpy(g.astype('int64')).cuda();valid=torch.ones_like(target,dtype=torch.bool)
  if i.get('ignore'):valid=~torch.from_numpy(np.asarray(Image.open(i['ignore']).resize((480,480),Image.Resampling.NEAREST))>0).cuda()
  ce=F.cross_entropy(lo[None],target[None],weight=lo.new_tensor([1.,2.]),reduction='none')[0];prob=lo.softmax(0)[1];t=target.float();tp=(prob*t*valid).sum();fp=(prob*(1-t)*valid).sum();fn=((1-prob)*t*valid).sum();tv=1-(tp+1)/(tp+.3*fp+.7*fn+1)
  loss=ce[valid].mean()+tv
  if i.get('domain','gref')=='gref':
   teacher=b['teacher'].cuda().softmax(0);loss=loss+.1*F.kl_div(lo.log_softmax(0),teacher,reduction='none').sum(0)[valid].mean()
  (loss/4).backward();losses.append(float(loss.detach()))
  if (j+1)%4==0 or j==len(fit)-1:torch.nn.utils.clip_grad_norm_(params,1.);opt.step();opt.zero_grad();steps+=1
  if (j+1)%50==0:print('epoch',epoch,'item',j+1,'loss',float(np.mean(losses[-50:])),flush=True)
 if epoch in [1,2,4]:
  result=evaluate('epoch_'+str(epoch));path=O/('customA_epoch_'+str(epoch)+'.pt');torch.save({name:getattr(P,name).state_dict() for name in modules},path);result['checkpoint']=str(path);result['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();results.append(result);print(json.dumps(dict(epoch=epoch,summary=result['summary'])),flush=True)
bg=base['summary']['gref'];bv=base['summary']['PersonPath22'];eligible=[]
for r in results[1:]:
 g=r['summary']['gref'];v=r['summary']['PersonPath22'];r['eligible']=g['positive_iou']>=bg['positive_iou']-.01 and g['no_target_accuracy']>=bg['no_target_accuracy'] and v['precision']>=bv['precision']-.02
 if r['eligible']:eligible.append(r)
selected=max(eligible,key=lambda r:r['summary']['PersonPath22']['f2']) if eligible else max(results[1:],key=lambda r:r['summary']['PersonPath22']['f2'])
lock=dict(primary=selected['tag'],checkpoint=selected['checkpoint'],sha256=selected['sha256'],passed_validation_constraints=bool(eligible),trainable_parameters=sum(p.numel() for p in params),modules=modules,learning_rate=1e-5,epochs=4,selected_epochs=[1,2,4],train_items=len(fit),validation_items=len(val),selection='Max validation box F2 with <=1pp gref positive loss, no negative accuracy loss, <=2pp box precision loss; if none eligible retain best F2 as failed-constraint experimental candidate',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),test_used=False)
assert not (O/'customA_lock.json').exists();(O/'customA_lock.json').write_text(json.dumps(lock,indent=2));(O/'customA_validation.json').write_text(json.dumps(results,indent=2));print(json.dumps(lock,indent=2))
