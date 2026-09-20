"""Frozen BLIP2 first-answer-token likelihood, preserving full-scene context."""
import argparse,json,platform,time,hashlib
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor,Blip2ForConditionalGeneration,BitsAndBytesConfig
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915'));a=p.parse_args()
modelid='Salesforce/blip2-flan-t5-xl';proc=AutoProcessor.from_pretrained(modelid,local_files_only=True)
model=Blip2ForConditionalGeneration.from_pretrained(modelid,local_files_only=True,device_map='auto',quantization_config=BitsAndBytesConfig(load_in_8bit=True),torch_dtype=torch.float16,low_cpu_mem_usage=True).eval()
tokens={w:proc.tokenizer.encode(w,add_special_tokens=False) for w in ['yes','no']};assert all(len(t)==1 for t in tokens.values()),tokens
out=a.out/'blip_presence.jsonl';done={json.loads(s)['key'] for s in out.read_text().splitlines()} if out.exists() else set()
for i in json.loads((a.out/'manifest.json').read_text())['items']:
    if i['key'] in done:continue
    im=Image.open(i['image']).convert('RGB');prompt=f'Question: Is there a person matching this description: {i["expression"]}? Answer yes or no. Answer:'
    x=proc(images=im,text=prompt,return_tensors='pt');x={k:v.to('cuda',dtype=torch.float16) if v.is_floating_point() else v.cuda() for k,v in x.items()};torch.cuda.synchronize();start=time.perf_counter()
    with torch.inference_mode():o=model.generate(**x,max_new_tokens=1,do_sample=False,return_dict_in_generate=True,output_scores=True)
    logits=o.scores[0][0].float();s=logits[tokens['yes'][0]]-logits[tokens['no'][0]];torch.cuda.synchronize()
    row=dict(key=i['key'],prompt=prompt,logit_yes_no=float(s),yes_probability=float(torch.sigmoid(s)),top_token=proc.tokenizer.decode([int(logits.argmax())]),seconds=time.perf_counter()-start)
    with out.open('a') as f:f.write(json.dumps(row)+'\n')
    print(i['key'],round(row['yes_probability'],3),flush=True)
(a.out/'blip_presence_config.json').write_text(json.dumps(dict(model=modelid,quantization='8bit',tokens=tokens,score='first-token yes/no conditional likelihood; threshold selected on development',training=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
