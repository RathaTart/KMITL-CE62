"""Prepare isolated RexSeek runtime, loading its embedded vision weights once."""
import json,platform,requests,shutil,hashlib
from pathlib import Path
from robust_download import download
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');source=root/'weights/RexSeek-3B-20260915';dest=root/'research_vendors/rexseek-runtime/model';dest.mkdir(exist_ok=True)
assert (source/'download_audit.json').exists(),'Wait for verified download'
for p in source.iterdir():
    q=dest/p.name
    if q.exists():continue
    if p.suffix=='.py' or p.name=='config.json':shutil.copy2(p,q)
    else:q.symlink_to(p)
vision=dest/'clip336';vision.mkdir(exist_ok=True)
for fn in ['config.json','preprocessor_config.json']:
    download('https://huggingface.co/openai/clip-vit-large-patch14-336/resolve/main/'+fn,str(vision/fn),max_stalls=8)
p=dest/'clip.py';original=(source/'clip.py').read_text();old='self.vision_tower = CLIPVisionModel.from_pretrained(\n            self.vision_tower_name, device_map=device_map\n        )';new='self.vision_tower = CLIPVisionModel(CLIPVisionConfig.from_pretrained(self.vision_tower_name))'
assert old in original
p.write_text(original.replace(old,new))
cfg=json.loads((dest/'config.json').read_text());cfg['mm_vision_tower']=str(vision);(dest/'config.json').write_text(json.dumps(cfg,indent=2))
(dest/'runtime_patch_audit.json').write_text(json.dumps(dict(reason='Avoid redundant base CLIP weight download; all 391 vision parameters are included in the pinned RexSeek checkpoint and loading missing keys must be checked.',source_sha256=hashlib.sha256(original.encode()).hexdigest(),patched_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),patch=dict(old=old,new=new)),indent=2))
print(dest)

