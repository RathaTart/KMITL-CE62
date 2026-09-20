#!/usr/bin/env bash
set -euo pipefail

# Dedicated environment: upgrading Transformers in the LISA environment would
# break its vendored 2023 LLaVA code.  Copying the already-working CUDA venv
# avoids another 2.5 GB torch download while keeping both stacks isolated.
BENCH_ROOT="${1:-$HOME/blip2-qformer-eval}"
LISA_VENV="$HOME/lisa-eval/code/.venv"
BENCH_VENV="$BENCH_ROOT/.venv"

mkdir -p "$BENCH_ROOT"

if [[ ! -x "$BENCH_VENV/bin/python" ]]; then
  cp -a "$LISA_VENV" "$BENCH_VENV"
fi

"$BENCH_VENV/bin/python" -m pip install --upgrade \
  "transformers==4.49.0" \
  "accelerate==1.2.1" \
  "huggingface-hub>=0.27,<0.30" \
  "safetensors>=0.4.5" \
  "sentencepiece>=0.2.0" \
  "protobuf>=4.25,<6"

"$BENCH_VENV/bin/python" - <<'PY'
import torch
import transformers
import accelerate
import bitsandbytes

assert torch.cuda.is_available(), "CUDA is required for this benchmark"
print("torch", torch.__version__)
print("transformers", transformers.__version__)
print("accelerate", accelerate.__version__)
print("bitsandbytes", bitsandbytes.__version__)
print("gpu", torch.cuda.get_device_name(0))
PY
