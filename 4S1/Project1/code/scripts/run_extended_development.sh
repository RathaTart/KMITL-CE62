#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
P=/home/osta/blip2-qformer-eval/.venv/bin/python
D=results/extended_dev_20260915
while [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ]; do sleep 10; done
$P scripts/extended_training_free.py qwen --view lisa > "$D/qwen_lisa.log" 2>&1
$P scripts/extended_training_free.py qwen --view candidate > "$D/qwen_candidate.log" 2>&1
$P scripts/extended_blip.py > "$D/blip_presence.log" 2>&1
.venv/bin/python scripts/run_external_benchmark.py --phase lisa --out-dir results/training_free_extended_20260915 --max-new-tokens 16 --sam-encoder-device cuda --save-vis 0 > "$D/fresh_lisa.log" 2>&1
