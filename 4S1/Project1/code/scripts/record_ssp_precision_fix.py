import json,platform,shutil,time,hashlib
from pathlib import Path
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/released_checkpoints_20260915';old=O/'initial_half_precision';old.mkdir(exist_ok=True)
for n in ['comparison.json','paired.json','per_expression.json','audit.json','examples.png','examples.json']:
 if (O/n).exists() and not (old/n).exists():shutil.copy2(O/n,old/n)
a=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),methods=['SSP_SAM_224_AMP','CoHD_Tiny'],reason='Correct numeric inference compatibility: whole SAM .half() changed embeddings substantially. Use float32 weights with autocast only in SAM image encoder. No checkpoint weights, mask thresholds, data or architecture changed.',diagnostic='Same image and same prompt model: whole-half versus FP32 embedding MAE 0.09277, mask-logit MAE 2.402; AMP versus FP32 embedding MAE 0.00006348 and mask-logit MAE 0.001509. Diagnostics do not establish exact output equivalence on all images.',initial_run='initial_half_precision; not representative of released SSP-SAM full-precision reference',script_sha256=hashlib.sha256((C/'scripts/run_released_ssp_amp.py').read_bytes()).hexdigest())
p=O/'precision_addendum.json';assert not p.exists();p.write_text(json.dumps(a,indent=2))
