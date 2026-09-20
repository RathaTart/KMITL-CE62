"""Frozen RexSeek with conservative explicit-person conjunction decomposition."""
import argparse,hashlib,json,platform,re,sys,time
from pathlib import Path
ROOT=Path('/home/osta/lisa-eval/code');sys.path.insert(0,str(ROOT/'research_vendors/rexseek-runtime/packages'))
import numpy as np,torch
from PIL import Image
from transformers import AutoProcessor,AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
assert platform.node()=='cenara70hx'
NOUN=re.compile(r'\b(?:person|people|man|men|woman|women|boy|boys|girl|girls|kid|kids|child|children|guy|guys|lady|ladies|baby|babies|player|players)\b',re.I)
def clauses(text):
    parts=[s.strip() for s in re.split(r'\s+and\s+|\s*&\s*',text,flags=re.I)]
    if len(parts)<2 or any(len(NOUN.findall(s))!=1 for s in parts):return [text]
    bare=[not re.sub(r'\b(?:the|a|an)\b|[^a-z]','',NOUN.sub('',s.lower())) for s in parts]
    if any(bare) and not all(bare):return [text]
    return parts
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results/extended_dev_20260915');a=p.parse_args();path=ROOT/'research_vendors/rexseek-runtime/model';proc=AutoProcessor.from_pretrained(path,trust_remote_code=True,local_files_only=True);tok=AutoTokenizer.from_pretrained(path,use_fast=False,local_files_only=True)
quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True,bnb_4bit_quant_type='nf4',llm_int8_skip_modules=['vision_tower','vision_tower_aux','mm_projector','mm_object_projector','lm_head'])
model,loading=AutoModelForCausalLM.from_pretrained(path,trust_remote_code=True,local_files_only=True,use_safetensors=True,quantization_config=quant,torch_dtype=torch.float16,device_map={'':0},output_loading_info=True,attn_implementation='eager');assert not loading['missing_keys'] and not loading['mismatched_keys'],loading
model.eval();torch.manual_seed(2026091501);dst=a.out/'rexseek_clauses.jsonl';done={json.loads(s)['key'] for s in dst.read_text().splitlines() if s} if dst.exists() else set();basepath=a.out/'rexseek.jsonl';base={r['key']:r for r in [json.loads(s) for s in basepath.read_text().splitlines() if s]} if basepath.exists() else {}
for i in json.loads((a.out/'manifest.json').read_text())['items']:
    if i['key'] in done:continue
    cs=clauses(i['expression'])
    if len(cs)==1 and i['key'] in base:row=dict(base[i['key']],clauses=cs,reused_whole_expression=True,additional_seconds=0.)
    else:
        im=Image.open(i['image']).convert('RGB');data=np.load(i['proposals']);boxes=data['boxes'].tolist();answers=[];indices=[];valid=True;start=time.perf_counter()
        for clause in cs:
            prompt=f'Please detect {clause} in this image. Answer the question with object indexes.'
            if boxes:
                x=proc.process(image=im,question=prompt,bbox=boxes);x={k:v.cuda().half() if v.is_floating_point() else v.cuda() for k,v in x.items()}
                with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):o=model.generate(x.pop('input_ids'),**x,do_sample=False,max_new_tokens=96)
                answer=tok.batch_decode(o,skip_special_tokens=False)[0].strip();groups=re.findall(r'<objects>(.*?)</objects>',answer,re.S);chosen=sorted(set(int(s) for group in groups for s in re.findall(r'<obj(\d+)>',group)));ok=bool(groups) and all(0<=j<len(boxes) for j in chosen)
                if not ok:chosen=[]
            else:answer='';chosen=[];ok=True
            valid=valid and ok;indices.extend(chosen);answers.append(dict(clause=clause,prompt=prompt,raw_answer=answer,valid=ok,selected_indices=chosen))
        torch.cuda.synchronize();row=dict(key=i['key'],clauses=cs,answers=answers,selected_indices=sorted(set(indices)),valid=valid,reused_whole_expression=False,additional_seconds=time.perf_counter()-start)
    with dst.open('a') as f:f.write(json.dumps(row)+'\n')
    print(i['key'],cs,row['selected_indices'],flush=True)
(a.out/'rexseek_clauses_config.json').write_text(json.dumps(dict(model=str(path),quantization='NF4 language linear layers; vision/projectors/head fp16',rule='Split AND/& only when each part contains exactly one explicit person noun; avoid mixed bare/modified noun scopes; otherwise preserve original. Attribute-only conjunctions remain intact.',training=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
