import json,platform,requests,importlib.util
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_url,get_hf_file_metadata
assert platform.node()=='cenara70hx'
rows=[]
for repo in ['facebook/sam3','IDEA-Research/RexSeek-3B']:
    row={'repo':repo}
    try:
        info=HfApi().model_info(repo,files_metadata=True);row.update(sha=info.sha,gated=info.gated,files=[{'name':s.rfilename,'size':s.size} for s in info.siblings])
        fn=next(s.rfilename for s in info.siblings if s.rfilename.endswith(('.safetensors','.pt','.bin')))
        try:md=get_hf_file_metadata(hf_hub_url(repo,fn));row['weight_access']={'status':'accessible','size':md.size}
        except Exception as e:row['weight_access']={'status':'blocked','error':type(e).__name__,'http_status':getattr(getattr(e,'response',None),'status_code',None)}
        if repo.endswith('RexSeek-3B'):
            r=requests.get(hf_hub_url(repo,'config.json'),timeout=30);r.raise_for_status();row['config']=r.json()
    except Exception as e:row['error']=type(e).__name__
    rows.append(row)
out=Path('/home/osta/lisa-eval/code/results/extended_dev_20260915/availability.json');out.write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
