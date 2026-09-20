"""End-to-end sanity check against the examples published in LISA's README.

Runs the exact image/prompt pairs upstream shows in its README and writes the
overlays next to upstream's own `vis_output/` renders, so the local 4-bit +
CPU-SAM setup can be compared against the published result *before* trusting any
benchmark number it produces.

    python scripts/smoke_test.py
"""

import argparse
import os
import sys
import time

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lisa_engine import LisaEngine, overlay, read_image_rgb  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGS = os.path.join(REPO_ROOT, "LISA", "imgs")

# (image, prompt) pairs taken verbatim from the upstream README table.
CASES = [
    ("example1.jpg", "Where can the driver see the car speed in this image? Please output segmentation mask."),
    ("example2.jpg", "Can you segment the food that tastes spicy and hot?"),
    ("obama.jpg", "Who was the president of the US in this image? Please output segmentation mask and explain the reason."),
    ("stand_higher.jpg", "What can make the woman stand higher? Please output segmentation mask and explain why."),
    ("dog_with_horn.jpg", "Can you segment the unusual part in this image and explain why."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", default=os.path.join(REPO_ROOT, "weights", "LISA-7B-v1"))
    ap.add_argument("--clip_path", default=os.path.join(REPO_ROOT, "weights", "clip-vit-large-patch14"))
    ap.add_argument("--quantization", default="4bit", choices=["none", "8bit", "4bit"])
    ap.add_argument("--sam_encoder_device", default="cpu", choices=["cuda", "cpu"])
    ap.add_argument("--sam_cpu_dtype", default="fp32", choices=["fp32", "bf16"])
    ap.add_argument("--quantize_seg_projection", action="store_true")
    ap.add_argument("--tag", default="", help="suffix for the output filenames")
    ap.add_argument("--max_new_tokens", type=int, default=128)
    ap.add_argument("--limit", type=int, default=len(CASES))
    args = ap.parse_args()

    out_dir = os.path.join(REPO_ROOT, "results", "smoke")
    os.makedirs(out_dir, exist_ok=True)

    t0 = time.time()
    engine = LisaEngine(
        model_path=args.model_path,
        clip_path=args.clip_path,
        quantization=args.quantization,
        sam_encoder_device=args.sam_encoder_device,
        sam_cpu_dtype=args.sam_cpu_dtype,
        quantize_seg_projection=args.quantize_seg_projection,
    )
    print(f"[smoke] loaded in {time.time() - t0:.0f}s, VRAM {engine.peak_vram_gb():.2f} GB", flush=True)

    for fname, prompt in CASES[: args.limit]:
        path = os.path.join(IMGS, fname)
        image = read_image_rgb(path)
        if image is None:
            print(f"[smoke] missing {path}")
            continue
        r = engine.segment(image, prompt, args.max_new_tokens)
        mask = np.zeros(image.shape[:2], dtype=bool)
        for m in r["masks"]:
            mask |= m
        cv2.imwrite(
            os.path.join(out_dir, fname.replace(".jpg", f"{args.tag}_pred.jpg")),
            cv2.cvtColor(np.concatenate([image, overlay(image, mask)], axis=1), cv2.COLOR_RGB2BGR),
        )
        print(
            f"[smoke] {fname}: {r['latency_s']:.1f}s  seg={r['emitted_seg']}  "
            f"mask_px={int(mask.sum())} ({100 * mask.mean():.2f}%)\n"
            f"         {r['text']}",
            flush=True,
        )

    print(f"[smoke] peak VRAM {engine.peak_vram_gb():.2f} GB / "
          f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
