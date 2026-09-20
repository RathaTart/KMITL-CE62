"""Read-only import of colleague's ZoomNeXt; write predictions in our results tree."""
import argparse,sys,json,time,hashlib,platform
from pathlib import Path
import cv2,numpy as np,torch
if platform.node()!='cenara70hx':raise SystemExit('Remote execution only')
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('results/grefcoco_pilot_p1_p2'));p.add_argument('--out',type=Path,default=Path('results/lisa_refinement_20260914/zoom'));a=p.parse_args()
root=Path('/home/osta/ZoomNeXt/ZoomNeXt');sys.path.insert(0,str(root))
from methods import EffB1_ZoomNeXt
from utils import ops
checkpoint=root/'outputs/EffB1_ZoomNeXt_BS2_LR2e-05_E30_H384_W384_OPMadam_OPGMfinetune_SCstep_AMP_INFOfinetune_person/exp_2/pth/state_final.pth'
state=torch.load(checkpoint,map_location='cpu');print('checkpoint keys',list(state)[:8],flush=True)
model=EffB1_ZoomNeXt(pretrained=False)
if 'state_dict' in state:state=state['state_dict']
model.load_state_dict(state,strict=True);model.cuda().eval()
a.out.mkdir(parents=True,exist_ok=True);(a.out/'masks').mkdir(exist_ok=True);(a.out/'probabilities').mkdir(exist_ok=True)
manifest=json.loads((a.source/'manifest.json').read_text());rows=[]
for i in manifest['items']:
    im=cv2.cvtColor(cv2.imread(i['image']),cv2.COLOR_BGR2RGB);h,w=im.shape[:2]
    images=ops.ms_resize(im,scales=(.5,1.,1.5),base_h=384,base_w=384)
    data={k:torch.from_numpy(im.copy()).float().div(255).permute(2,0,1)[None].cuda() for k,im in zip(['image_s','image_m','image_l'],images)}
    torch.cuda.synchronize();t=time.perf_counter()
    with torch.no_grad():prob=model(data=data).sigmoid()[0,0].cpu().numpy()
    torch.cuda.synchronize();elapsed=time.perf_counter()-t
    prob=(prob-prob.min())/(prob.max()-prob.min()+1e-8);prob=ops.resize(prob,height=h,width=w)
    name=f'{i["item_id"]}__{i["prompt_id"]}'
    np.save(a.out/'probabilities'/f'{name}.npy',prob.astype('float16'))
    cv2.imwrite(str(a.out/'masks'/f'{name}.png'),(prob>=.5).astype('uint8')*255)
    rows.append(dict(key=i['key'],model_s=elapsed));print(i['key'],flush=True)
(a.out/'provenance.json').write_text(json.dumps(dict(checkpoint=str(checkpoint),sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),protocol='RGB, three scales base384, fp32, native per-image minmax normalization then threshold .5; vision-only no text input',rows=rows),indent=2))
