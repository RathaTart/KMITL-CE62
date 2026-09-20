"""Opt-in experimental hat/black-clothing verifier, remote only."""
import argparse,json,platform,hashlib
from pathlib import Path
assert platform.node()=='cenara70hx'
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--attribute',choices=['hat','black_coat'],required=True);p.add_argument('--main-person',action='store_true',help='Use only largest proposed component for cropped-person diagnostics');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);assert not out.exists(),'Refuse overwrite';assert Path(a.image).is_file();out.mkdir(parents=True)
from region_verifier_engine import RegionVerifier
from PIL import Image
lock=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915/method_lock.json');selection=json.loads(lock.read_text())['selection'];engine=RegionVerifier();mask,raw,meta=engine.predict(a.image,a.attribute,selection,main_person=a.main_person)
Image.fromarray(mask.astype('uint8')*255).save(out/'mask.png');Image.fromarray(raw.astype('uint8')*255).save(out/'proposals.png');(out/'result.json').write_text(json.dumps(dict(image=a.image,image_sha256=hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),attribute=a.attribute,selection=selection,method_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest(),ground_truth_used=False,experimental=True,**meta),indent=2));print('Saved experimental result to',str(out))
