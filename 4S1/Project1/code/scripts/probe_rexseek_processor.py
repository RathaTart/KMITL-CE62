import sys,json,platform
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code');sys.path.insert(0,str(root/'research_vendors/rexseek-runtime/packages'))
import numpy as np
from PIL import Image
from transformers import AutoConfig,AutoProcessor
path=root/'research_vendors/rexseek-runtime/model';cfg=AutoConfig.from_pretrained(path,local_files_only=True,trust_remote_code=True);p=AutoProcessor.from_pretrained(path,local_files_only=True,trust_remote_code=True)
i=json.loads((root/'results/extended_dev_20260915/manifest.json').read_text())['items'][0];x=p.process(image=Image.open(i['image']).convert('RGB'),question='Please detect '+i['expression']+' in this image. Answer the question with object indexes.',bbox=np.load(i['proposals'])['boxes'].tolist());print({k:list(v.shape) for k,v in x.items()});print('RexSeek processor/config compatible',cfg.model_type)
