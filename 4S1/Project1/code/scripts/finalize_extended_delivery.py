"""Complete deployment smoke and archive only after the frozen test succeeds."""
import json,os,subprocess,tarfile,time
from pathlib import Path
R=Path('/home/osta/lisa-eval/code');os.chdir(R)
D=R/'results/extended_dev_20260915';T=R/'results/extended_test_20260915';O=R/'results/extended_public_20260915'
while Path('/proc/214902').exists(): time.sleep(20)
assert (T/'export.log').exists() and (O/'data.json').exists(),'Frozen test did not complete; inspect its logs'
data=json.loads((O/'data.json').read_text());assert len(data['items'])==180
sample=json.loads((D/'manifest.json').read_text())['items'][0]
smoke=R/'results/extended_cli_smoke_20260915'
if not (smoke/'result.json').exists():
    assert not smoke.exists(),'Incomplete smoke run requires inspection'
    subprocess.run(['/home/osta/blip2-qformer-eval/.venv/bin/python','scripts/infer_extended.py','--image',sample['image'],'--text',sample['expression'],'--out',str(smoke)],check=True)
result=json.loads((smoke/'result.json').read_text());assert result['annotation_used'] is False
import shutil
for name in ['result.json','overlay.png','primary_lock.json','run.log']: shutil.copy2(smoke/name,O/('deployment_'+name))
shutil.copy2(result['mask'],O/'deployment_mask.png')
shutil.copy2(sample['image'],O/'deployment_image.jpg')
with tarfile.open(R/'results/extended_public_20260915.tar.gz','w:gz') as archive: archive.add(O,arcname='extended-assets')
with tarfile.open(R/'results/extended_records_20260915.tar.gz','w:gz') as archive:
    for directory in [D,T,R/'results/training_free_extended_20260915',smoke]:
        for file in directory.rglob('*'):
            if file.is_file() and file.suffix in {'.json','.jsonl','.log'}: archive.add(file,arcname=str(file.relative_to(R)))
print('FINALIZATION_COMPLETE',flush=True)
