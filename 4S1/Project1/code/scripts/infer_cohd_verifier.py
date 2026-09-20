"""Remote image/text CLI for the frozen CoHD verifier experiment."""
import argparse,json
from pathlib import Path
from PIL import Image
from cohd_verifier_engine import CoHDVerifier,C
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--text',required=True);p.add_argument('--out',required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args();out=Path(a.out);assert not out.exists(),'Refuse overwrite';out.mkdir(parents=True)
engine=CoHDVerifier(C/'results/cohd_upgrade_20260915/method_lock.json');mask,meta=engine.predict(a.image,a.text,not a.baseline);Image.fromarray(mask.astype('uint8')*255).save(out/'mask.png');(out/'result.json').write_text(json.dumps(dict(image=a.image,expression=a.text,**meta),indent=2));print(json.dumps(meta))
