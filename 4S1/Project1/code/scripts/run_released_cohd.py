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
p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=90);p.add_argument('--out',default='released_checkpoints_20260915/CoHD_Tiny');a=p.parse_args();O=C/'results'/a.out;O.mkdir(parents=True,exist_ok=True);(O/'masks').mkdir(exist_ok=True)
torch.set_num_threads(4);torch.manual_seed(20260915)
cfg=get_cfg();add_deeplab_config(cfg);add_maskformer2_config(cfg);add_refcoco_config(cfg);cfg.merge_from_file(str(R/'CoHD/configs/referring_swin_tiny_eval.yaml'));cfg.REFERRING.BERT_TYPE=str(bert);cfg.MODEL.WEIGHTS='';cfg.MODEL.DEVICE='cuda'
t=time.perf_counter();model=build_model(cfg);ck=R/'weights/CoHD_CoHD_grefcoco_swin_tiny.pth';state=torch.load(ck,map_location='cpu',weights_only=True);print('checkpoint keys',list(state)[:8],flush=True);state=state.get('model',state);loaded=model.load_state_dict(state,strict=True);del state;model.eval();tokenizer=BertTokenizer.from_pretrained(bert);load_s=time.perf_counter()-t
from detectron2.data.transforms import ResizeTransform
items=json.loads((C/'results/router_confirm_20260915/manifest.json').read_text())['items'][:a.limit];rows=[]
for j,i in enumerate(items):
 t=time.perf_counter();im=np.asarray(Image.open(i['image']).convert('RGB'));h,w=im.shape[:2];size=cfg.INPUT.IMAGE_SIZE;img=ResizeTransform(h,w,size,size).apply_image(im if cfg.INPUT.FORMAT=='RGB' else im[:,:,::-1]);ids=tokenizer.encode(i['expression'],add_special_tokens=True)[:cfg.REFERRING.MAX_TOKENS];tokens=ids+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));attn=[1]*len(ids)+[0]*(cfg.REFERRING.MAX_TOKENS-len(ids));data=dict(image=torch.as_tensor(np.ascontiguousarray(img.transpose(2,0,1))),lang_tokens=torch.tensor([tokens]),lang_mask=torch.tensor([attn]),height=h,width=w)
 torch.cuda.synchronize();tm=time.perf_counter()
 with torch.inference_mode():out=model([data])[0]
 torch.cuda.synchronize();model_s=time.perf_counter()-tm
 nt=bool(out['nt_label'].argmax(dim=0));native=out['ref_seg'].argmax(0).byte().cpu().numpy();mask=np.asarray(Image.fromarray(native).resize((w,h),Image.Resampling.NEAREST))>0
 if nt:mask[:]=False
 path=O/'masks'/(i['item_id']+'__'+i['prompt_id']+'.png');Image.fromarray(mask.astype('uint8')*255).save(path);row=dict(key=i['key'],mask=str(path),no_target=nt,model_s=model_s,request_s=time.perf_counter()-t,mask_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),count=out['count_pred'].detach().cpu().tolist());rows.append(row)
 with (O/'rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(j+1,len(items),round(model_s,3),flush=True)
(O/'provenance.json').write_text(json.dumps(dict(checkpoint=str(ck),code_commit=os.popen('git -C '+str(R/'CoHD')+' rev-parse HEAD').read().strip(),strict_load=True,model_load_s=load_s,precision='float32',deformable_attention='upstream PyTorch fallback on GPU; no compiled CUDA extension',input_size=cfg.INPUT.IMAGE_SIZE,input_format=cfg.INPUT.FORMAT,ground_truth_used=False,torch=torch.__version__,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
