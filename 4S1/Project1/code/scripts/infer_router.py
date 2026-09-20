"""Run an explicitly selected frozen router on an arbitrary remote image."""
import argparse,hashlib,json,os,platform,re,subprocess,time
from pathlib import Path
import numpy as np
from PIL import Image
from router_features import features,action_mask,training_free_action,ACTIONS
from router_model import load,decide
assert platform.node()=='cenara70hx'
os.environ.setdefault('HF_HOME','/home/osta/blip2-qformer-eval/hf-cache')
R=Path('/home/osta/lisa-eval/code');P='/home/osta/blip2-qformer-eval/.venv/bin/python';L=str(R/'.venv/bin/python');p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--text',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--method',choices=['Learned_primary','Learned_accuracy','Learned_no_zoom','TF_Zoom','TF_presence','LISA_cached'],default='Learned_primary');a=p.parse_args();assert not a.out.exists();assert a.image.is_file() and a.text.strip();assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU busy'
a.out=a.out.resolve();a.out.mkdir(parents=True);i=dict(key='custom::expression',item_id='custom',prompt_id='expression',image=str(a.image.resolve()),expression=a.text,lisa_instruction=a.text+' Please output segmentation mask.',blip2_instruction=a.text);(a.out/'manifest.json').write_text(json.dumps(dict(items=[i]),indent=2));loaded=load();steps=[];start=time.perf_counter()

def run(command):
    t=time.perf_counter()
    with (a.out/'run.log').open('a') as f:subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
    steps.append(dict(command=command,wall_seconds=time.perf_counter()-t))

if a.method not in ['LISA_cached','TF_presence']:
    run(['/home/osta/Yolo_World/.venv/bin/python','/home/osta/Yolo_World/scripts/yoloworld_backend.py','--dataset-dir',str(a.out),'--out-dir',str(a.out/'yolo'),'--vocab-source','expression'])
    if a.method!='Learned_no_zoom':run(['/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python','scripts/zoom_attribute_export.py','--source',str(a.out),'--out',str(a.out/'zoom')])
if a.method not in ['LISA_cached','TF_Zoom']:
    run([P,'scripts/extended_training_free.py','qwen','--view','presence','--out',str(a.out)]);r=json.loads((a.out/'qwen_presence.jsonl').read_text().splitlines()[0])['results'][0];i.update(presence_probability=r['yes_probability'],presence_logit=r['logit_yes_no'])
if a.method=='LISA_cached':action=0
elif a.method=='TF_presence':action=5 if i['presence_probability']<loaded[1]['presence_only']['threshold'] else 0
else:
    zm=a.out/'zoom/masks/custom__expression.png';zp=a.out/'zoom/probabilities/custom__expression.npy'
    if a.method=='Learned_no_zoom':
        shape=np.asarray(Image.open(a.image)).shape[:2];zm.parent.mkdir(parents=True);zp.parent.mkdir(parents=True);Image.fromarray(np.zeros(shape,dtype='uint8')).save(zm);np.save(zp,np.zeros(shape,dtype='float16'))
    i.update(zoom_mask=str(zm),zoom_probability=str(zp));yr=json.loads((a.out/'yolo/p3_expression/grounding_boxes.jsonl').read_text().splitlines()[0]);f=features(i,yr)
    action=training_free_action(f,loaded[0]['training_free']['config']) if a.method=='TF_Zoom' else decide(f,loaded)[a.method]
    if a.method=='Learned_no_zoom' and action in [2,3,4]:run(['/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python','scripts/zoom_attribute_export.py','--source',str(a.out),'--out',str(a.out/'zoom')])
if action==0:run([L,'scripts/run_router_lisa.py','--out-dir',str(a.out),'--max-new-tokens','16','--sam-encoder-device','cuda'])
elif action in [1,3,4]:run([P,'scripts/run_external_benchmark.py','--phase','sam','--out-dir',str(a.out/'yolo/p3_expression')])
rgb=np.asarray(Image.open(a.image).convert('RGB'));zero=np.zeros(rgb.shape[:2],bool)
def mask(path):return np.asarray(Image.open(path))>0 if path.exists() else zero
lisa=mask(a.out/'p1_masks/custom__expression.png');yolo=mask(a.out/'yolo/p3_expression/masks/custom__expression.png');zoom=mask(a.out/'zoom/masks/custom__expression.png');pred=action_mask(action,lisa,yolo,zoom);valid=True
if action==0:
    r=json.loads((a.out/'p1_rows.jsonl').read_text().splitlines()[0]);text=r['answer'].split('ASSISTANT:')[-1].lower();valid=bool(r['emitted_seg']) or bool(re.search(r'\bno (?:matching )?(?:person|people|man|woman|one)\b|not (?:present|visible)|\bnone\b',text))
Image.fromarray(pred.astype('uint8')*255).save(a.out/'mask.png');Image.fromarray(np.where(pred[:,:,None],(.5*rgb+.5*np.array([255,103,55])).astype('uint8'),rgb)).save(a.out/'overlay.png')
result=dict(method=a.method,action=ACTIONS[action],response_valid=valid,expression=a.text,end_to_end_seconds=time.perf_counter()-start,mask=str(a.out/'mask.png'),overlay=str(a.out/'overlay.png'),steps=steps,ground_truth_used=False,foundation_weights_updated=False,router_trained=a.method.startswith('Learned'),method_lock_sha256=hashlib.sha256((R/'results/router_dev_20260915/router_lock.json').read_bytes()).hexdigest(),timing_scope='One cold-process request including subprocess/model loading and mask rendering; not steady-state throughput');(a.out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

