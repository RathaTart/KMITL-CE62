"""Pre-LISA, pre-SAM routing features; no labels or LISA predictions are read."""
import re
import cv2
import numpy as np
from PIL import Image
ACTIONS=['LISA','YOLO_SAM','ZoomNeXt','intersection','union','empty']

def features(item,record):
    z=np.asarray(Image.open(item['zoom_mask']))>0;p=np.load(item['zoom_probability']).astype('float32');h,w=z.shape
    boxes=np.asarray(record.get('boxes',[]),dtype=float).reshape(-1,4);scores=np.asarray(record.get('scores',[]),dtype=float);b=np.zeros_like(z)
    for x1,y1,x2,y2 in boxes:
        b[max(0,int(y1)):min(h,int(y2)+1),max(0,int(x1)):min(w,int(x2)+1)]=True
    area=lambda m:float(m.mean());iou=float((b&z).sum()/max(1,(b|z).sum()));n,labels,stats,_=cv2.connectedComponentsWithStats(z.astype('uint8'),8)
    sizes=stats[1:,cv2.CC_STAT_AREA] if n>1 else np.array([0]);s=np.sort(scores)[::-1];areas=(boxes[:,2]-boxes[:,0])*(boxes[:,3]-boxes[:,1])/(h*w) if len(boxes) else np.array([0.])
    q=item['expression'].lower();out={'n_boxes':len(boxes),'score_max':float(s[0]) if len(s) else 0.,'score_mean':float(s.mean()) if len(s) else 0.,'score_gap':float(s[0]-s[1]) if len(s)>1 else float(s[0]) if len(s) else 0.,'score_min':float(s[-1]) if len(s) else 0.,'box_area':area(b),'zoom_area':area(z),'box_zoom_iou':iou,'zoom_in_boxes':float((b&z).sum()/max(1,z.sum())),'box_in_zoom':float((b&z).sum()/max(1,b.sum())),'area_ratio':area(z)/max(area(b),1/(h*w)),'largest_box':float(areas.max()),'mean_box':float(areas.mean()),'zoom_components':int((sizes>=h*w*.0005).sum()),'zoom_largest_fraction':float(sizes.max()/max(1,z.sum())),'zoom_ambiguous_fraction':float(((p>.25)&(p<.75)).mean()),'zoom_mean':float(p.mean()),'zoom_std':float(p.std()),'zoom_box_mean':float(p[b].mean()) if b.any() else 0.,'words':len(q.split()),'chars':len(q),'aspect':w/h}
    patterns={'plural':r'\b(all|both|two|three|four|people|men|women|boys|girls|players)\b|\band\b','relative':r'\b(next|beside|behind|between|front|left of|right of)\b','direction':r'\b(left|right|middle|center|top|bottom)\b','color':r'\b(red|blue|green|black|white|yellow|pink|orange|purple|brown|grey|gray)\b','clothing':r'\b(shirt|hat|jacket|coat|pants|dress|shorts|wearing)\b','action':r'\b(sitting|standing|running|walking|holding|looking|riding)\b','occlusion':r'\b(part|hidden|back|small|far)\b','negation':r'\b(not|no|without)\b'}
    out.update({k:float(bool(re.search(v,q))) for k,v in patterns.items()})
    if 'presence_probability' in item:out.update(presence_probability=float(item['presence_probability']),presence_logit=float(item['presence_logit']))
    return out

def action_mask(action,lisa,yolo,zoom):
    return lisa if action==0 else yolo if action==1 else zoom if action==2 else yolo&zoom if action==3 else yolo|zoom if action==4 else np.zeros_like(zoom)

def training_free_action(f,cfg):
    # Zoom-only gate intentionally tests the user's suggested visual difficulty proxy.
    if cfg['family']=='zoom':ok=f['zoom_ambiguous_fraction']<=cfg['ambiguity'] and f['zoom_components']<=cfg['components']
    else:ok=f['box_zoom_iou']>=cfg['agreement'] and f['score_max']>=cfg['score'] and f['n_boxes']<=cfg['boxes'] and f['words']<=cfg['words']
    if cfg.get('simple') and (f['relative'] or f['plural']):ok=False
    if cfg.get('empty') and f['n_boxes']==0 and f['zoom_area']<.01:return 5
    return cfg['action'] if ok else 0
