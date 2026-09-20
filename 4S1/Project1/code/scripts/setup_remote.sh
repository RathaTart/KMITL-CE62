#!/usr/bin/env bash
# Bootstrap the LISA evaluation harness on a Linux GPU box (e.g. cenara70hx).
#
# Run this ON THE REMOTE, after the project files have been pushed across. Only
# two things have to travel over the tunnel:
#
#     CamouflageData  (123 MB)  - our own dataset, not downloadable anywhere
#     code/scripts/   (188 KB)  - this harness
#
# Everything else is fetched from its origin by the remote itself, which is the
# whole point of moving the work here: the LISA checkpoint is 16 GB and the
# laptop's link stalls on files that size.
#
# From the laptop (PowerShell), with $U set to the remote username:
#
#   $K = "$HOME\.ssh\lisa_cenara70hx"; $R = "100.69.21.71"
#   ssh -i $K $U@$R 'mkdir -p ~/lisa-eval/code/scripts ~/lisa-eval/dataset'
#   scp -i $K -r code\scripts\*                     ${U}@${R}:~/lisa-eval/code/scripts/
#   scp -i $K code\requirements-inference.txt       ${U}@${R}:~/lisa-eval/code/
#   scp -i $K -r "dataset\Military Personnel Dataset dataset" ${U}@${R}:~/lisa-eval/dataset/
#   ssh -i $K $U@$R 'bash ~/lisa-eval/code/scripts/setup_remote.sh'
#
# Idempotent: re-running skips whatever is already in place.

set -euo pipefail

ROOT="${LISA_ROOT:-$HOME/lisa-eval}"
CODE="$ROOT/code"
VENV="$CODE/.venv"
PY="$VENV/bin/python"

echo "=== 0. what are we running on ==============================================="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv || {
    echo "!! nvidia-smi failed - no usable GPU here. Stopping."; exit 1; }
echo "CPU cores : $(nproc)"
echo "RAM       : $(free -g | awk '/^Mem:/{print $2" GB total, "$7" GB available"}')"
echo "Disk      : $(df -h "$HOME" | awk 'NR==2{print $4" free on "$6}')"
echo
echo "Need ~25 GB free: 16 GB checkpoint + 1.7 GB CLIP + 271 MB ReasonSeg + venv."

# ---------------------------------------------------------------------------
# 1. Python 3.11. Not 3.12: transformers 4.31 needs tokenizers<0.14, which has
#    no cp312 wheel and cannot be built for 3.12 (PyO3 0.18 predates it).
# ---------------------------------------------------------------------------
echo
echo "=== 1. python ==============================================================="
PYBIN=""
for cand in python3.11 python3.10; do
    if command -v "$cand" >/dev/null 2>&1; then PYBIN="$cand"; break; fi
done
if [ -z "$PYBIN" ]; then
    echo "No python3.11/3.10 found. Installing a private 3.11 via uv (no root needed)."
    command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    uv python install 3.11
    # --seed installs pip into the venv; without it "$PY -m pip" does not exist.
    uv venv --seed --python 3.11 "$VENV"
else
    echo "Using $PYBIN ($("$PYBIN" -V))"
    [ -x "$PY" ] || "$PYBIN" -m venv "$VENV"
fi
"$PY" -V

# ---------------------------------------------------------------------------
# 2. Dependencies. On Linux the PyPI torch wheels already bundle CUDA, so there
#    is no need for the download.pytorch.org detour the Windows side requires.
# ---------------------------------------------------------------------------
echo
echo "=== 2. dependencies ========================================================="
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet \
    "torch==2.4.1" "torchvision==0.19.1" \
    "transformers==4.31.0" "accelerate==0.21.0" "huggingface_hub==0.25.2" \
    "bitsandbytes==0.45.5" "sentencepiece==0.2.0" "einops==0.8.0" \
    "numpy==1.26.4" "opencv-python-headless==4.10.0.84" "Pillow==10.4.0" \
    "scipy==1.14.1" "tqdm==4.66.5" "matplotlib==3.9.2" "pandas==2.2.3"

"$PY" - <<'PYCHECK'
import torch, transformers, tokenizers
print("torch       ", torch.__version__, "| cuda", torch.version.cuda,
      "| available", torch.cuda.is_available())
assert torch.cuda.is_available(), "CUDA not visible to torch - stop and fix this first"
p = torch.cuda.get_device_properties(0)
print("gpu         ", p.name, round(p.total_memory / 1024**3, 2), "GiB")
print("transformers", transformers.__version__, "| tokenizers", tokenizers.__version__)
PYCHECK

# ---------------------------------------------------------------------------
# 3. Upstream LISA. Vendored as-is; never edited. Device and precision changes
#    belong in lisa_engine.py, which patches at runtime.
# ---------------------------------------------------------------------------
echo
echo "=== 3. LISA source =========================================================="
if [ -d "$CODE/LISA/.git" ] || [ -f "$CODE/LISA/chat.py" ]; then
    echo "already present"
else
    git clone --depth 1 https://github.com/dvlab-research/LISA.git "$CODE/LISA"
fi

# ---------------------------------------------------------------------------
# 4. Weights + ReasonSeg, fetched by the remote over its own link.
# ---------------------------------------------------------------------------
echo
echo "=== 4. weights and benchmark data ==========================================="
HF_HUB_DISABLE_XET=1 "$PY" - <<'PYDL'
import os
from huggingface_hub import snapshot_download

root = os.path.join(os.environ.get("LISA_ROOT", os.path.expanduser("~/lisa-eval")), "code")

jobs = [
    ("xinlai/LISA-7B-v1", os.path.join(root, "weights", "LISA-7B-v1"), None),
    ("openai/clip-vit-large-patch14", os.path.join(root, "weights", "clip-vit-large-patch14"),
     ["*.h5", "*.msgpack", "*.onnx", "flax_model*", "*.safetensors"]),
]
for repo, dst, ignore in jobs:
    print(f"[dl] {repo} -> {dst}", flush=True)
    snapshot_download(repo_id=repo, local_dir=dst, ignore_patterns=ignore, max_workers=8)

# fcxfcx/ReasonSeg, not xinlai/ReasonSeg - the latter does not exist as a
# dataset repo and 401s. The official release is a Google Drive folder; this
# mirror keeps the exact layout LISA/utils/data_processing.py expects.
ds = os.path.join(root, "data", "reason_seg", "ReasonSeg")
print(f"[dl] ReasonSeg -> {ds}", flush=True)
snapshot_download(repo_id="fcxfcx/ReasonSeg", repo_type="dataset", local_dir=ds,
                  allow_patterns=["val/*", "explanatory/*"], max_workers=8)
print("ALL DOWNLOADS COMPLETE", flush=True)
PYDL

# The checkpoint is two pickle shards; a truncated download fails later with an
# opaque unpickling error, so check the size before trusting it.
#
# index.json's metadata.total_size counts TENSOR bytes only, while the .bin
# files also carry pickle + zip container overhead - so a *correct* checkpoint
# is slightly LARGER than total_size (~328 KB more, measured). Hence >=, not ==.
"$PY" - <<'PYVERIFY'
import glob, json, os, sys

root = os.path.join(os.environ.get("LISA_ROOT", os.path.expanduser("~/lisa-eval")), "code")
d = os.path.join(root, "weights", "LISA-7B-v1")
want = json.load(open(os.path.join(d, "pytorch_model.bin.index.json")))["metadata"]["total_size"]
got = sum(os.path.getsize(f) for f in glob.glob(os.path.join(d, "*.bin")))
print(f"checkpoint: {got} bytes on disk, {want} declared as tensor bytes")
if got < want:
    sys.exit(f"TRUNCATED - re-run this script to resume ({want - got} bytes short)")
print("checkpoint size OK")
PYVERIFY

# ---------------------------------------------------------------------------
# 5. Confirm our own dataset arrived intact.
# ---------------------------------------------------------------------------
echo
echo "=== 5. CamouflageData ======================================================="
CAMO="$ROOT/dataset/Military Personnel Dataset dataset/CamouflageData"
if [ -d "$CAMO/img" ]; then
    echo "img: $(find "$CAMO/img" -type f | wc -l) files (expect 1000)"
    echo "gt : $(find "$CAMO/gt"  -type f | wc -l) files (expect 1000)"
else
    echo "!! MISSING - copy it across before running the camouflage task:"
    echo "   scp -r 'dataset\\Military Personnel Dataset dataset' user@host:~/lisa-eval/dataset/"
fi

cat <<EOF

=== done ====================================================================
Next, on this machine:

  cd $ROOT
  $PY code/scripts/smoke_test.py --sam_encoder_device cuda

If the GPU has >= 16 GB, drop the 6 GB workarounds entirely and prefer
--sam_encoder_device cuda (much faster; identical output, the encoder is frozen):

  $PY code/scripts/run_eval.py --task camouflage --limit 60 \\
      --quantization 4bit --sam_encoder_device cuda
  $PY code/scripts/run_eval.py --task reasonseg --limit 200 \\
      --quantization 4bit --sam_encoder_device cuda

Then pull the artifacts back to the laptop:

  scp -i \$K -r ${USER}@HOST:$ROOT/code/results/* code\\results\\
EOF
