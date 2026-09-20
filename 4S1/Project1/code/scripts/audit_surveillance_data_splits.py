"""Read-only source split audit, remote CPU only; no models or evaluation tuning."""
import csv, hashlib, json, platform
from pathlib import Path
if platform.node()!='cenara70hx': raise SystemExit('Remote only')
base=Path('/home/osta/ZoomNeXt/datasets/MyPersonSplit')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
splits={s:{p.name:sha(p) for p in (base/s/'Image').iterdir() if p.is_file()} for s in ['train','val','test']}
patterns={s:sorted({n.split('_')[0] for n in files}) for s,files in splits.items()}
rows=list(csv.DictReader(Path('results/camouflage/per_image.csv').open()))
names=sorted({r['image'] for r in rows}); source=Path('/home/osta/lisa-eval/dataset/Military Personnel Dataset dataset/CamouflageData')
originals={p.name:p for p in source.rglob('*') if p.is_file() and p.name in names}
overlap={s:[n for n in names if n in files and n in originals and sha(originals[n])==files[n]] for s,files in splits.items()}
result=dict(status='completed',host=platform.node(),meaning='Data provenance only. Presence in a training directory does not independently prove a checkpoint consumed that file.',split_counts={s:len(v) for s,v in splits.items()},pattern_prefixes=patterns,split_hash_intersections={a+'__'+b:len(set(splits[a].values())&set(splits[b].values())) for a,b in [('train','val'),('train','test'),('val','test')]},historical_camouflage_images=len(names),historical_originals_found=len(originals),historical_byte_identical_overlap_counts={s:len(v) for s,v in overlap.items()},historical_byte_identical_overlap_names=overlap,script_sha256=sha(Path(__file__)))
log=Path('/home/osta/ZoomNeXt/ZoomNeXt/outputs/EffB1_ZoomNeXt_BS2_LR2e-05_E30_H384_W384_OPMadam_OPGMfinetune_SCstep_AMP_INFOfinetune_person/exp_2/log_2026-08-25.txt')
result['checkpoint_training_log']=dict(path=str(log),sha256=sha(log),evidence=[dict(line=j,text=s) for j,s in enumerate(log.read_text().splitlines(),1) if 'MyPersonSplit/train' in s or 'Length of my_person_tr' in s or "'my_person_tr'," in s],limitation='Historical log records the training path and size; this audit cannot prove those directory contents never changed after training.')
out=Path('results/surveillance_data_audit_20260914');out.mkdir(exist_ok=True);(out/'split_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
