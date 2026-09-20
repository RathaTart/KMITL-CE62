set -e
PY=/home/osta/lisa-eval/released-models/.venv/bin/python
ROOT=/home/osta/lisa-eval/code
OUT=$ROOT/results/cohd_cctv_20260915
$PY $ROOT/scripts/evaluate_cctv_custom.py --manifest $OUT/test_manifest.json --out $OUT/test_results > $OUT/test.log 2>&1
$PY $ROOT/scripts/benchmark_cctv_custom.py > $OUT/runtime.log 2>&1
$PY $ROOT/scripts/evaluate_cctv_custom.py --manifest $OUT/regression_manifest.json --out $OUT/regression_results > $OUT/regression.log 2>&1
