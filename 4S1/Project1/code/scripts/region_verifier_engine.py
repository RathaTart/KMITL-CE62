"""Frozen person proposal + spatial CLIP verification; remote inference only.

Supports hat and black upper clothing only. Connected components are approximate
person proposals, not an instance detector. No ground truth is read here.
"""
import platform,time,json
from pathlib import Path
assert platform.node()=='cenara70hx'
import numpy as np,cv2,torch
from PIL import Image
from transformers import CLIPModel,CLIPProcessor
from cohd_scale_engine import predict as cohd_predict
WEIGHTS=Path('/home/osta/lisa-eval/released-models/weights/clip-vit-base-patch32')
COLORS=['black','white','gray','blue','red','brown','green','yellow','pink','purple','orange']
HAT=['a person wearing a hat','a person wearing a baseball cap','a person wearing a knitted beanie','a person with uncovered hair','a person wearing a hood']
COLOR_TEXT=[f'a person wearing a {c} {item}' for c in COLORS for item in ['coat','jacket','top']]
class RegionVerifier:
 def __init__(self):
  self.clip=CLIPModel.from_pretrained(WEIGHTS,local_files_only=True,torch_dtype=torch.float16).to('cuda').eval();self.processor=CLIPProcessor.from_pretrained(WEIGHTS,local_files_only=True)
  text=self.processor(text=HAT+COLOR_TEXT,return_tensors='pt',padding=True).to('cuda')
  with torch.inference_mode():features=self.clip.get_text_features(**text).float();features=features/features.norm(dim=-1,keepdim=True)
  self.hat=features[:len(HAT)];color=features[len(HAT):].reshape(len(COLORS),3,-1).mean(1);self.color=color/color.norm(dim=-1,keepdim=True)
 def propose(self,path,main_person=True):
  mask,meta=cohd_predict(path,'all people','scale704_guard');n,labels,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'),8)
  # Small predictions remain eligible; cap is a declared latency limit, not GT filtering.
  order=sorted(range(1,n),key=lambda j:int(stats[j,4]),reverse=True)[:1 if main_person else 8]
  boxes=[list(map(int,stats[j,:4])) for j in order]
  return mask,labels,order,boxes,meta
 def features(self,image,boxes,attribute,modes):
  crops=[];keys=[];W,H=image.size
  for j,(x,y,w,h) in enumerate(boxes):
   for mode in modes:
    a,b=(0.,1.) if mode=='whole' else ((0.,.42) if attribute=='hat' else (.20,.75))
    box=(max(0,x-round(w*.05)),max(0,y+int(h*a)),min(W,x+w+round(w*.05)),min(H,y+max(int(h*b),int(h*a)+1)))
    crops.append(image.crop(box));keys.append((j,mode,box))
  if not crops:return []
  inputs=self.processor(images=crops,return_tensors='pt')['pixel_values'].to('cuda',dtype=torch.float16)
  with torch.inference_mode():z=self.clip.get_image_features(pixel_values=inputs).float();z=z/z.norm(dim=-1,keepdim=True);scores=z@(self.hat if attribute=='hat' else self.color).T
  scores=scores.cpu().numpy();result=[]
  for key,s in zip(keys,scores):
   margin=float(max(s[:3])-max(s[3:])) if attribute=='hat' else float(s[0]-max(s[1:]))
   result.append(dict(candidate=key[0],mode=key[1],region=list(key[2]),margin=margin,similarities=s.tolist()))
  return result
 def predict(self,path,attribute,selection,main_person=True):
  if attribute not in ['hat','black_coat']:raise ValueError('Supported attributes: hat, black_coat')
  torch.cuda.synchronize();start=time.perf_counter();mask,labels,ids,boxes,meta=self.propose(path,main_person);image=Image.open(path).convert('RGB')
  rule=selection[attribute];features=self.features(image,boxes,attribute,[rule['mode']]);result=np.zeros(mask.shape,bool)
  for f in features:
   f['accepted']=f['margin']>rule['threshold']
   if f['accepted']:result|=labels==ids[f['candidate']]
  torch.cuda.synchronize();elapsed=time.perf_counter()-start
  return result,mask,dict(request_s=elapsed,proposal_request_s=meta['request_s'],verification_and_overhead_s=elapsed-meta['request_s'],candidate_boxes=boxes,features=features,main_person=main_person)
