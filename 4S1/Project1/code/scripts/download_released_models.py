import json,sys,requests,subprocess
from pathlib import Path
R=Path('/home/osta/lisa-eval/released-models'); W=R/'weights';W.mkdir(exist_ok=True)
manifest=[]
for repo,paths in [('RobertLuo1/CoHD',['CoHD_grefcoco_swin_tiny.pth']),('wayneicloud/SSP-SAM',['output/grefcoco/224/checkpoint_best_miou.pth','pretrained_checkpoints/CS/CS-ViT-B-16.pt'])]:
    meta=requests.get('https://huggingface.co/api/models/'+repo+'?blobs=true',timeout=60).json()
    for name in paths:
        f=next(f for f in meta['siblings'] if f['rfilename']==name);dest=W/(repo.split('/')[1]+'_'+Path(name).name);digest=f.get('lfs',{}).get('sha256');url='https://huggingface.co/'+repo+'/resolve/'+meta['sha']+'/'+name
        row=dict(repo=repo,revision=meta['sha'],file=name,dest=str(dest),sha256=digest,size=f.get('size'));manifest.append(row)
        (R/'downloads.json').write_text(json.dumps(manifest,indent=2));print(row,flush=True)
        cmd=[sys.executable,'/home/osta/lisa-eval/code/scripts/robust_download.py',url,str(dest)]
        if digest:cmd+=['--sha256',digest]
        subprocess.run(cmd,check=True)
