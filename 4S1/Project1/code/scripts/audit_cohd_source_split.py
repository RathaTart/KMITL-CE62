import platform,json,hashlib
from pathlib import Path
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_upgrade_20260915';test=json.loads((C/'results/cohd_upgrade_test_20260915/manifest.json').read_text())['items'];refs=json.loads((C.parent/'dataset/grefcoco/grefs(unc).json').read_text());trainids={r['image_id'] for r in refs if r['split']=='train'};testids={i['image_id'] for i in test};p=O/'source_split_audit.json';p.write_text(json.dumps(dict(official_grefcoco_train_image_overlap=len(testids&trainids),test_images=len(testids),note='Annotation split audit only; does not establish absence from all pretraining datasets.'),indent=2));print(p.read_text())
