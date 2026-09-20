#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
F=results/router_confirm_20260915
P=/home/osta/blip2-qformer-eval/.venv/bin/python
$P scripts/lock_router_controls.py > results/router_controls.log 2>&1
.venv/bin/python scripts/run_router_lisa.py --out-dir "$F" --max-new-tokens 16 --sam-encoder-device cuda > "$F/lisa.log" 2>&1
/home/osta/Yolo_World/.venv/bin/python /home/osta/Yolo_World/scripts/yoloworld_backend.py --dataset-dir "$F" --out-dir "$F/yolo" --vocab-source expression > "$F/yolo.log" 2>&1
$P scripts/run_external_benchmark.py --phase sam --out-dir "$F/yolo/p3_expression" > "$F/sam.log" 2>&1
/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python scripts/zoom_attribute_export.py --source "$F" --out "$F/zoom" > "$F/zoom.log" 2>&1
$P scripts/extended_training_free.py qwen --view presence --out "$F" > "$F/presence.log" 2>&1
