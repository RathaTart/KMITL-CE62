"""Frozen-model verification experiments. All inference/evaluation is remote-only."""
import argparse, hashlib, json, platform, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path('/home/osta/lisa-eval/code')
def read(p): return json.loads(Path(p).read_text())
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2))
def resolve(p):
    p=Path(p);return p if p.is_absolute() else ROOT/p
def name(i):return i['item_id']+'__'+i['prompt_id']
def prepare(out):
    items=[]
    for src,props in [('grefcoco_pilot_p1_p2','global_local_dev_20260914'),('training_free_fresh_20260914','global_local_fresh_20260914')]:
        base=ROOT/'results'/src
        for original in read(base/'manifest.json')['items']:
            i=dict(original)
            for k in ['image','ground_truth']:i[k]=str(resolve(i[k]))
            i['ground_truth_instances']=[str(resolve(p)) for p in i.get('ground_truth_instances',[])]
            i['lisa_mask']=str(base/'p1_masks'/(name(i)+'.png'))
            i['proposals']=str(ROOT/'results'/props/'proposals'/(name(i)+'.npz'))
            i['development_source']=src
            assert Path(i['lisa_mask']).is_file(),i['lisa_mask']
            assert Path(i['proposals']).is_file(),i['proposals']
            items.append(i)
    assert len(items)==90 and len({Path(i['image']).name for i in items})==90
    write(out/'manifest.json',dict(items=items,status='Explored development only; no model-weight training'))
    write(out/'protocol.json',dict(seed=2026091501,development=90,primary_test=180,
        families=['Qwen full-scene presence','Qwen LISA-region verification','Qwen individual candidate verification','BLIP2 likelihood verification','CLIP contrastive selection','geometric mask refinement','custom combinations'],
        selection='Choose on development only; lock one primary custom method before fresh test scoring. Positive IoU and no-target accuracy reported separately. A gate may sacrifice at most 1 percentage point development positive IoU. No guarantee of superiority.',
        test='results/training_free_extended_20260915',training=False,scope='gRefCOCO language selection; does not establish CCTV generalization',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print('Prepared',len(items),flush=True)
def qwen(a):
    import torch
    from transformers import AutoProcessor,Qwen2VLForConditionalGeneration
    modelid='Qwen/Qwen2-VL-2B-Instruct'
    proc=AutoProcessor.from_pretrained(modelid,local_files_only=True,min_pixels=256*28*28,max_pixels=512*28*28)
    model=Qwen2VLForConditionalGeneration.from_pretrained(modelid,local_files_only=True,torch_dtype=torch.float16,attn_implementation='sdpa').cuda().eval()
    torch.manual_seed(2026091501)
    tokens={w:proc.tokenizer.encode(w,add_special_tokens=False) for w in ['Yes','No']}
    assert all(len(v)==1 for v in tokens.values()),tokens
    dst=a.out/('qwen_'+a.view+'.jsonl');done={}
    if dst.exists():done={r['key']:r for r in [json.loads(s) for s in dst.read_text().splitlines() if s]}
    for i in read(a.out/'manifest.json')['items']:
        if i['key'] in done:continue
        original=Image.open(i['image']).convert('RGB');views=[]
        if a.view=='presence':views=[(original,None)]
        elif a.view=='lisa':
            mask=np.asarray(Image.open(i['lisa_mask']))>0
            im=original.copy();ys,xs=np.where(mask)
            if len(xs):ImageDraw.Draw(im).rectangle([int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],outline='red',width=3)
            views=[(im,-1)]
        else:
            data=np.load(i['proposals'])
            for j,b in enumerate(data['boxes']):
                im=original.copy();ImageDraw.Draw(im).rectangle(b.tolist(),outline='red',width=3);views.append((im,j))
        result=[]
        for im,j in views:
            if a.view=='presence':prompt=f'Is there at least one person in this image matching the description "{i["expression"]}"? All stated attributes must belong to that same person. Use scene context for relations. Answer Yes or No.'
            else:prompt=f'Does the person or group marked by the red rectangle match the description "{i["expression"]}"? All stated clothing attributes must belong to the described person. Use the full image for spatial relations. Answer Yes or No.'
            text=proc.apply_chat_template([{'role':'user','content':[{'type':'image'},{'type':'text','text':prompt}]}],tokenize=False,add_generation_prompt=True)
            x=proc(text=[text],images=[im],return_tensors='pt').to('cuda');torch.cuda.synchronize();start=time.perf_counter()
            with torch.inference_mode():logits=model(**x,use_cache=False).logits[0,-1].float()
            score=logits[tokens['Yes'][0]]-logits[tokens['No'][0]]
            torch.cuda.synchronize()
            result.append(dict(index=j,logit_yes_no=float(score),yes_probability=float(torch.sigmoid(score)),top_token=proc.tokenizer.decode([int(logits.argmax())]),prompt=prompt,seconds=time.perf_counter()-start))
        row=dict(key=i['key'],results=result)
        with dst.open('a') as f:f.write(json.dumps(row)+'\n')
        print(a.view,i['key'],[round(r['yes_probability'],3) for r in result],flush=True)
    write(a.out/('qwen_'+a.view+'_config.json'),dict(model=modelid,precision='fp16',max_pixels=512*28*28,score='first-token Yes minus No logits; conditional binary score, not calibrated probability',tokens=tokens,training=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),peak_memory_gib=torch.cuda.max_memory_allocated()/2**30))
if __name__=='__main__':
    if platform.node()!='cenara70hx':raise SystemExit('Remote only')
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','qwen']);p.add_argument('--out',type=Path,default=ROOT/'results/extended_dev_20260915');p.add_argument('--view',choices=['presence','lisa','candidate'],default='presence');a=p.parse_args()
    if a.stage=='prepare':prepare(a.out)
    else:qwen(a)
