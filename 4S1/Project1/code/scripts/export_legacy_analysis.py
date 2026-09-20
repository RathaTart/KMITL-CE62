"""Export legacy presentation aggregates on the authorized remote host only."""
import ast, csv, json, os, socket
from pathlib import Path
import cv2
import numpy as np

if 'cenara70hx' not in socket.gethostname().lower():
    raise SystemExit('Run the aggregate export on cenara70hx only.')
ROOT=Path('/home/osta/lisa-eval/code')
RESULTS=str(ROOT/'results')
PIPELINE_RESULTS=str(ROOT/'results/blip2_grounded_sam')
EXTERNAL_RESULTS={k:str(ROOT/'results'/v) for k,v in {'grefcoco':'grefcoco_pilot_p1_p2','mots_small_person':'mots_small_person_pilot_p1_p2','mots_surveillance_person60':'mots_small_person_p1_p2'}.items()}
source=Path(__file__).with_name('server_source.py').read_text()
tree=ast.parse(source)
keep={'load_rows','load_summary','spearman','prediction','read_jsonl_by_key','load_pipeline_rows','pipeline_rows','external_rows','build_analysis'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in keep]
for n in nodes:n.decorator_list=[]
presets=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROMPT_PRESETS' for t in n.targets))
exec(compile(ast.Module(body=[presets]+nodes,type_ignores=[]),'legacy_export','exec'))
PIPELINE_ROWS=None
original_load_rows=load_rows
# No new processing of excluded drone imagery; existing files remain archival.
def load_rows(task):
    return [] if task=='drone' else original_load_rows(task)
out=build_analysis()
out['provenance']={'host':socket.gethostname(),'purpose':'legacy website cached presentation','drone':'excluded from new processing','source':'saved results; no new model inference'}
target=ROOT/'results/portal_legacy_20260915'
target.mkdir(exist_ok=True)
(target/'analysis.json').write_text(json.dumps(out))
print({k:v for k,v in out['counts'].items()})

