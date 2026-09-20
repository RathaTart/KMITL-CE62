#!/usr/bin/env bash
set -euo pipefail
cd /home/osta/lisa-eval/code
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
P=/home/osta/blip2-qformer-eval/.venv/bin/python
D=results/extended_dev_20260915
F=results/training_free_extended_20260915
G=results/global_local_extended_20260915
while [ -n "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ]; do sleep 10; done
$P scripts/extended_training_free.py qwen --view candidate >> "$D/qwen_candidate.log" 2>&1
$P scripts/extended_blip.py > "$D/blip_presence.log" 2>&1
$P scripts/prepare_rexseek_model.py > "$D/rexseek_prepare.log" 2>&1
$P scripts/extended_rexseek.py --limit 1 > "$D/rexseek_smoke.log" 2>&1
$P scripts/extended_rexseek.py > "$D/rexseek.log" 2>&1
.venv/bin/python scripts/extended_candidate_sweep.py > "$D/candidate_sweep.log" 2>&1
.venv/bin/python scripts/extended_gate_sweep.py > "$D/gate_sweep.log" 2>&1
.venv/bin/python scripts/freeze_extended_pipeline.py --freeze > "$D/freeze.log" 2>&1
.venv/bin/python scripts/run_external_benchmark.py --phase lisa --out-dir "$F" --max-new-tokens 16 --sam-encoder-device cuda --save-vis 0 > "$D/fresh_lisa.log" 2>&1
$P scripts/global_local_selector.py candidates --source "$F" --out "$G" > "$D/fresh_candidates.log" 2>&1
$P scripts/global_local_selector.py masks --source "$F" --out "$G" > "$D/fresh_sam.log" 2>&1
$P scripts/bind_extended_fresh.py > "$D/fresh_bind.log" 2>&1
