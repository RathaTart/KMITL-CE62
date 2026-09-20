"""Run the locked primary pipeline on any remote image and description.

All stages run serially on cenara70hx. Refuses to overwrite prior output.
"""
import argparse,hashlib,json,os,platform,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image
assert platform.node()=='cenara70hx','Run through the remote host; local inference is disabled'
os.environ.setdefault('HF_HOME','/home/osta/blip2-qformer-eval/hf-cache')
ROOT=Path('/home/osta/lisa-eval/code');P='/home/osta/blip2-qformer-eval/.venv/bin/python';L=str(ROOT/'.venv/bin/python')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--text',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--lock',type=Path,default=ROOT/'results/extended_dev_20260915/method_lock.json');a=p.parse_args()
assert a.image.resolve().is_file();assert a.text.strip();assert not a.out.exists(),'Use a new output directory';assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU is busy; run after the experiment queue finishes'
a.out=a.out.resolve();a.out.mkdir(parents=True);lock=json.loads(a.lock.read_text());cfg=lock['variants'][lock['primary']];single=dict(lock,variants={lock['primary']:cfg},source_full_lock_sha256=hashlib.sha256(a.lock.read_bytes()).hexdigest());singlepath=a.out/'primary_lock.json';singlepath.write_text(json.dumps(single,indent=2))
i=dict(key='custom::expression',item_id='custom',prompt_id='expression',image=str(a.image.resolve()),expression=a.text.strip(),lisa_instruction=a.text.strip()+' Please output segmentation mask.',blip2_instruction=a.text.strip());manifest=dict(items=[i],status='User-supplied inference; no ground-truth annotation consumed');(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2));commands=[];start=time.perf_counter()
def run(cmd):
    commands.append(cmd)
    with (a.out/'run.log').open('a') as f:subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
verifier=cfg.get('verifier');verifier_sources=(verifier.get('sources') or [verifier['source']]) if verifier else []
need_lisa=not cfg.get('selector') or 'qwen_lisa' in verifier_sources
if need_lisa:run([L,'scripts/run_external_benchmark.py','--phase','lisa','--out-dir',str(a.out),'--max-new-tokens','16','--sam-encoder-device','cuda','--save-vis','0'])
else:
    im=Image.open(i['image']);folder=a.out/'p1_masks';folder.mkdir();Image.new('L',im.size).save(folder/'custom__expression.png');(a.out/'p1_rows.jsonl').write_text(json.dumps(dict(key=i['key'],answer='LISA stage omitted: primary uses independent selector',emitted_seg=False))+'\n')
props=a.out/'person_proposals'
run([P,'scripts/global_local_selector.py','candidates','--source',str(a.out),'--out',str(props)]);run([P,'scripts/global_local_selector.py','masks','--source',str(a.out),'--out',str(props)])
i.update(lisa_mask=str(a.out/'p1_masks/custom__expression.png'),proposals=str(props/'proposals/custom__expression.npz'));(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2));required=set()
if cfg.get('verifier'):required.update(verifier_sources)
choice=cfg.get('selector') or cfg.get('correction')
if choice:required.add('qwen_candidate' if choice['family'].startswith('qwen') else 'rexseek_clauses' if choice['family'].startswith('rexseek_clauses') else 'rexseek')
for source in sorted(required):
    if source.startswith('qwen_'):run([P,'scripts/extended_training_free.py','qwen','--view',source.removeprefix('qwen_'),'--out',str(a.out)])
    elif source=='blip_presence':run([P,'scripts/extended_blip.py','--out',str(a.out)])
    elif source=='rexseek_clauses':run([P,'scripts/extended_rexseek_clauses.py','--out',str(a.out)])
    else:run([P,'scripts/extended_rexseek.py','--out',str(a.out)])
run([L,'scripts/render_extended_pipeline.py','--out',str(a.out),'--lock',str(singlepath)])
maskpath=a.out/'predictions'/lock['primary']/'masks/custom__expression.png';mask=np.asarray(Image.open(maskpath))>0;rgb=np.asarray(Image.open(i['image']).convert('RGB'));overlay=np.where(mask[:,:,None],(.5*rgb+.5*np.array([255,103,55])).astype('uint8'),rgb);Image.fromarray(overlay).save(a.out/'overlay.png')
audit=json.loads((a.out/'prediction_audit.json').read_text())[0]
result=dict(response_valid=audit['valid'],decisions=audit['decisions'],expression=a.text,mask=str(maskpath),overlay=str(a.out/'overlay.png'),predicted_pixels=int(mask.sum()),end_to_end_seconds=time.perf_counter()-start,includes='process startup, model loading, image preprocessing, all required inference stages, mask rendering and overlay export; checkpoint download excluded',commands=commands,lisa_stage_required=need_lisa,training=False,annotation_used=False,source_lock_sha256=single['source_full_lock_sha256']);(a.out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))



