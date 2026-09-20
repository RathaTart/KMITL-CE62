"""Fetch official annotation metadata only; no videos, model inference, or tuning."""
import hashlib,json,platform,urllib.request,zipfile
from pathlib import Path
if platform.node()!='cenara70hx': raise SystemExit('Remote only')
out=Path('results/personpath22_metadata_20260914');out.mkdir(exist_ok=True)
base='https://tracking-dataset-eccv-2022.s3.amazonaws.com/dataset/annotation/'
report={'purpose':'Dataset readiness for fixed-camera CCTV; no imagery downloaded or selected','files':{}}
for name in ['splits.json','anno_visible.zip']:
    path=out/name
    if not path.exists(): urllib.request.urlretrieve(base+name,path)
    info={'url':base+name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if name.endswith('.json'):
        data=json.loads(path.read_text());info['top_level_type']=type(data).__name__
        if isinstance(data,dict):info['entries']={k:len(v) if hasattr(v,'__len__') else v for k,v in data.items()};info['sample']={k:v[:3] if isinstance(v,list) else str(v)[:300] for k,v in data.items()}
    else:
        with zipfile.ZipFile(path) as z:
            names=z.namelist();info['archive_entries']=names[:12];info['n_entries']=len(names)
            for n in names:
                if n.endswith('.json'):
                    data=json.loads(z.read(n));info['sample_json']=n;info['top_level_type']=type(data).__name__
                    if isinstance(data,dict):
                        info['top_level_keys']=list(data)[:30]
                        info['value_types']={k:type(v).__name__ for k,v in list(data.items())[:30]}
                        if 'samples' in data:
                            info['sample_count']=len(data['samples']);info['first_sample']=str(next(iter(data['samples'].items())))[:4500]
                            info['metadata']=data.get('metadata')
                        for k,v in data.items():
                            if isinstance(v,dict):info['first_dict']={k:str(next(iter(v.items()),None))[:2000]};break
                    break
            video_json=next(n for n in names if n.startswith('anno_visible_2022/') and n.endswith('.json'))
            video=json.loads(z.read(video_json));info['first_video_structure']={k:type(v).__name__ for k,v in video.items()};info['first_video_preview']=str(video)[:3500]
    report['files'][name]=info
(out/'readiness.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
