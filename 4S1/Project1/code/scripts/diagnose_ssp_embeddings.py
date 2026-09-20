"""Released SSP-SAM-224 inference, including uncached SAM encoding; no GT reads."""
import argparse,hashlib,json,os,platform,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/released-models');C=Path('/home/osta/lisa-eval/code');S=R/'SSP-SAM';sys.path[:0]=[str(S),str(S/'segment-anything')]
import pkg_resources,packaging
pkg_resources.packaging=packaging  # compatibility for upstream's old import
import models.ssp_sam_224 as module
from datasets.transforms import RandomResize,ToTensor,NormalizeAndPad,SAMResize
from clip import tokenize
p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=90);p.add_argument('--out',default='released_checkpoints_20260915/SSP_SAM_224');a=p.parse_args();O=C/'results'/a.out;O.mkdir(parents=True,exist_ok=True);(O/'masks').mkdir(exist_ok=True);(O/'native_masks').mkdir(exist_ok=True)
torch.set_num_threads(4);torch.manual_seed(20260915);module.sam_checkpoint=str(R/'weights/sam_vit_h_4b8939.pth');start=time.perf_counter()
model=module.SSP_SAM(str(R/'weights/SSP-SAM_CS-ViT-B-16.pt'),SimpleNamespace(is_pretrain=False),device='cpu')
ck=R/'weights/SSP-SAM_checkpoint_best_miou.pth';state=torch.load(ck,map_location='cpu',weights_only=False)['model'];state={k:v for k,v in state.items() if not k.startswith('encoder')}
# Upstream dataset computes features using original frozen SAM. Verify released encoder matches it.
original=model.sam.image_encoder.state_dict();encoder_equal=all(torch.equal(original[k],state['sam.image_encoder.'+k]) for k in original if 'sam.image_encoder.'+k in state);assert encoder_equal
missing,unexpected=model.load_state_dict(state,strict=False);assert not unexpected;assert all(k.startswith('encoder.') for k in missing),(missing,unexpected);del state,original
model=model.cuda().eval();model.sam.image_encoder.float();load_s=time.perf_counter()-start
transforms=[RandomResize([224],record_resize_info=True),ToTensor(keys=[]),NormalizeAndPad(size=224,center_place=True)];sam_transform=SAMResize();items=json.loads((C/'results/router_confirm_20260915/manifest.json').read_text())['items'][2:3]
for j,i in enumerate(items):
 t=time.perf_counter();original=Image.open(i['image']).convert('RGB');w,h=original.size;img=original;target={'phrase':i['expression'].lower(),'ori_size':torch.tensor([h,w]),'bbox':torch.tensor([0.,0.,float(w),float(h)])}
 for tr in transforms:img,target=tr(img,target)
 image_mask=target['mask'].unsqueeze(0).cuda();td={k:v.unsqueeze(0).cuda() for k,v in target.items() if isinstance(v,torch.Tensor)};words=tokenize([i['expression'].lower()+'.']).cuda();wm=words!=0;sam_img=sam_transform(np.asarray(original)).unsqueeze(0).cuda().float();img=img.unsqueeze(0).cuda()
 torch.cuda.synchronize();tm=time.perf_counter()
 with torch.inference_mode():embedding=model.sam.image_encoder(sam_img).float(); model.sam.image_encoder.half(); half_embedding=model.sam.image_encoder(sam_img.half()).float(); print('EMBED',float((embedding-half_embedding).abs().max()),float((embedding-half_embedding).abs().mean()),bool(torch.isfinite(half_embedding).all()),flush=True)
 torch.cuda.synchronize();encoder_s=time.perf_counter()-tm;tm=time.perf_counter()
 with torch.inference_mode():out=model(img,image_mask,words,wm,embedding,td['ori_size'],td)['pred_masks']; out_half=model(img,image_mask,words,wm,half_embedding,td['ori_size'],td)['pred_masks']; out_repeat=model(img,image_mask,words,wm,embedding,td['ori_size'],td)['pred_masks']; print('LOGITS',float((out-out_half).abs().mean()),float((out-out_repeat).abs().max()),flush=True)
 torch.cuda.synchronize();decoder_s=time.perf_counter()-tm;native=(out.sigmoid()>=.5).squeeze().cpu().numpy();assert native.shape==(512,512),native.shape;empty=bool(native.sum()<50)
 nh,nw=sam_transform.resize_transform.get_preprocess_shape(h,w,1024);up=np.asarray(Image.fromarray(native).resize((1024,1024),Image.Resampling.NEAREST));mask=np.asarray(Image.fromarray(up[:nh,:nw]).resize((w,h),Image.Resampling.NEAREST)).copy()
 if empty:mask[:]=False
 name=i['item_id']+'__'+i['prompt_id']+'.png';path=O/'masks'/name;Image.fromarray(mask.astype('uint8')*255).save(path);Image.fromarray(native.astype('uint8')*255).save(O/'native_masks'/name)
 row=dict(key=i['key'],mask=str(path),no_target=empty,native_pixels=int(native.sum()),model_s=encoder_s+decoder_s,sam_encoder_s=encoder_s,prompt_decoder_s=decoder_s,request_s=time.perf_counter()-t,mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 with (O/'rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(j+1,len(items),round(row['model_s'],3),flush=True)
(O/'provenance.json').write_text(json.dumps(dict(checkpoint=str(ck),code_commit=os.popen('git -C '+str(S)+' rev-parse HEAD').read().strip(),load_policy='Same as official test.py: ignore encoder.* and load released CLIP Surgery weights; missing keys verified encoder-only',original_sam_encoder_equal=encoder_equal,model_load_s=load_s,precision='Full float32 precision diagnostic',sam_embedding_cached=False,no_target_rule='fewer than 50 foreground pixels in native 512x512 mask, as paper GRES protocol',mask_conversion='threshold native logits at 0, nearest upsample to 1024, remove bottom/right SAM padding, nearest resize to original',ground_truth_used=False,torch=torch.__version__,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))



