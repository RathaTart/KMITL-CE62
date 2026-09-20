"""Join per-camouflage-pattern IoU against the measured pattern properties.

Answers the question the roadmap asks: *which* camouflage defeats
language-guided segmentation, and is the difficulty predictable from a property
of the pattern rather than only observable after the fact?

Inputs:
    results/camouflage/per_image.csv   - one row per (image, prompt)
    results/dataset_analysis.json      - per-pattern statistics, no GPU needed

    python scripts/analyze_patterns.py
"""

import csv
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO_ROOT, "results", "camouflage", "per_image.csv")
STATS = os.path.join(REPO_ROOT, "results", "dataset_analysis.json")


def spearman(xs, ys):
    """Rank correlation, computed by hand to avoid a scipy dependency here.

    Rank correlation rather than Pearson because the relationship of interest is
    monotonic ("harder patterns score lower"), not necessarily linear, and n=20
    makes it sensitive to a single outlier.
    """
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def main():
    for p in (CSV, STATS):
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")

    # ---- per-pattern IoU, overall and per prompt --------------------------
    iou, by_prompt = {}, {}
    with open(CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("iou"):
                continue
            pat = row["item_id"].split("_")[0]
            iou.setdefault(pat, []).append(float(row["iou"]))
            by_prompt.setdefault(pat, {}).setdefault(row["prompt_id"], []).append(
                float(row["iou"])
            )

    stats = json.load(open(STATS, encoding="utf-8"))["camouflage"]["per_pattern"]

    def med(pat, key):
        v = stats.get(pat, {}).get(key)
        return v.get("median") if isinstance(v, dict) else v

    rows = []
    for pat in sorted(iou):
        vals = iou[pat]
        rows.append(
            dict(
                pattern=pat,
                name=stats.get(pat, {}).get("name", "?"),
                n=len(vals),
                miou=100 * sum(vals) / len(vals),
                contrast=stats.get(pat, {}).get("camo_contrast_median"),
                area=med(pat, "target_area_pct"),
                bbox=stats.get(pat, {}).get("bbox_side_px_median"),
                comps=stats.get(pat, {}).get("mean_components"),
                prompts={
                    k: 100 * sum(v) / len(v) for k, v in by_prompt[pat].items()
                },
            )
        )

    rows.sort(key=lambda r: r["miou"])

    print("\nPer-pattern mean IoU, hardest first")
    print(f"{'pattern':<11} {'name':<22} {'n':>3} {'mIoU':>6} "
          f"{'contrast':>9} {'area%':>7} {'bbox px':>8}")
    print("-" * 72)
    for r in rows:
        c = f"{r['contrast']:9.1f}" if r["contrast"] is not None else f"{'-':>9}"
        a = f"{r['area']:7.2f}" if r["area"] is not None else f"{'-':>7}"
        b = f"{r['bbox']:8.0f}" if r["bbox"] is not None else f"{'-':>8}"
        print(f"{r['pattern']:<11} {r['name'][:22]:<22} {r['n']:>3} "
              f"{r['miou']:6.1f} {c} {a} {b}")

    # ---- does any measured property predict difficulty? -------------------
    print("\nRank correlation of pattern difficulty (mean IoU) with:")
    for key, label in (
        ("contrast", "camo_contrast (target vs background)"),
        ("area", "target area % of frame"),
        ("bbox", "target bbox side, px"),
        ("comps", "mean connected components (fragmentation)"),
    ):
        pairs = [(r[key], r["miou"]) for r in rows if r[key] is not None]
        if len(pairs) < 5:
            print(f"  {label:<40} n/a")
            continue
        rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
        strength = (
            "strong" if abs(rho) >= 0.7 else
            "moderate" if abs(rho) >= 0.4 else
            "weak" if abs(rho) >= 0.2 else "negligible"
        )
        print(f"  {label:<40} rho = {rho:+.3f}  ({strength}, n={len(pairs)})")

    # ---- prompt effect on the hardest vs easiest patterns ----------------
    print("\nPrompt effect, hardest 5 patterns vs easiest 5")
    pids = sorted({p for r in rows for p in r["prompts"]})
    print(f"{'group':<14}" + "".join(f"{p:>15}" for p in pids))
    for label, sub in (("hardest 5", rows[:5]), ("easiest 5", rows[-5:])):
        line = f"{label:<14}"
        for p in pids:
            vs = [r["prompts"][p] for r in sub if p in r["prompts"]]
            line += f"{sum(vs)/len(vs):>15.1f}" if vs else f"{'-':>15}"
        print(line)


if __name__ == "__main__":
    sys.exit(main())
