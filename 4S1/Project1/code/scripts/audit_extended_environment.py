"""Record exact cached checkpoint content and runtime without exposing credentials."""
import hashlib,importlib.metadata,json,platform,subprocess,time
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');hub=Path('/home/osta/blip2-qformer-eval/hf-cache/hub');out=root/'results/extended_dev_20260915';models={}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(16*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
for model in ['Qwen/Qwen2-VL-2B-Instruct','Salesforce/blip2-flan-t5-xl','facebook/sam-vit-huge','IDEA-Research/grounding-dino-tiny']:
    base=hub/('models--'+model.replace('/','--'));revision=(base/'refs/main').read_text().strip();snapshot=base/'snapshots'/revision;files=[]
    for p in sorted(snapshot.iterdir()):
        if p.is_file():files.append(dict(name=p.name,size=p.stat().st_size,sha256=sha(p)))
    models[model]=dict(revision=revision,files=files);print('audited',model,flush=True)
result=dict(host=platform.node(),created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),models=models,packages={name:importlib.metadata.version(name) for name in ['torch','torchvision','transformers','numpy','Pillow','bitsandbytes','huggingface-hub']},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip(),script_hashes={p.name:sha(p) for p in (root/'scripts').glob('*extended*') if p.is_file()},rexseek_download_audit=str(root/'weights/RexSeek-3B-20260915/download_audit.json'))
(out/'environment_audit.json').write_text(json.dumps(result,indent=2));print('Environment audit saved',flush=True)
