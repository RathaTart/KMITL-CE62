"""Full-image inference with original, existing-head adaptation, or verifier."""
import json,pickle,time,copy
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from cohd_verifier_engine import model,cfg,tokenizer,C,ResizeTransform
O=C/'results/cohd_cctv_20260915'
class CCTVEngine:
 def __init__(self):
  self.a=json.loads((O/'customA_lock.json').read_text());self.b=json.loads((O/'customB_lock.json').read_text());self.head=pickle.loads(Path(self.b['checkpoint']).read_bytes());self.custom=torch.load(self.a['checkpoint'],map_location='cpu',weights_only=True);self.original={name:{k:v.detach().cpu().clone() for k,v in getattr(model.sem_seg_head.predictor,name).state_dict().items()} for name in self.custom};self.mode='original';self.handle=None;self.captured={}
 def prepare_mode(self,mode,features):
  weights_mode='original' if mode=='original' else 'custom'
  if weights_mode!=self.mode:
   for name,state in (self.original if weights_mode=='original' else self.custom).items():getattr(model.sem_seg_head.predictor,name).load_state_dict(state,strict=True)
   self.mode=weights_mode
  if self.handle:self.handle.remove();self.handle=None
  if features or mode=='customB':self.handle=model.sem_seg_head.predictor.mask_embed.register_forward_pre_hook(lambda m,a:self.captured.update(q=a[0].detach().mean(dim=(0,2)).flatten()))
 def predict(self,path,text,mode,features=False):
  self.prepare_mode(mode,features);torch.cuda.synchronize();start=time.perf_counter();im=np.asarray(Image.open(path).convert('RGB'));h,w=im.shape[:2];size=cfg.INPUT.IMAGE_SIZE;img=ResizeTransform(h,w,size,size).apply_image(im if cfg.INPUT.FORMAT=='RGB' else im[:,:,::-1]);ids=tokenizer.encode(text,add_special_tokens=True)[:cfg.REFERRING.MAX_TOKENS];tokens=ids+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));attn=[1]*len(ids)+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));data=dict(image=torch.as_tensor(np.ascontiguousarray(img.transpose(2,0,1))),lang_tokens=torch.tensor([tokens]),lang_mask=torch.tensor([attn]),height=h,width=w)
  with torch.inference_mode():
   out=model([data])[0];nt=bool(out['nt_label'].argmax());x=None
   if features or mode=='customB':
    margin=out['ref_seg'][1]-out['ref_seg'][0];prob=margin.sigmoid();fg=margin>0;stats=torch.stack([prob.mean(),prob.std(),fg.float().mean(),prob[fg].mean() if fg.any() else prob.new_zeros(()),prob.max(),margin.mean(),margin.std()]);x=torch.cat([out['nt_label'].flatten(),out['count_pred'].flatten(),stats,self.captured['q']]).cpu().numpy()
   score=None
   if mode=='customB':score=float(self.head['model'].predict_proba(x[None])[0,1]);nt=score>=self.head['threshold']
   native=out['ref_seg'].argmax(0).byte().cpu().numpy();raw=np.asarray(Image.fromarray(native).resize((w,h),Image.Resampling.NEAREST))>0;mask=np.zeros_like(raw) if nt else raw
  torch.cuda.synchronize();elapsed=time.perf_counter()-start
  return mask,dict(request_s=elapsed,no_target=nt,verifier_score=score),x,raw
