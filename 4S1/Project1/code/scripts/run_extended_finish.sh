#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
P=/home/osta/blip2-qformer-eval/.venv/bin/python
D=results/extended_dev_20260915
F=results/training_free_extended_20260915
T=results/extended_test_20260915
while kill -0 "$1" 2>/dev/null; do sleep 10; done
test -f "$D/method_lock.json"
test -f "$T/manifest.json"
$P scripts/run_extended_selected_models.py > "$T/selected_stages.log" 2>&1
/home/osta/Yolo_World/.venv/bin/python /home/osta/Yolo_World/scripts/yoloworld_backend.py --dataset-dir "$F" --out-dir "$F/yolo" --vocab-source expression > "$T/yolo.log" 2>&1
$P scripts/run_external_benchmark.py --phase sam --out-dir "$F/yolo/p3_expression" > "$T/yolo_sam.log" 2>&1
/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python scripts/zoom_attribute_export.py --source "$F" --out "$F/zoom" > "$T/zoom.log" 2>&1
.venv/bin/python scripts/render_extended_pipeline.py > "$T/render.log" 2>&1
.venv/bin/python scripts/score_extended_pipeline.py > "$T/score.log" 2>&1
