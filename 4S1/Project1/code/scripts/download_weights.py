"""Download the pretrained weights needed to run LISA-7B-v1 inference.

Downloads two things into code/weights/:
  * xinlai/LISA-7B-v1          (~15 GB) - LLaVA-7B + SAM ViT-H merged checkpoint
  * openai/clip-vit-large-patch14 (~1.7 GB) - CLIP vision tower used by LLaVA

Safe to re-run: snapshot_download resumes and skips files already present.
"""

import os
import sys

os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

from huggingface_hub import snapshot_download

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS = os.path.join(HERE, "weights")

TARGETS = [
    ("xinlai/LISA-7B-v1", "LISA-7B-v1", None),
    (
        "openai/clip-vit-large-patch14",
        "clip-vit-large-patch14",
        # skip the duplicate tf/flax/onnx copies of the weights
        ["*.h5", "*.msgpack", "*.onnx", "flax_model*"],
    ),
]


def main():
    os.makedirs(WEIGHTS, exist_ok=True)
    for repo_id, subdir, ignore in TARGETS:
        dst = os.path.join(WEIGHTS, subdir)
        print(f"[download] {repo_id} -> {dst}", flush=True)
        snapshot_download(
            repo_id=repo_id,
            local_dir=dst,
            local_dir_use_symlinks=False,
            ignore_patterns=ignore,
            max_workers=4,
            resume_download=True,
        )
        print(f"[done] {repo_id}", flush=True)
    print("ALL DOWNLOADS COMPLETE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
