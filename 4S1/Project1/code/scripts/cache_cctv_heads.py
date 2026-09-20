"""Cache frozen inputs to CoHD's existing prediction heads, remote only."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from cohd_verifier_engine import model,cfg,tokenizer,C,ResizeTransform
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--out',required=True);a=p.parse_args();O=Path(a.out);assert not O.exists();O.mkdir(parents=True);items=json.loads(Path(a.manifest).read_text())['items'];captured={}
def hmask(mod,args):captured['queries']=args[0].detach().cpu()
def hdha(mod,args):captured['attns']=[v.detach().cpu() for v in args[0]]
model.sem_seg_head.predictor.mask_embed.register_forward_pre_hook(hmask);model.sem_seg_head.predictor.dha.register_forward_pre_hook(hdha)
rows=[]
for j,i in enumerate(items):
 im=np.asarray(Image.open(i['image']).convert('RGB'));h,w=im.shape[:2];size=cfg.INPUT.IMAGE_SIZE;img=ResizeTransform(h,w,size,size).apply_image(im if cfg.INPUT.FORMAT=='RGB' else im[:,:,::-1]);ids=tokenizer.encode(i['expression'],add_special_tokens=True)[:cfg.REFERRING.MAX_TOKENS];tokens=ids+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));attn=[1]*len(ids)+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));data=dict(image=torch.as_tensor(np.ascontiguousarray(img.transpose(2,0,1))),lang_tokens=torch.tensor([tokens]),lang_mask=torch.tensor([attn]),height=h,width=w)
 with torch.inference_mode():out=model([data])[0]
 blob=dict(**captured,count=out['count_pred'].cpu(),nt=out['nt_label'].cpu(),teacher=out['ref_seg'].cpu(),key=i['key']);f=O/(i['item_id']+'__expression.pt');torch.save(blob,f);rows.append(dict(key=i['key'],cache=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 print(j+1,len(items),flush=True)
(O/'index.json').write_text(json.dumps(rows,indent=2));(O/'provenance.json').write_text(json.dumps(dict(manifest=a.manifest,manifest_sha256=hashlib.sha256(Path(a.manifest).read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),weights='Released CoHD unchanged',ground_truth_used_in_feature_extraction=False),indent=2))
