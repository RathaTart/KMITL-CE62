"""Does keeping only the largest connected component improve the masks?

Motivated by an observed failure mode rather than a guess. On
dataset20_07_00009552 the prediction had almost exactly the right *area*
(3241 px vs 3276 px of ground truth) yet IoU 0.000: instead of localising one
figure, the model spread fragments across camouflage-textured foliage while the
soldier stood elsewhere in the frame. Ground truth for this dataset is always a
single person, i.e. one connected blob, so a diffuse multi-component prediction
is structurally wrong whatever its area.

This re-scores every saved mask under two zero-cost post-processing rules and
reports the change. It needs no GPU and no re-inference - it reads the masks
`run_eval.py` already wrote.

    python scripts/postprocess_experiment.py
"""

import csv
import os
import sys

import cv2
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(REPO_ROOT)
CAMO = os.path.join(
    PROJECT_ROOT, "dataset", "Military Personnel Dataset dataset", "CamouflageData"
)
RES = os.path.join(REPO_ROOT, "results", "camouflage")

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from metrics import aggregate, per_image_metrics  # noqa: E402


def largest_component(mask):
    """Keep only the biggest 4-connected blob."""
    if not mask.any():
        return mask
    n, lab = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
    if n <= 2:  # background + one component
        return mask
    sizes = [(lab == i).sum() for i in range(1, n)]
    return lab == (1 + int(np.argmax(sizes)))


def n_components(mask):
    if not mask.any():
        return 0
    n, _ = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
    return n - 1


def main():
    rows = list(csv.DictReader(open(os.path.join(RES, "per_image.csv"), encoding="utf-8")))
    if not rows:
        raise SystemExit("no per_image.csv - run the camouflage task first")

    base, largest, comps = [], [], []
    for r in rows:
        item, prompt = r["item_id"], r["prompt_id"]
        mp = os.path.join(RES, "masks", f"{item}__{prompt}.png")
        gp = os.path.join(CAMO, "gt", item + ".png")
        if not (os.path.exists(mp) and os.path.exists(gp)):
            continue
        pred = cv2.imread(mp, cv2.IMREAD_GRAYSCALE) > 127
        gt = cv2.imread(gp, cv2.IMREAD_GRAYSCALE) > 127

        b = per_image_metrics(pred, gt)
        b.update(prompt_id=prompt, item_id=item, emitted_seg=True)
        base.append(b)

        lc = largest_component(pred)
        l = per_image_metrics(lc, gt)
        l.update(prompt_id=prompt, item_id=item, emitted_seg=True)
        largest.append(l)

        comps.append((n_components(pred), b["iou"]))

    def line(tag, agg):
        return (f"| {tag:<34} | {agg['n_images']:>4} | {100*agg['gIoU']:>6.2f} | "
                f"{100*agg['cIoU']:>6.2f} | {100*agg['mean_dice']:>6.2f} | "
                f"{100*agg['iou_at_50']:>6.2f} |")

    hdr = (f"| {'variant':<34} | {'n':>4} | {'gIoU':>6} | {'cIoU':>6} | "
           f"{'Dice':>6} | {'IoU>50':>6} |")
    print("\n" + hdr)
    print("|" + "-" * 36 + "|" + "-" * 6 + "|" + ("-" * 8 + "|") * 4)
    ab, al = aggregate(base), aggregate(largest)
    print(line("as-published (all components)", ab))
    print(line("largest connected component only", al))
    print(f"\ndelta: gIoU {100*(al['gIoU']-ab['gIoU']):+.2f}  "
          f"cIoU {100*(al['cIoU']-ab['cIoU']):+.2f}  "
          f"Dice {100*(al['mean_dice']-ab['mean_dice']):+.2f}  "
          f"IoU>=0.5 {100*(al['iou_at_50']-ab['iou_at_50']):+.2f} pts")

    print("\nper prompt, largest-component rule:")
    print(hdr)
    print("|" + "-" * 36 + "|" + "-" * 6 + "|" + ("-" * 8 + "|") * 4)
    for pid in sorted({r["prompt_id"] for r in base}):
        b = aggregate([r for r in base if r["prompt_id"] == pid])
        l = aggregate([r for r in largest if r["prompt_id"] == pid])
        print(line(f"{pid} before", b))
        print(line(f"{pid} after", l))

    # Is fragmentation itself a failure signal? If diffuse masks are the bad
    # ones, component count is a usable confidence proxy - available at
    # inference time, with no ground truth needed.
    print("\nmask fragmentation vs accuracy:")
    print(f"| {'components in prediction':<34} | {'n':>4} | {'mean IoU':>8} |")
    print("|" + "-" * 36 + "|" + "-" * 6 + "|" + "-" * 10 + "|")
    for lo, hi, lab in ((0, 0, "0 (empty)"), (1, 1, "1"), (2, 3, "2-3"),
                        (4, 9, "4-9"), (10, 10**9, "10+")):
        sel = [i for c, i in comps if lo <= c <= hi]
        if sel:
            print(f"| {lab:<34} | {len(sel):>4} | {100*sum(sel)/len(sel):>8.2f} |")


if __name__ == "__main__":
    sys.exit(main())
