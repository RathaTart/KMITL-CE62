#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
P=/home/osta/blip2-qformer-eval/.venv/bin/python
F=results/training_free_fresh_20260914
G=results/global_local_fresh_20260914
wait_gpu() {
  while [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ]; do sleep 10; done
}
# Existing development SAM mask generation must finish before this launcher.
wait_gpu
$P scripts/global_local_selector.py features
$P scripts/global_local_selector.py choose
$P scripts/proposal_agreement.py choose
wait_gpu
.venv/bin/python scripts/run_external_benchmark.py --phase lisa --out-dir "$F" --max-new-tokens 16 --sam-encoder-device cuda --save-vis 0
wait_gpu
$P scripts/global_local_selector.py candidates --source "$F" --out "$G"
wait_gpu
$P scripts/global_local_selector.py masks --source "$F" --out "$G"
wait_gpu
$P scripts/global_local_selector.py features --source "$F" --out "$G"
$P scripts/global_local_selector.py render --source "$F" --out "$G" --lock results/global_local_dev_20260914/method_lock.json
$P scripts/proposal_agreement.py render --source "$F" --proposals "$G" --out "$F/agreement" --lock results/agreement_dev_20260914/method_lock.json
wait_gpu
/home/osta/Yolo_World/.venv/bin/python /home/osta/Yolo_World/scripts/yoloworld_backend.py --dataset-dir "$F" --out-dir "$F/yolo" --vocab-source expression
wait_gpu
$P scripts/run_external_benchmark.py --phase sam --out-dir "$F/yolo/p3_expression"
wait_gpu
/home/osta/ZoomNeXt/ZoomNeXt/.venv/bin/python scripts/zoom_attribute_export.py --source "$F" --out "$F/zoom"
.venv/bin/python scripts/score_training_free_fresh.py
