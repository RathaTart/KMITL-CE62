#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
export HF_HUB_OFFLINE=1
PY=/home/osta/blip2-qformer-eval/.venv/bin/python
OUT=results/attribute_pilot_20260914
CUSTOM=results/attribute_custom_20260914
for stage in prepare direct candidates verify masks score; do
  "$PY" scripts/attribute_pilot.py "$stage" --custom --out "$CUSTOM"
done
"$PY" scripts/attribute_pilot.py prompt_fixed
/home/osta/Yolo_World/.venv/bin/python /home/osta/Yolo_World/scripts/yoloworld_backend.py \
  --dataset-dir "$OUT/direct" --out-dir "$OUT/yolo" --vocab-source expression --conf-threshold 0.05
"$PY" scripts/run_blip2_grounded_sam.py --phase sam --out-dir "$OUT/yolo/p3_expression"
for target in "$CUSTOM" "$OUT"; do
  "$PY" scripts/context_selector.py --out "$target"
  "$PY" scripts/run_blip2_grounded_sam.py --phase sam --out-dir "$target/context"
  "$PY" scripts/top1_ablation.py --out "$target"
done
"$PY" scripts/attribute_pilot.py score
"$PY" scripts/attribute_pilot.py score --custom --out "$CUSTOM"
"$PY" scripts/audit_attribute_results.py
