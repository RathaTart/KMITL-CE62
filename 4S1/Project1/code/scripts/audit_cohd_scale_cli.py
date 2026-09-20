import platform,json,subprocess,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_scale_20260915';checks=[]
for stage,manifest in [('confirmation','confirmation_manifest.json'),('language','language_manifest.json')]:
 item=json.loads((O/manifest).read_text())['items'][0];out=O/('cli_'+stage)
 subprocess.run([sys.executable,str(C/'scripts/infer_cohd_scale.py'),'--image',item['image'],'--text',item['expression'],'--method','scale704_guard','--out',str(out)],check=True)
 reference=O/stage/'scale704_guard'/(item['item_id']+'.png');same=np.array_equal(np.asarray(Image.open(out/'mask.png')),np.asarray(Image.open(reference)));assert same
 checks.append(dict(stage=stage,item_id=item['item_id'],pixel_identical=same))
lock=json.loads((O/'method_lock.json').read_text());unchanged={path:hashlib.sha256(Path(path).read_bytes()).hexdigest()==value for path,value in lock['hashes'].items()};assert all(unchanged.values())
(O/'cli_audit.json').write_text(json.dumps(dict(checks=checks,locked_files_unchanged=unchanged),indent=2));print('CLI and frozen method checks passed')
