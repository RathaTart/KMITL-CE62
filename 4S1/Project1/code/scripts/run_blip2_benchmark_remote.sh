#!/usr/bin/env bash
set -euo pipefail

# cenara70hx-only orchestration for the paired 60-image benchmark.  Every model
# stage is resumable; re-running this file skips completed JSONL rows and masks.
BENCH_PY="$HOME/blip2-qformer-eval/.venv/bin/python"
RUNNER="$HOME/lisa-eval/code/scripts/run_blip2_grounded_sam.py"
OUT_DIR="$HOME/lisa-eval/code/results/blip2_grounded_sam"

export HF_HOME="$HOME/blip2-qformer-eval/hf-cache"

"$BENCH_PY" "$RUNNER" --phase prepare --out-dir "$OUT_DIR" --limit 60
"$BENCH_PY" "$RUNNER" --phase blip2 --out-dir "$OUT_DIR"
"$BENCH_PY" "$RUNNER" --phase grounding --out-dir "$OUT_DIR" \
  --box-threshold 0.25 --text-threshold 0.25
"$BENCH_PY" "$RUNNER" --phase sam --out-dir "$OUT_DIR"
"$BENCH_PY" "$RUNNER" --phase score --out-dir "$OUT_DIR"
