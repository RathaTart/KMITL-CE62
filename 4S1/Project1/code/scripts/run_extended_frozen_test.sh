#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
P=/home/osta/blip2-qformer-eval/.venv/bin/python
D=results/extended_dev_20260915
F=results/training_free_extended_20260915
G=results/global_local_extended_20260915
T=results/extended_test_20260915
test -f "$D/method_lock.json"
while [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ]; do sleep 10; done
.venv/bin/python scripts/run_external_benchmark.py --phase lisa --out-dir "$F" --max-new-tokens 16 --sam-encoder-device cuda --save-vis 0 > "$D/fresh_lisa.log" 2>&1
$P scripts/global_local_selector.py candidates --source "$F" --out "$G" > "$D/fresh_candidates.log" 2>&1
$P scripts/global_local_selector.py masks --source "$F" --out "$G" > "$D/fresh_sam.log" 2>&1
$P scripts/bind_extended_fresh.py > "$D/fresh_bind.log" 2>&1
$P scripts/run_extended_selected_models.py > "$T/selected_stages.log" 2>&1
/home/osta/Yolo_World/.venv/bin/python /home/osta/Yolo_World/scripts/yoloworld_backend.py --dataset-dir "$F" --out-dir "$F/yolo" --vocab-source expression > "$T/yolo.log" 2>&1
$P scripts/run_external_benchmark.py --phase sam --out-dir "$F/yolo/p3_expression" > "$T/yolo_sam.log" 2>&1
/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python scripts/zoom_attribute_export.py --source "$F" --out "$F/zoom" > "$T/zoom.log" 2>&1
.venv/bin/python scripts/render_extended_pipeline.py > "$T/render.log" 2>&1
.venv/bin/python scripts/score_extended_pipeline.py > "$T/score.log" 2>&1
.venv/bin/python scripts/export_extended_evidence.py > "$T/export.log" 2>&1
