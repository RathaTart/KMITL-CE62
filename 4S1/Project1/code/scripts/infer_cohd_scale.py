"""Remote-only single image/text inference for locked scale candidates."""
import argparse,json,hashlib,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--text',required=True);p.add_argument('--method',choices=['original','scale704_guard','scale768_guard'],default='original');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);assert not out.exists(),'Refuse overwrite';assert Path(a.image).is_file();out.mkdir(parents=True)
from cohd_scale_engine import predict,VARIANTS
from PIL import Image
mask,meta=predict(a.image,a.text,a.method);Image.fromarray(mask.astype('uint8')*255).save(out/'mask.png');record=dict(image=a.image,image_sha256=hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),text=a.text,method=a.method,configuration=VARIANTS[a.method],ground_truth_used=False,**meta);(out/'result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
