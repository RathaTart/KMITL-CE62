"""Turn results/<task>/summary.json into the tables for progress report item 2
("ทดสอบผลตามงานที่ศึกษาด้วยตนเอง").

Emits Markdown to stdout and to results/report_tables.md, so the numbers pasted
into the .docx can always be regenerated from the run artifacts rather than
retyped by hand.
"""

import csv
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO_ROOT, "results")

# LISA paper, Table 1, ReasonSeg val "overall".
PAPER = {"LISA-7B": (44.4, 46.0), "LISA-7B (ft)": (52.9, 54.0)}


def load(task):
    path = os.path.join(RESULTS, task, "summary.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}"


def fmt_agg(name, agg):
    return (
        f"| {name} | {agg.get('n_images', 0)} | {pct(agg.get('gIoU'))} | "
        f"{pct(agg.get('cIoU'))} | {pct(agg.get('mean_dice'))} | "
        f"{pct(agg.get('mean_precision'))} | {pct(agg.get('mean_recall'))} | "
        f"{pct(agg.get('iou_at_50'))} | {agg.get('mean_latency_s', 0):.1f} |"
    )


HEADER = (
    "| กรณีทดสอบ | ภาพ | gIoU | cIoU | Dice | Precision | Recall | IoU≥0.5 | เวลา/ภาพ (วินาที) |\n"
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
)


def main():
    out = []
    rs = load("reasonseg")
    if rs:
        out += [
            "## 1) ทดสอบซ้ำบนชุดข้อมูลต้นฉบับของ LISA (ReasonSeg val)",
            "",
            "| Method | gIoU | cIoU | ที่มา |",
            "| --- | ---: | ---: | --- |",
        ]
        for k, (g, c) in PAPER.items():
            out.append(f"| {k} | {g} | {c} | Lai et al., 2024 – Table 1 |")
        agg = rs.get("overall", {})
        out.append(
            f"| LISA-7B-v1 (ทดสอบเอง, 4-bit) | {pct(agg.get('gIoU'))} | "
            f"{pct(agg.get('cIoU'))} | การทดลองนี้ ({agg.get('n_images', 0)} ภาพ) |"
        )
        out += ["", HEADER, fmt_agg("ReasonSeg val", agg), ""]

    for task, title in (
        ("camouflage", "## 2) ทดสอบกับชุดข้อมูล CamouflageData (บุคคลพรางตัว)"),
        ("drone", "## 3) ภาพจากโดรน (ไม่มี ground truth – เชิงคุณภาพ)"),
    ):
        s = load(task)
        if not s:
            continue
        out += [title, ""]
        if s.get("overall"):
            out += [HEADER, fmt_agg("รวมทุก prompt", s["overall"])]
            for pid, agg in s.get("by_prompt", {}).items():
                if agg:
                    out.append(fmt_agg(pid, agg))
            out.append("")
        out += [
            f"- อัตราการสร้างโทเค็น `[SEG]`: {100 * s.get('seg_emit_rate_all', 0):.1f}%",
            f"- หน่วยความจำ GPU สูงสุด: {s.get('peak_vram_gb', 0):.2f} GB บน {s.get('gpu', '-')}",
            f"- เวลารวม: {s.get('total_wall_s', 0):.0f} วินาที",
            "",
        ]

    # Per-camouflage-pattern breakdown: which of the 20 patterns defeat LISA.
    camo_csv = os.path.join(RESULTS, "camouflage", "per_image.csv")
    if os.path.exists(camo_csv):
        by_pattern = {}
        with open(camo_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("iou"):
                    continue
                by_pattern.setdefault(row["item_id"].split("_")[0], []).append(
                    float(row["iou"])
                )
        if by_pattern:
            out += [
                "### IoU แยกตามลายพราง (เรียงจากยากไปง่าย)",
                "",
                "| ชุด | จำนวน | mean IoU |",
                "| --- | ---: | ---: |",
            ]
            ranked = sorted(by_pattern.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
            for pattern, vals in ranked:
                out.append(
                    f"| {pattern} | {len(vals)} | {100 * sum(vals) / len(vals):.1f} |"
                )
            out.append("")

    text = "\n".join(out) if out else "No results found - run scripts/run_eval.py first."
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "report_tables.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    sys.exit(main())
