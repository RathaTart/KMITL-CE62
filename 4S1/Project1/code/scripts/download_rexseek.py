import hashlib,json,platform
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_url
from robust_download import download
assert platform.node()=='cenara70hx'
repo='IDEA-Research/RexSeek-3B';info=HfApi().model_info(repo,files_metadata=True);out=Path('/home/osta/lisa-eval/code/weights/RexSeek-3B-20260915');out.mkdir(exist_ok=True)
manifest=[]
for s in info.siblings:
    if '/' in s.rfilename or not s.rfilename.endswith(('.json','.txt','.py','.safetensors')):continue
    dest=out/s.rfilename;expected=s.lfs.sha256 if s.lfs else None
    download(hf_hub_url(repo,s.rfilename,revision=info.sha),str(dest),sha256=expected,max_stalls=8)
    assert dest.stat().st_size==s.size,(s.rfilename,dest.stat().st_size,s.size)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    assert not expected or digest==expected
    manifest.append(dict(file=s.rfilename,size=s.size,sha256=digest))
(out/'download_audit.json').write_text(json.dumps(dict(repo=repo,revision=info.sha,files=manifest),indent=2))
