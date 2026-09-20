"""Training-free candidate selection inspired by HybridGL/TAS spatial guidance.

This is NOT a reproduction of HybridGL: it uses frozen standard CLIP L/14
image embeddings, detector proposals, explicit geometry and conservative clauses.
"""
import argparse,hashlib,json,platform,re,time
from pathlib import Path
import cv2,numpy as np
from PIL import Image

def read(p):return json.loads(Path(p).read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s]
def name(i):return f'{i["item_id"]}__{i["prompt_id"]}'
def clauses(text):
    # Split only explicit conjunctions introducing another person/directional noun.
    # Keep clothing conjunctions such as "black jacket and blue hat" intact.
    return [s.strip() for s in re.split(r'\band\s+(?=(?:the\s+|a\s+)?(?:man|woman|boy|girl|guy|lady|kid|person|child|baby|left person|right person)\b)',text,flags=re.I) if s.strip()]

def prepare(a):
    m=read(a.source/'manifest.json');write(a.out/'manifest.json',m);write(a.out/'candidates/manifest.json',m)
    (a.out/'candidates/blip2_answers.jsonl').write_text(''.join(json.dumps(dict(key=i['key'],answer='person'))+'\n' for i in m['items']))

def candidates(a):
    from run_blip2_grounded_sam import phase_grounding,DEFAULT_GROUNDING
    prepare(a);phase_grounding(a.out/'candidates',DEFAULT_GROUNDING,.25,.25,0)

def masks(a):
    import torch
    from torchvision.ops import nms
    from transformers import SamModel,SamProcessor
    proc=SamProcessor.from_pretrained('facebook/sam-vit-huge',local_files_only=True)
    model=SamModel.from_pretrained('facebook/sam-vit-huge',local_files_only=True,torch_dtype=torch.float16).cuda().eval()
    m=read(a.out/'manifest.json');boxes={r['key']:r for r in lines(a.out/'candidates/grounding_boxes.jsonl')};audit=[]
    for i in m['items']:
        dst=a.out/'proposals'/f'{name(i)}.npz'
        if dst.exists():continue
        dst.parent.mkdir(parents=True,exist_ok=True);im=Image.open(i['image']).convert('RGB');r=boxes[i['key']]
        b=torch.tensor(r['boxes'],dtype=torch.float32).reshape(-1,4);scores=torch.tensor(r['scores']);keep=nms(b,scores,.5).tolist()[:12];b=b[keep].tolist();scores=scores[keep].tolist();start=time.perf_counter()
        if b:
            x=proc(images=im,input_boxes=[b],return_tensors='pt');x={k:v.cuda().half() if v.is_floating_point() else v.cuda() for k,v in x.items()}
            with torch.inference_mode():o=model(**x,multimask_output=False)
            masks=proc.image_processor.post_process_masks(o.pred_masks.cpu(),x['original_sizes'].cpu(),x['reshaped_input_sizes'].cpu())[0][:,0].numpy()>0
        else:masks=np.zeros((0,im.height,im.width),bool)
        np.savez_compressed(dst,masks=masks,boxes=np.array(b).reshape(-1,4),detector_scores=np.array(scores));audit.append(dict(key=i['key'],n=len(b),seconds=time.perf_counter()-start));write(a.out/'sam_audit.json',audit);print('candidate masks',i['key'],len(b),flush=True)

def features(a):
    import torch
    from transformers import CLIPModel,CLIPProcessor
    path='/home/osta/lisa-eval/code/weights/clip-vit-large-patch14';proc=CLIPProcessor.from_pretrained(path,local_files_only=True);model=CLIPModel.from_pretrained(path,local_files_only=True,torch_dtype=torch.float16).cuda().eval();rows=[]
    for i in read(a.out/'manifest.json')['items']:
        im=np.asarray(Image.open(i['image']).convert('RGB'));data=np.load(a.out/'proposals'/f'{name(i)}.npz');ms=data['masks'];boxes=data['boxes'];views=[]
        blurred=cv2.GaussianBlur(im,(31,31),0)
        for mask,b in zip(ms,boxes):
            x1,y1,x2,y2=[int(v) for v in b];x1=max(0,x1);y1=max(0,y1);x2=min(im.shape[1],x2+1);y2=min(im.shape[0],y2+1)
            isolated=np.where(mask[:,:,None],im,128).astype('uint8');local=isolated[y1:y2,x1:x2]
            if not local.size:local=isolated
            global_view=np.where(mask[:,:,None],im,blurred).astype('uint8')
            views.extend([Image.fromarray(local).resize((224,224)),Image.fromarray(global_view).resize((224,224))])
        cs=clauses(i['expression']);texts=['a photo of '+s for s in cs]+['a photo of a person']
        with torch.inference_mode():
            te=proc(text=texts,padding=True,truncation=True,max_length=77,return_tensors='pt');te={k:v.cuda() for k,v in te.items()};tf=model.get_text_features(**te);tf=torch.nn.functional.normalize(tf.float(),dim=-1)
            vf=[]
            for start in range(0,len(views),8):
                x=proc(images=views[start:start+8],return_tensors='pt')['pixel_values'].cuda().half();f=model.get_image_features(pixel_values=x);vf.append(torch.nn.functional.normalize(f.float(),dim=-1))
            similarities=(torch.cat(vf)@tf.T).cpu().numpy().reshape(len(ms),2,len(texts)) if vf else np.zeros((0,2,len(texts)))
        rows.append(dict(key=i['key'],clauses=cs,local=similarities[:,0].tolist(),global_context=similarities[:,1].tolist(),boxes=boxes.tolist(),image_size=[im.shape[1],im.shape[0]],detector_scores=data['detector_scores'].tolist()))
        write(a.out/'clip_scores.json',rows);print('CLIP',i['key'],len(ms),cs,flush=True)
    write(a.out/'feature_config.json',dict(training=False,model=path,checkpoint_sha256=hashlib.sha256((Path(path)/'pytorch_model.bin').read_bytes()).hexdigest(),global_view='sharp candidate, Gaussian-blurred full-image context',local='candidate mask isolated on gray, cropped to detector box',no_weight_updates=True,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))

def selected(r,mode,floor):
    local=np.array(r['local']);global_=np.array(r['global_context']);n=len(local)
    if n==0:return [],[]
    score=local[:,:-1] if mode=='local' else .5*(local[:,:-1]+global_[:,:-1]);evidence=score.copy();b=np.array(r['boxes']);cx=(b[:,0]+b[:,2])/(2*r['image_size'][0]);cy=(b[:,1]+b[:,3])/(2*r['image_size'][1]);ops=[]
    if mode=='spatial':
        for j,q in enumerate(r['clauses']):
            q=q.lower();op=None
            if re.search(r'\b(left|right) of\b|\bnext to\b|\bbeside\b',q):ops.append('relative relation not executed');continue
            left=bool(re.search(r'\bleft(?:most)?\b',q));right=bool(re.search(r'\bright(?:most)?\b',q))
            if left and not right:score[:,j]+=.08*(.5-cx);op='left coordinate bonus'
            elif right and not left:score[:,j]+=.08*(cx-.5);op='right coordinate bonus'
            elif re.search(r'\b(center|middle)\b',q):score[:,j]+=.08*(.5-np.abs(cx-.5));op='horizontal center bonus'
            ops.append(op)
    keep=[]
    for j,q in enumerate(r['clauses']):
        best=int(score[:,j].argmax())
        if evidence[best,j]<floor:continue
        if re.search(r'\b(all|both|people|men|women|boys|girls|kids|players)\b',q,re.I):
            keep.extend(int(k) for k in range(n) if score[k,j]>=score[best,j]-.015 and evidence[k,j]>=floor)
        else:keep.append(best)
    return sorted(set(keep)),ops

def render(a,mode,floor,folder):
    folder.mkdir(parents=True,exist_ok=True);records={r['key']:r for r in read(a.out/'clip_scores.json')};audit=[]
    for i in read(a.out/'manifest.json')['items']:
        r=records[i['key']];keep,ops=selected(r,mode,floor);data=np.load(a.out/'proposals'/f'{name(i)}.npz');masks=data['masks'];pred=masks[keep].any(0) if keep else np.zeros(masks.shape[1:],bool);Image.fromarray(pred.astype('uint8')*255).save(folder/f'{name(i)}.png');audit.append(dict(key=i['key'],selected_indices=keep,spatial_operations=ops))
    write(folder.parent/'selection.json',audit)

def choose(a):
    trials=[]
    for mode in ['local','hybrid','spatial']:
        for floor in [0.,.20,.25,.30]:
            folder=a.out/f'{mode}_{floor:.2f}'/'masks';render(a,mode,floor,folder);scores=[]
            for i in read(a.out/'manifest.json')['items']:
                pred=np.asarray(Image.open(folder/f'{name(i)}.png'))>0;gt=np.asarray(Image.open(i['ground_truth']))>0;union=(pred|gt).sum();scores.append(float((pred&gt).sum()/union) if union else 1.)
            trials.append(dict(mode=mode,floor=floor,development_overall_iou=float(np.mean(scores))))
    best=max(trials,key=lambda r:r['development_overall_iou']);write(a.out/'method_lock.json',dict(chosen=best,trials=trials,training=False,selection='Only historical 30-expression development GT; no fresh evaluation GT used',implementation='HybridGL/GeoSelect-inspired simplified CLIP/geometry baseline, not a reproduction'))
    print(json.dumps(best),flush=True)

if __name__=='__main__':
    if platform.node()!='cenara70hx':raise SystemExit('Remote only')
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','candidates','masks','features','choose','render']);p.add_argument('--source',type=Path,default=Path('results/grefcoco_pilot_p1_p2'));p.add_argument('--out',type=Path,default=Path('results/global_local_dev_20260914'));p.add_argument('--lock',type=Path);a=p.parse_args()
    if a.stage=='render':
        cfg=read(a.lock)['chosen'];render(a,cfg['mode'],cfg['floor'],a.out/'selected/masks');write(a.out/'applied_lock.json',read(a.lock))
    else:globals()[a.stage](a)
