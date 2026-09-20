"""Download the ReasonSeg val split - the benchmark LISA itself is evaluated on.

The official release is a Google Drive folder (not scriptable); fcxfcx/ReasonSeg
on the HF Hub mirrors it with the identical on-disk layout that
LISA/utils/data_processing.py expects:

    <split>/<image>.jpg  +  <split>/<image>.json   ("text", "is_sentence", "shapes")

Only `val` (200 images) and the explanatory answers are pulled; `test` (779) and
`train` (239) are left out to keep the download small.
"""

import os
import sys

from huggingface_hub import snapshot_download

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(HERE, "data", "reason_seg", "ReasonSeg")


def main():
    os.makedirs(DST, exist_ok=True)
    print(f"[download] fcxfcx/ReasonSeg (val + explanatory) -> {DST}", flush=True)
    snapshot_download(
        repo_id="fcxfcx/ReasonSeg",
        repo_type="dataset",
        local_dir=DST,
        allow_patterns=["val/*", "explanatory/*"],
        max_workers=8,
        resume_download=True,
    )
    n = len([f for f in os.listdir(os.path.join(DST, "val")) if f.endswith(".jpg")])
    print(f"REASONSEG VAL COMPLETE: {n} images", flush=True)


if __name__ == "__main__":
    sys.exit(main())
