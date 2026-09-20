"""Remote-only fixed-weight scale/precision controls. No ground truth in inference."""
import time,contextlib
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import cv2
from cohd_verifier_engine import model,cfg,tokenizer,ResizeTransform

VARIANTS={
 'original':dict(size=480,amp=False,tiles=False),
 'fp32_640':dict(size=640,amp=False,tiles=False),
 'amp_480':dict(size=480,amp=True,tiles=False),
 'amp_640':dict(size=640,amp=True,tiles=False),
 'amp_768':dict(size=768,amp=True,tiles=False),
 'tiles_amp256':dict(size=256,amp=True,tiles=True),
 'tiles_amp320':dict(size=320,amp=True,tiles=True),
 'full_tiles_amp256':dict(size=256,amp=True,tiles=True,full=True),
 'adapt_amp640':dict(size=640,amp=True,tiles=False,adapter=True),
 'adapt_amp768':dict(size=768,amp=True,tiles=False,adapter=True),
 'adapt_tiles256':dict(size=256,amp=True,tiles=True,adapter=True),
 'adapt_tiles320':dict(size=320,amp=True,tiles=True,adapter=True),
 'full_top_amp480':dict(size=480,amp=True,tiles=False,roi='top'),
 'full_center_amp480':dict(size=480,amp=True,tiles=False,roi='center'),
 'scale768_guard':dict(size=768,amp=True,tiles=False,adapter=True,shape=[20,1.2]),
 'adapt_amp704':dict(size=704,amp=True,tiles=False,adapter=True),
 'scale704_guard':dict(size=704,amp=True,tiles=False,adapter=True,shape=[20,1.2]),
 'center_guard':dict(size=480,amp=True,tiles=False,roi='center',shape=[20,.8]),
}

def grid_hook(module,args):
 x=args[0];expected=module.layers[0].in_features
 if x.shape[-1]==expected:return args
 side=int(round(x.shape[-1]**.5));dest=int(round(expected**.5));assert side*side==x.shape[-1] and dest*dest==expected
 # Adapt the spatial projection input only, keeping the high-resolution attention maps.
 b,q,_=x.shape;y=F.interpolate(x.reshape(b,q,side,side),size=(dest,dest),mode='bilinear',align_corners=False).flatten(2)
 return (y,)+args[1:]

def predict(path,text,variant):
 v=VARIANTS[variant];torch.cuda.synchronize();start=time.perf_counter()
 im=np.asarray(Image.open(path).convert('RGB'));h,w=im.shape[:2]
 ids=tokenizer.encode(text,add_special_tokens=True)[:cfg.REFERRING.MAX_TOKENS];n=cfg.REFERRING.MAX_TOKENS
 tokens=torch.tensor([ids+[0]*(n-len(ids))]);attn=torch.tensor([[1]*len(ids)+[0]*(n-len(ids))])
 if v['tiles']:
  cw=int(round(w*.55));ch=int(round(h*.55));regions=[(x,y,x+cw,y+ch) for y in [0,h-ch] for x in [0,w-cw]]
  if v.get('full'):regions=[(0,0,w,h)]+regions
 else:regions=[(0,0,w,h)]
 if v.get('roi')=='top':regions.append((0,0,w,int(round(h*.55))))
 if v.get('roi')=='center':regions.append((int(w*.2),int(h*.2),int(w*.8),int(h*.8)))
 inputs=[]
 for x1,y1,x2,y2 in regions:
  crop=im[y1:y2,x1:x2];hh,ww=crop.shape[:2];size=v['size']
  img=ResizeTransform(hh,ww,size,size).apply_image(crop if cfg.INPUT.FORMAT=='RGB' else crop[:,:,::-1])
  inputs.append(dict(image=torch.as_tensor(np.ascontiguousarray(img.transpose(2,0,1))),lang_tokens=tokens,lang_mask=attn,height=hh,width=ww))
 handles=[]
 if v.get('adapter'):
  for m in model.modules():
   if m.__class__.__name__=='SDM_Attention':handles.append(m.out_proj.register_forward_pre_hook(grid_hook))
 try:
  with torch.inference_mode(),torch.autocast(device_type='cuda',dtype=torch.float16,enabled=v['amp']):outputs=model(inputs)
 finally:
  for handle in handles:handle.remove()
 result=np.zeros((h,w),bool);decisions=[]
 for o,(x1,y1,x2,y2) in zip(outputs,regions):
  assert torch.isfinite(o['ref_seg']).all() and torch.isfinite(o['nt_label']).all(),'Non-finite output'
  nt=bool(o['nt_label'].argmax());decisions.append(nt)
  mask=o['ref_seg'].argmax(0).byte().cpu().numpy()
  if not nt:result[y1:y2,x1:x2]|=np.asarray(Image.fromarray(mask).resize((x2-x1,y2-y1),Image.Resampling.NEAREST))>0
 if v.get('shape'):
  minheight,ratio=v['shape'];n,labels,stats,_=cv2.connectedComponentsWithStats(result.astype('uint8'),8);keep=np.zeros(n,bool)
  for j,(x,y,ww,hh,area) in enumerate(stats):
   if j:keep[j]=area>=4096 or (hh>=minheight and ww/max(1,hh)<=ratio)
  result=keep[labels]
 torch.cuda.synchronize()
 return result,dict(request_s=time.perf_counter()-start,passes=len(inputs),no_target=all(decisions),peak_bytes=torch.cuda.max_memory_allocated())
