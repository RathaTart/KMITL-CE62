import platform
assert platform.node()=='cenara70hx'
import numpy as np,cv2
from PIL import Image
from scipy.optimize import linear_sum_assignment

def box_iou(a,b):
 x=max(a[0],b[0]);y=max(a[1],b[1]);w=max(0,min(a[2],b[2])-x);h=max(0,min(a[3],b[3])-y);inter=w*h
 return inter/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)
def components(mask):
 n,l,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8);return [(int(j),[int(x),int(y),int(x+w),int(y+h)]) for j,(x,y,w,h,area) in enumerate(stats) if j and area>=4],l

def metrics(i,mask):
 comps,labels=components(mask)
 if 'boxes' in i:
  gt=[g['box'] for g in i['boxes']];scores=np.array([[box_iou(p,g) for g in gt] for _,p in comps]).reshape(len(comps),len(gt));tp=0;matched=set()
  if scores.size:
   a,b=linear_sum_assignment(-scores)
   for x,y in zip(a,b):
    if scores[x,y]>=.5:tp+=1;matched.add(x)
  fp=0
  for j,(_,b) in enumerate(comps):
   if j in matched:continue
   area=max(1,(b[2]-b[0])*(b[3]-b[1]));ignored=any(max(0,min(b[2],ig[2])-max(b[0],ig[0]))*max(0,min(b[3],ig[3])-max(b[1],ig[1]))/area>.5 for ig in i.get('ignore_boxes',[]))
   fp+=not ignored
  return dict(tp=tp,fp=fp,fn=len(gt)-tp,gt=len(gt),empty=not mask.any(),small_gt=sum(g[3]-g[1]<64 for g in gt))
 gt=np.asarray(Image.open(i['ground_truth']))>0;valid=np.ones(gt.shape,bool)
 if i.get('ignore'):valid&=~(np.asarray(Image.open(i['ignore']))>0)
 assert gt.shape==mask.shape
 pred=mask&valid;gt=gt&valid;inter=int((pred&gt).sum());union=int((pred|gt).sum());covered=[];small=[]
 for p in i.get('ground_truth_instances',[]):
  g=(np.asarray(Image.open(p))>0)&valid;covered.append(float((g&pred).sum()/max(1,g.sum())));ys,xs=np.where(g);small.append(bool(len(ys) and ys.max()-ys.min()+1<64))
 return dict(iou=inter/union if union else 1.,intersection=inter,union=union,empty=not pred.any(),pixel_fp=int((pred&~gt).sum()),pixel_fn=int((gt&~pred).sum()),covered50=sum(v>=.5 for v in covered),target_instances=len(covered),instance_coverages=covered,small_instances=sum(small),small_covered50=sum(s and v>=.5 for s,v in zip(small,covered)))

def aggregate(rows):
 out={}
 for domain in ['gref','MOTS','PersonPath22']:
  rr=[r for r in rows if r['domain']==domain]
  if not rr:continue
  if domain=='PersonPath22':
   tp=sum(r['metrics']['tp'] for r in rr);fp=sum(r['metrics']['fp'] for r in rr);fn=sum(r['metrics']['fn'] for r in rr);out[domain]=dict(tp=tp,fp=fp,fn=fn,recall=tp/max(1,tp+fn),precision=tp/max(1,tp+fp),f2=5*tp/max(1,5*tp+4*fn+fp),n=len(rr))
  else:
   pos=[r for r in rr if r['target_count']>0];neg=[r for r in rr if r['target_count']==0];ms=[r['metrics'] for r in pos];total=sum(m['target_instances'] for m in ms);out[domain]=dict(positive_iou=float(np.mean([m['iou'] for m in ms])) if ms else None,no_target_accuracy=float(np.mean([r['metrics']['empty'] for r in neg])) if neg else None,positive_empty=sum(m['empty'] for m in ms),n=len(rr),instance_coverage_recall50=sum(m['covered50'] for m in ms)/max(1,total),target_instances=total,ciou=sum(m['intersection'] for m in ms)/max(1,sum(m['union'] for m in ms)),pixel_fp=sum(m['pixel_fp'] for m in ms),pixel_fn=sum(m['pixel_fn'] for m in ms),small_instance_recall50=sum(m['small_covered50'] for m in ms)/max(1,sum(m['small_instances'] for m in ms)),small_instances=sum(m['small_instances'] for m in ms))
 return out
