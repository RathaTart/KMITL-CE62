"""Aggregate a run from `per_image.jsonl`, finished or not.

`run_eval.py` only writes `summary.json` at the very end, so a sweep that is
still going - or one that was interrupted - has no aggregate. This reads the
incremental JSONL instead and prints the same gIoU / cIoU pair, so a long run can
be reported on at any point.

    python scripts/summarize.py camouflage
    python scripts/summarize.py reasonseg --json
    python scripts/summarize.py --path some/other/per_image.jsonl

Numbers from a partial run are partial. The `n_images` and `progress` fields are
printed for exactly that reason - never quote a gIoU without them.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics import aggregate  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LISA paper, Table 1, ReasonSeg val "overall".
PAPER = {"LISA-7B": (44.4, 46.0), "LISA-7B (ft)": (52.9, 54.0)}


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # A partially flushed final line is expected while a run is live.
                pass
    return rows


def fmt(name, agg, width=26):
    if not agg:
        return f"| {name:<{width}} | {'-':>5} | {'-':>6} | {'-':>6} | {'-':>6} | {'-':>6} | {'-':>6} |"
    return (
        f"| {name:<{width}} | {agg['n_images']:>5} | {100*agg['gIoU']:>6.2f} | "
        f"{100*agg['cIoU']:>6.2f} | {100*agg['mean_dice']:>6.2f} | "
        f"{100*agg['iou_at_50']:>6.2f} | {agg['mean_latency_s']:>6.1f} |"
    )


HEAD = (
    f"| {'group':<26} | {'n':>5} | {'gIoU':>6} | {'cIoU':>6} | {'Dice':>6} | "
    f"{'IoU>50':>6} | {'sec/im':>6} |"
)
RULE = "|" + "-" * 28 + "|" + "-" * 7 + "|" + ("-" * 8 + "|") * 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default="camouflage")
    ap.add_argument("--path", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--expected", type=int, default=0, help="total items, for progress")
    args = ap.parse_args()

    path = args.path or os.path.join(
        REPO_ROOT, "results", args.task, "per_image.jsonl"
    )
    if not os.path.exists(path):
        raise SystemExit(f"no such file: {path}")

    rows = load(path)
    scored = [r for r in rows if "iou" in r]
    if not rows:
        raise SystemExit("no rows yet")

    overall = aggregate(scored)
    by_prompt = {
        pid: aggregate([r for r in scored if r["prompt_id"] == pid])
        for pid in sorted({r["prompt_id"] for r in rows})
    }
    # CamouflageData ids are <pattern>_<clip>_<frame>, so the pattern is field 0.
    by_pattern = {}
    for r in scored:
        by_pattern.setdefault(r["item_id"].split("_")[0], []).append(r)

    out = {
        "task": args.task,
        "n_rows": len(rows),
        "n_scored": len(scored),
        "seg_emit_rate_all": sum(1 for r in rows if r.get("emitted_seg")) / len(rows),
        "overall": overall,
        "by_prompt": by_prompt,
        "by_pattern": {k: aggregate(v) for k, v in sorted(by_pattern.items())},
    }
    if args.expected:
        out["progress"] = f"{len(rows)}/{args.expected}"

    if args.json:
        print(json.dumps(out, indent=2))
        return

    print(f"\n=== {args.task} ===  {len(rows)} inferences"
          + (f" of {args.expected}" if args.expected else "")
          + f", {len(scored)} scored")
    print(f"[SEG] emit rate: {100*out['seg_emit_rate_all']:.1f}%   "
          f"(a mask-less answer scores IoU 0, so read this next to gIoU)")
    print()
    print(HEAD)
    print(RULE)
    print(fmt("OVERALL", overall))
    for pid, agg in by_prompt.items():
        print(fmt("  " + pid, agg))

    # Only meaningful when ids actually share a prefix, i.e. CamouflageData's
    # 20 patterns over 180 rows. ReasonSeg ids are unique per image, so the
    # grouping would just restate the per-image table.
    if 1 < len(by_pattern) <= max(1, len(scored) // 2):
        print()
        print("per camouflage pattern, hardest first:")
        print(HEAD)
        print(RULE)
        ranked = sorted(out["by_pattern"].items(), key=lambda kv: kv[1].get("gIoU", 1))
        for pat, agg in ranked:
            print(fmt("  " + pat, agg))

    if args.task == "reasonseg" and overall:
        print()
        print("against the paper (Table 1, ReasonSeg val overall):")
        for k, (g, c) in PAPER.items():
            print(f"  {k:<28} gIoU {g:>5.1f}  cIoU {c:>5.1f}   Lai et al. 2024")
        print(f"  {'this run (4-bit, partial)':<28} "
              f"gIoU {100*overall['gIoU']:>5.1f}  cIoU {100*overall['cIoU']:>5.1f}")
        print("  NOTE: LISA-7B-v1 was trained on ReasonSeg train+val, so this is")
        print("        a pipeline sanity check, NOT a clean reproduction.")


if __name__ == "__main__":
    sys.exit(main())
