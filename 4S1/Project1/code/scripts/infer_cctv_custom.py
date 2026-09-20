"""Run a locked CCTV experiment variant on an arbitrary image, on cenara70hx."""
import argparse,json,platform,hashlib
from pathlib import Path
from PIL import Image
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--text',default='all people');p.add_argument('--model',choices=['original','customA','customB'],default='original');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);assert not out.exists(),'Refuse overwrite';assert Path(a.image).is_file();out.mkdir(parents=True)
from cctv_engine import CCTVEngine
engine=CCTVEngine();mask,meta,_,_=engine.predict(a.image,a.text,a.model);Image.fromarray(mask.astype('uint8')*255).save(out/'mask.png');result=dict(image=a.image,image_sha256=hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),text=a.text,model=a.model,ground_truth_used=False,**meta);(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
