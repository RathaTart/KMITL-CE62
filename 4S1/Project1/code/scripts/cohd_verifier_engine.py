import json,sys,types,os,time,hashlib,platform,argparse
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/released-models');C=Path('/home/osta/lisa-eval/code');sys.path.insert(0,str(R/'CoHD'))
# Upstream ships a mathematically equivalent PyTorch fallback; CUDA toolkit is unavailable.
shim=types.ModuleType('MultiScaleDeformableAttention')
def unavailable(*args):raise RuntimeError('Use upstream PyTorch deformable attention fallback')
shim.ms_deform_attn_forward=unavailable;sys.modules['MultiScaleDeformableAttention']=shim
from detectron2.config import get_cfg
from detectron2.projects.deeplab import add_deeplab_config
from detectron2.modeling import build_model
from transformers import BertModel,BertConfig,BertTokenizer
import requests
bert=R/'weights/bert-base-uncased';bert.mkdir(exist_ok=True)
for name in ['config.json','vocab.txt','tokenizer_config.json']:
 p=bert/name
 if not p.exists():
  res=requests.get('https://huggingface.co/google-bert/bert-base-uncased/resolve/main/'+name,timeout=60);res.raise_for_status();p.write_bytes(res.content)
# All BERT tensors are restored from the released CoHD checkpoint, verified strictly below.
BertModel.from_pretrained=classmethod(lambda cls,*a,**kw:cls(BertConfig.from_pretrained(bert)))
from gres_model import add_maskformer2_config,add_refcoco_config
torch.set_num_threads(4);torch.manual_seed(20260915)
cfg=get_cfg();add_deeplab_config(cfg);add_maskformer2_config(cfg);add_refcoco_config(cfg);cfg.merge_from_file(str(R/'CoHD/configs/referring_swin_tiny_eval.yaml'));cfg.REFERRING.BERT_TYPE=str(bert);cfg.MODEL.WEIGHTS='';cfg.MODEL.DEVICE='cuda'
t=time.perf_counter();model=build_model(cfg);ck=R/'weights/CoHD_CoHD_grefcoco_swin_tiny.pth';state=torch.load(ck,map_location='cpu',weights_only=True);print('checkpoint keys',list(state)[:8],flush=True);state=state.get('model',state);loaded=model.load_state_dict(state,strict=True);del state;model.eval();tokenizer=BertTokenizer.from_pretrained(bert);load_s=time.perf_counter()-t

from detectron2.data.transforms import ResizeTransform
class CoHDVerifier:
 def __init__(self, lock_path):
  import pickle
  self.lock=json.loads(Path(lock_path).read_text());self.selected=self.lock['selected']['primary'];self.head=None
  if self.selected['name']!='threshold':self.head=pickle.loads(Path(self.selected['checkpoint']).read_bytes())
  self.captured={};self.handle=None
 def enable_features(self,enabled):
  if self.handle is not None:self.handle.remove();self.handle=None
  if enabled and self.head is not None:
   self.handle=model.sem_seg_head.predictor.mask_embed.register_forward_pre_hook(lambda module,args:self.captured.update(embedding=args[0].detach().mean(dim=(0,2)).flatten()))
 def predict(self,image_path,expression,modified=True):
  self.enable_features(modified);torch.cuda.synchronize();start=time.perf_counter()
  im=np.asarray(Image.open(image_path).convert('RGB'));h,w=im.shape[:2];size=cfg.INPUT.IMAGE_SIZE
  img=ResizeTransform(h,w,size,size).apply_image(im if cfg.INPUT.FORMAT=='RGB' else im[:,:,::-1])
  ids=tokenizer.encode(expression,add_special_tokens=True)[:cfg.REFERRING.MAX_TOKENS];tokens=ids+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));attn=[1]*len(ids)+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids))
  data=dict(image=torch.as_tensor(np.ascontiguousarray(img.transpose(2,0,1))),lang_tokens=torch.tensor([tokens]),lang_mask=torch.tensor([attn]),height=h,width=w)
  with torch.inference_mode():
   out=model([data])[0];nt=bool(out['nt_label'].argmax(dim=0));score=None
   if modified:
    if self.head is None:
     scores=out['nt_label'];score=float(scores[1]/(scores[0]+scores[1]+1e-12))
    else:
     margin=out['ref_seg'][1]-out['ref_seg'][0];prob=margin.sigmoid();fg=margin>0
     stats=torch.stack([prob.mean(),prob.std(),fg.float().mean(),prob[fg].mean() if fg.any() else prob.new_zeros(()),prob.max(),margin.mean(),margin.std()])
     x=torch.cat([out['nt_label'].flatten(),out['count_pred'].flatten(),stats,self.captured['embedding']]).cpu().numpy()
     score=float(self.head['model'].predict_proba(x[None,:self.head['dim']])[0,1])
    nt=score>=self.selected['threshold']
   native=out['ref_seg'].argmax(0).byte().cpu().numpy()
  mask=np.asarray(Image.fromarray(native).resize((w,h),Image.Resampling.NEAREST))>0
  if nt:mask[:]=False
  torch.cuda.synchronize()
  return mask,dict(no_target=nt,verifier_score=score,request_s=time.perf_counter()-start)
