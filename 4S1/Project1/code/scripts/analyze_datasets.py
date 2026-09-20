"""Characterise the two evaluation sets before any model is run.

This answers "what is LISA actually being asked to do here?" quantitatively, and
the numbers are what make the later IoU results interpretable: on CamouflageData
the targets are tiny and low-contrast, which bounds what any segmenter can score
and explains why gIoU and cIoU must both be reported.

Deliberately depends only on numpy + Pillow + scipy, so it runs on the system
Python with no CUDA and no downloads. Polygon rasterisation mirrors
LISA/utils/data_processing.py: polygons sorted by area descending, "ignore"
labels burned as 255, everything else as 1.

    python scripts/analyze_datasets.py
"""

import json
import os
import statistics
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(REPO_ROOT)
CAMO = os.path.join(
    PROJECT_ROOT, "dataset", "Military Personnel Dataset dataset", "CamouflageData"
)
REASONSEG = os.path.join(REPO_ROOT, "data", "reason_seg", "ReasonSeg", "val")
OUT = os.path.join(REPO_ROOT, "results", "dataset_analysis.json")

PATTERN_NAMES = {}
_stmt = os.path.join(CAMO, "Camouﬂage pattern statement.txt")
if os.path.exists(_stmt):
    with open(_stmt, encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(",.")
            if "-" in line:
                key, _, name = line.partition("-")
                PATTERN_NAMES[key.strip()] = name.strip()


def q(values, p):
    return float(np.percentile(values, p)) if len(values) else float("nan")


def summarise(values):
    if not values:
        return {}
    return {
        "n": len(values),
        "min": float(min(values)),
        "p25": q(values, 25),
        "median": float(statistics.median(values)),
        "p75": q(values, 75),
        "max": float(max(values)),
        "mean": float(statistics.fmean(values)),
    }


def camouflage_contrast(rgb, mask):
    """How well does the target blend into what immediately surrounds it?

    Mean RGB distance between the target pixels and a ring of background around
    them. A low value means the soldier's colours match the local scene - the
    literal definition of effective camouflage, and a direct predictor of how
    hard the instance is for a segmenter.
    """
    if not mask.any():
        return None
    ring = ndimage.binary_dilation(mask, iterations=15) & ~mask
    if not ring.any():
        return None
    fg = rgb[mask].astype(np.float64).mean(axis=0)
    bg = rgb[ring].astype(np.float64).mean(axis=0)
    return float(np.linalg.norm(fg - bg))


def analyse_camouflage():
    img_dir, gt_dir = os.path.join(CAMO, "img"), os.path.join(CAMO, "gt")
    if not os.path.isdir(img_dir):
        return None

    per_pattern = {}
    all_frac, all_contrast, all_components = [], [], []

    files = sorted(f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".png")))
    for i, fname in enumerate(files, 1):
        stem = os.path.splitext(fname)[0]
        pattern = stem.split("_")[0]
        gt_path = os.path.join(gt_dir, stem + ".png")
        if not os.path.exists(gt_path):
            continue

        mask = np.array(Image.open(gt_path).convert("L")) > 127
        rgb = np.array(Image.open(os.path.join(img_dir, fname)).convert("RGB"))
        frac = float(mask.mean())
        _, n_comp = ndimage.label(mask)
        contrast = camouflage_contrast(rgb, mask)

        rec = per_pattern.setdefault(
            pattern, {"frac": [], "contrast": [], "components": [], "bbox_px": []}
        )
        rec["frac"].append(frac)
        rec["components"].append(n_comp)
        if contrast is not None:
            rec["contrast"].append(contrast)
            all_contrast.append(contrast)
        if mask.any():
            ys, xs = np.where(mask)
            rec["bbox_px"].append(
                float(np.sqrt((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)))
            )
        all_frac.append(frac)
        all_components.append(n_comp)

        if i % 200 == 0:
            print(f"  camouflage {i}/{len(files)}", flush=True)

    patterns = {}
    for pattern, rec in sorted(per_pattern.items()):
        patterns[pattern] = {
            "name": PATTERN_NAMES.get(pattern, "?"),
            "n_images": len(rec["frac"]),
            "target_area_pct": {
                k: 100 * v for k, v in summarise(rec["frac"]).items() if k != "n"
            },
            "bbox_side_px_median": statistics.median(rec["bbox_px"]) if rec["bbox_px"] else None,
            "camo_contrast_median": statistics.median(rec["contrast"]) if rec["contrast"] else None,
            "mean_components": statistics.fmean(rec["components"]),
        }

    return {
        "n_images": len(all_frac),
        "n_patterns": len(patterns),
        "image_size": "854x480",
        "target_area_pct_overall": {
            k: 100 * v for k, v in summarise(all_frac).items() if k != "n"
        },
        "camo_contrast_overall": summarise(all_contrast),
        "components_overall": summarise([float(c) for c in all_components]),
        "per_pattern": patterns,
    }


def reasonseg_mask(anno, height, width):
    """Rasterise ReasonSeg polygons the way LISA's data_processing.py does."""
    shapes = [s for s in anno["shapes"] if s["label"].lower() != "flag"]
    areas = []
    for s in shapes:
        pts = [tuple(p) for p in s["points"]]
        tmp = Image.new("L", (width, height), 0)
        if len(pts) >= 2:
            ImageDraw.Draw(tmp).polygon(pts, fill=1, outline=1)
        areas.append(np.array(tmp).sum())

    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for _, s in sorted(zip(areas, shapes), key=lambda kv: -kv[0]):
        value = 255 if "ignore" in s["label"].lower() else 1
        pts = [tuple(p) for p in s["points"]]
        if len(pts) >= 2:
            draw.polygon(pts, fill=value, outline=value)
    return np.array(mask)


def analyse_reasonseg():
    if not os.path.isdir(REASONSEG):
        return None
    stems = sorted(
        os.path.splitext(f)[0] for f in os.listdir(REASONSEG) if f.endswith(".jpg")
    )
    fracs, words, ignore_frac, megapixels = [], [], [], []
    n_short = n_long = n_with_ignore = 0

    for i, stem in enumerate(stems, 1):
        with open(os.path.join(REASONSEG, stem + ".json"), encoding="utf-8", errors="replace") as f:
            anno = json.load(f)
        with Image.open(os.path.join(REASONSEG, stem + ".jpg")) as im:
            width, height = im.size
        mask = reasonseg_mask(anno, height, width)

        target = mask == 1
        ignore = mask == 255
        fracs.append(float(target.mean()))
        ignore_frac.append(float(ignore.mean()))
        n_with_ignore += int(ignore.any())
        megapixels.append(width * height / 1e6)

        text = anno["text"]
        text = text[0] if isinstance(text, list) else text
        words.append(len(str(text).split()))
        if anno["is_sentence"]:
            n_long += 1
        else:
            n_short += 1
        if i % 50 == 0:
            print(f"  reasonseg {i}/{len(stems)}", flush=True)

    return {
        "n_images": len(stems),
        "n_short_query": n_short,
        "n_long_query": n_long,
        "query_words": summarise([float(w) for w in words]),
        "target_area_pct": {k: 100 * v for k, v in summarise(fracs).items() if k != "n"},
        "images_with_ignore_region": n_with_ignore,
        "ignore_area_pct": {k: 100 * v for k, v in summarise(ignore_frac).items() if k != "n"},
        "megapixels": summarise(megapixels),
    }


def main():
    print("[analyse] ReasonSeg val ...", flush=True)
    reason = analyse_reasonseg()
    print("[analyse] CamouflageData ...", flush=True)
    camo = analyse_camouflage()

    result = {"reasonseg_val": reason, "camouflage": camo}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    if reason:
        print("\n=== ReasonSeg val ===")
        print(f"  images            : {reason['n_images']} "
              f"({reason['n_short_query']} short / {reason['n_long_query']} long query)")
        print(f"  query length      : median {reason['query_words']['median']:.0f} words "
              f"(max {reason['query_words']['max']:.0f})")
        print(f"  target area       : median {reason['target_area_pct']['median']:.2f}% "
              f"of frame (p25 {reason['target_area_pct']['p25']:.2f} / "
              f"p75 {reason['target_area_pct']['p75']:.2f})")
        print(f"  images w/ ignore  : {reason['images_with_ignore_region']}")
        print(f"  resolution        : median {reason['megapixels']['median']:.2f} MP")

    if camo:
        print("\n=== CamouflageData ===")
        t = camo["target_area_pct_overall"]
        print(f"  images            : {camo['n_images']} over {camo['n_patterns']} patterns")
        print(f"  target area       : median {t['median']:.3f}% of frame "
              f"(p25 {t['p25']:.3f} / p75 {t['p75']:.3f} / max {t['max']:.2f})")
        c = camo["camo_contrast_overall"]
        print(f"  camo contrast     : median {c['median']:.1f} RGB units vs local background")
        print("\n  hardest patterns (smallest targets):")
        ranked = sorted(
            camo["per_pattern"].items(), key=lambda kv: kv[1]["target_area_pct"]["median"]
        )
        for key, rec in ranked[:5]:
            print(f"    {key} {rec['name'][:34]:34s} "
                  f"area {rec['target_area_pct']['median']:.3f}%  "
                  f"box ~{rec['bbox_side_px_median']:.0f}px  "
                  f"contrast {rec['camo_contrast_median']:.1f}")
        print("\n  lowest contrast (best-blended) patterns:")
        for key, rec in sorted(
            camo["per_pattern"].items(), key=lambda kv: kv[1]["camo_contrast_median"]
        )[:5]:
            print(f"    {key} {rec['name'][:34]:34s} "
                  f"contrast {rec['camo_contrast_median']:.1f}  "
                  f"area {rec['target_area_pct']['median']:.3f}%")

    print(f"\n[analyse] written to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
