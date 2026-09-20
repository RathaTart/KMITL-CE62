#!/usr/bin/env bash
# Complete the two external P1/P2 pilot benchmarks on cenara70hx. Run every
# model serially because the GPU has 8 GB.
set -euo pipefail

ROOT="${ROOT:-/home/osta/lisa-eval/code}"
P1_PY="${P1_PY:-$ROOT/.venv/bin/python}"
P2_PY="${P2_PY:-/home/osta/blip2-qformer-eval/.venv/bin/python}"
export HF_HOME="${HF_HOME:-/home/osta/blip2-qformer-eval/hf-cache}"
RUNNER="$ROOT/scripts/run_external_benchmark.py"
GREF="$ROOT/results/grefcoco_pilot_p1_p2"
MOTS="$ROOT/results/mots_small_person_pilot_p1_p2"

cd "$ROOT"

"$P1_PY" "$RUNNER" --phase lisa --out-dir "$GREF" --max-new-tokens 16
"$P2_PY" "$RUNNER" --phase blip2 --out-dir "$GREF"
"$P2_PY" "$RUNNER" --phase grounding --out-dir "$GREF"
"$P2_PY" "$RUNNER" --phase sam --out-dir "$GREF"
"$P2_PY" "$RUNNER" --phase score --out-dir "$GREF"

"$P1_PY" "$RUNNER" --phase lisa --out-dir "$MOTS" --max-new-tokens 16
"$P2_PY" "$RUNNER" --phase blip2 --out-dir "$MOTS"
"$P2_PY" "$RUNNER" --phase grounding --out-dir "$MOTS"
"$P2_PY" "$RUNNER" --phase sam --out-dir "$MOTS"
"$P2_PY" "$RUNNER" --phase score --out-dir "$MOTS"

echo "EXTERNAL BENCHMARKS COMPLETE"
