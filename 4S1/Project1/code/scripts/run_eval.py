"""Evaluate LISA-7B-v1 on ReasonSeg val (the paper's own benchmark) or on the
locally supplied CamouflageData / drone imagery.

Examples
--------
# reproduce the paper's benchmark on a 50-image sample of ReasonSeg val
python scripts/run_eval.py --task reasonseg --limit 50

# camouflaged-person segmentation, 3 prompt phrasings, 40 images
python scripts/run_eval.py --task camouflage --limit 40

# qualitative only (no ground truth)
python scripts/run_eval.py --task drone

Outputs land in results/<task>/: per-image CSV, aggregate JSON, predicted masks
and side-by-side overlays.
"""

import argparse
import csv
import json
import os
import random
import sys
import time

import cv2
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lisa_engine import LisaEngine, overlay, read_image_rgb  # noqa: E402
from metrics import aggregate, per_image_metrics  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(REPO_ROOT)

DEFAULT_MODEL = os.path.join(REPO_ROOT, "weights", "LISA-7B-v1")
DEFAULT_CLIP = os.path.join(REPO_ROOT, "weights", "clip-vit-large-patch14")
REASONSEG_VAL = os.path.join(REPO_ROOT, "data", "reason_seg", "ReasonSeg", "val")
CAMO_ROOT = os.path.join(
    PROJECT_ROOT, "dataset", "Military Personnel Dataset dataset", "CamouflageData"
)
DRONE_ROOT = os.path.join(PROJECT_ROOT, "dataset", "drone")

# Three phrasings of the same intent, from plain referring to LISA-style
# reasoning. Comparing them isolates how much of the result is prompt-driven.
CAMO_PROMPTS = {
    "p1_referring": "Please segment the person in this image.",
    "p2_explicit": "Please segment the camouflaged soldier hiding in this image.",
    "p3_reasoning": (
        "Who is hiding in this scene by wearing clothing that blends into the "
        "background? Please output segmentation mask."
    ),
}

DRONE_PROMPTS = {
    "p1_referring": "Please segment the car in this image.",
    "p2_explicit": "Please segment the vehicle that is hidden or covered in this image.",
    "p3_reasoning": (
        "Which object in this aerial view is a vehicle concealed under cover? "
        "Please output segmentation mask."
    ),
}


def load_reasonseg_items(limit, seed):
    """ReasonSeg val: <stem>.jpg + <stem>.json with polygons and instructions.

    The instruction lives in the json (`text` / `is_sentence`) and needs no
    image, so nothing is decoded here - only `gt_spec` is recorded, and the mask
    is rasterised later in the loop from the image that is read there anyway.
    ReasonSeg images run up to 28 MP; materialising 200 target+ignore mask pairs
    up front costs well over a gigabyte of RAM for no benefit.
    """
    stems = sorted(
        os.path.splitext(f)[0] for f in os.listdir(REASONSEG_VAL) if f.endswith(".jpg")
    )
    rng = random.Random(seed)
    rng.shuffle(stems)
    if limit:
        stems = stems[:limit]

    items = []
    for stem in sorted(stems):
        img_path = os.path.join(REASONSEG_VAL, stem + ".jpg")
        json_path = os.path.join(REASONSEG_VAL, stem + ".json")
        with open(json_path, "r", encoding="utf-8", errors="replace") as fh:
            anno = json.load(fh)
        sents, is_sentence = anno["text"], anno["is_sentence"]
        # Phrasing copied verbatim from LISA/utils/dataset.py::ValDataset - the
        # *evaluation* wording, which differs from the randomised training
        # templates in utils/utils.py. Using the training templates instead would
        # make the numbers non-comparable with the paper.
        instruction = (sents[0] if isinstance(sents, list) else sents).strip()
        query = (
            "{} Please output segmentation mask.".format(instruction)
            if is_sentence
            else "What is {} in this image? Please output segmentation mask.".format(
                instruction
            )
        )
        items.append(
            dict(
                item_id=stem,
                prompt_id="paper_query",
                image_path=img_path,
                instruction=query,
                gt_spec=("reasonseg", json_path),
            )
        )
    return items


def load_camouflage_items(limit, seed, prompts):
    """Stratified sample across the 20 camouflage patterns, with binary GT."""
    img_dir, gt_dir = os.path.join(CAMO_ROOT, "img"), os.path.join(CAMO_ROOT, "gt")
    by_pattern = {}
    for f in sorted(os.listdir(img_dir)):
        if f.lower().endswith((".jpg", ".png")):
            by_pattern.setdefault(f.split("_")[0], []).append(f)

    rng = random.Random(seed)
    per_pattern = max(1, (limit or 40) // len(by_pattern))
    chosen = []
    for pattern in sorted(by_pattern):
        files = by_pattern[pattern]
        chosen.extend(rng.sample(files, min(per_pattern, len(files))))
    chosen = sorted(chosen)[: (limit or len(chosen))]

    items = []
    for f in chosen:
        stem = os.path.splitext(f)[0]
        gt_path = os.path.join(gt_dir, stem + ".png")
        if not os.path.exists(gt_path):
            continue
        for pid, text in prompts.items():
            items.append(
                dict(
                    item_id=stem,
                    prompt_id=pid,
                    image_path=os.path.join(img_dir, f),
                    instruction=text,
                    gt_spec=("binary_png", gt_path),
                )
            )
    return items


def load_drone_items(limit, prompts):
    """Qualitative only - the drone stills ship without segmentation masks."""
    files = sorted(f for f in os.listdir(DRONE_ROOT) if f.lower().endswith(".png"))
    if limit:
        files = files[:limit]
    items = []
    for f in files:
        for pid, text in prompts.items():
            items.append(
                dict(
                    item_id=os.path.splitext(f)[0],
                    prompt_id=pid,
                    image_path=os.path.join(DRONE_ROOT, f),
                    instruction=text,
                    gt_spec=None,
                )
            )
    return items


def resolve_gt(item, image):
    """Build (gt, ignore) for one item, at the moment it is scored.

    Returns (None, None) for the qualitative tasks that ship no masks.
    """
    spec = item.get("gt_spec")
    if spec is None:
        return None, None

    kind, path = spec
    if kind == "binary_png":
        gt_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if gt_img is None:
            return None, None
        return gt_img > 127, None

    if kind == "reasonseg":
        # 1 = target, 255 = ignore. See metrics.py for why 255 has to come out
        # of both the numerator and the denominator.
        sys.path.insert(0, os.path.join(REPO_ROOT, "LISA"))
        from utils.data_processing import get_mask_from_json

        mask, _, _ = get_mask_from_json(path, image)
        return mask == 1, mask == 255

    raise ValueError("unknown gt_spec kind: {!r}".format(kind))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["reasonseg", "camouflage", "drone"])
    ap.add_argument("--model_path", default=DEFAULT_MODEL)
    ap.add_argument("--clip_path", default=DEFAULT_CLIP)
    ap.add_argument("--quantization", default="4bit", choices=["none", "8bit", "4bit"])
    ap.add_argument("--sam_encoder_device", default="cpu", choices=["cuda", "cpu"])
    ap.add_argument("--sam_cpu_dtype", default="fp32", choices=["fp32", "bf16"])
    ap.add_argument(
        "--quantize_seg_projection",
        action="store_true",
        help="quantise text_hidden_fcs too (upstream's behaviour). Off by "
        "default: it is the [SEG]->SAM prompt bridge and costs only 25 MB to "
        "keep in fp16. Turn on to reproduce upstream or to run the ablation.",
    )
    ap.add_argument("--precision", default="fp16", choices=["fp32", "fp16", "bf16"])
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max_new_tokens", type=int, default=64)
    ap.add_argument("--save_vis", type=int, default=12, help="how many overlays to save")
    ap.add_argument("--out_dir", default=None)
    args = ap.parse_args()

    out_dir = args.out_dir or os.path.join(REPO_ROOT, "results", args.task)
    os.makedirs(os.path.join(out_dir, "vis"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "masks"), exist_ok=True)

    if args.task == "reasonseg":
        items = load_reasonseg_items(args.limit, args.seed)
    elif args.task == "camouflage":
        items = load_camouflage_items(args.limit, args.seed, CAMO_PROMPTS)
    else:
        items = load_drone_items(args.limit, DRONE_PROMPTS)
    print(f"[eval] task={args.task}  items={len(items)}", flush=True)

    engine = LisaEngine(
        model_path=args.model_path,
        clip_path=args.clip_path,
        precision=args.precision,
        quantization=args.quantization,
        sam_encoder_device=args.sam_encoder_device,
        sam_cpu_dtype=args.sam_cpu_dtype,
        quantize_seg_projection=args.quantize_seg_projection,
    )
    print(f"[eval] model loaded, VRAM allocated {engine.peak_vram_gb():.2f} GB", flush=True)

    rows, saved_vis = [], 0
    t_start = time.time()

    # Append every scored item to a JSONL as it completes. A camouflage or
    # ReasonSeg sweep runs for hours at ~45 s/image, and per_image.csv plus
    # summary.json are only written at the very end - so without this, an
    # interruption at item 179 of 180 loses everything. The JSONL is the
    # recovery path, not the reported artifact.
    stream_path = os.path.join(out_dir, "per_image.jsonl")
    stream = open(stream_path, "w", encoding="utf-8")
    for idx, item in enumerate(items, 1):
        image = read_image_rgb(item["image_path"])
        if image is None:
            print("[eval] SKIP unreadable " + item["image_path"], flush=True)
            continue
        gt, ignore = resolve_gt(item, image)
        result = engine.segment(image, item["instruction"], args.max_new_tokens)

        mask = np.zeros(image.shape[:2], dtype=bool)
        for m in result["masks"]:
            mask |= m

        row = dict(
            item_id=item["item_id"],
            prompt_id=item["prompt_id"],
            image=os.path.basename(item["image_path"]),
            instruction=item["instruction"],
            answer=result["text"],
            emitted_seg=result["emitted_seg"],
            n_seg=len(result["masks"]),
            latency_s=round(result["latency_s"], 3),
        )
        if gt is not None:
            row.update(per_image_metrics(mask, gt, ignore))

        rows.append(row)
        stream.write(json.dumps(row, ensure_ascii=False) + chr(10))
        stream.flush()

        tag = f"{item['item_id']}__{item['prompt_id']}"
        cv2.imwrite(
            os.path.join(out_dir, "masks", tag + ".png"), mask.astype(np.uint8) * 255
        )
        if saved_vis < args.save_vis:
            panels = [image, overlay(image, mask, (255, 0, 0))]
            if gt is not None:
                panels.append(overlay(image, gt, (0, 255, 0)))
            vis = cv2.cvtColor(np.concatenate(panels, axis=1), cv2.COLOR_RGB2BGR)
            cv2.imwrite(os.path.join(out_dir, "vis", tag + ".jpg"), vis)
            saved_vis += 1

        iou_txt = f" IoU={row['iou']:.3f}" if "iou" in row else ""
        print(
            f"[{idx}/{len(items)}] {tag}{iou_txt} "
            f"{result['latency_s']:.1f}s :: {result['text'][:70]}",
            flush=True,
        )

    stream.close()

    with open(os.path.join(out_dir, "per_image.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "task": args.task,
        "model": os.path.basename(args.model_path),
        "quantization": args.quantization,
        "sam_encoder_device": args.sam_encoder_device,
        "sam_cpu_dtype": args.sam_cpu_dtype,
        "quantize_seg_projection": args.quantize_seg_projection,
        "seed": args.seed,
        "max_new_tokens": args.max_new_tokens,
        "gpu": torch.cuda.get_device_name(0),
        "peak_vram_gb": round(engine.peak_vram_gb(), 2),
        "total_wall_s": round(time.time() - t_start, 1),
        "overall": aggregate([r for r in rows if "iou" in r]),
        "by_prompt": {
            pid: aggregate([r for r in rows if r["prompt_id"] == pid and "iou" in r])
            for pid in sorted({r["prompt_id"] for r in rows})
        },
        "seg_emit_rate_all": sum(1 for r in rows if r["emitted_seg"]) / max(1, len(rows)),
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
