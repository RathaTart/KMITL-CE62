"""Run and score P1 (LISA) and P2 (BLIP-2 -> DINO -> SAM) on a manifest.

The manifest is produced by ``prepare_external_benchmarks.py``.  Each phase is
resumable because the 8 GB remote GPU can only hold one large model at a time.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
CODE_ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from metrics import aggregate, per_image_metrics  # noqa: E402
from run_blip2_grounded_sam import (  # noqa: E402
    DEFAULT_BLIP2,
    DEFAULT_GROUNDING,
    DEFAULT_SAM,
    phase_blip2,
    phase_grounding,
    phase_sam,
)

DEFAULT_MODEL = CODE_ROOT / "weights" / "LISA-7B-v1"
DEFAULT_CLIP = CODE_ROOT / "weights" / "clip-vit-large-patch14"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def keyed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["key"]): row for row in rows}


def phase_lisa(args: argparse.Namespace) -> None:
    import torch
    from lisa_engine import LisaEngine, overlay, read_image_rgb

    manifest = read_json(args.out_dir / "manifest.json")
    items = manifest["items"][: args.max_items or None]
    rows_path = args.out_dir / "p1_rows.jsonl"
    done = keyed(read_jsonl(rows_path))
    mask_dir = args.out_dir / "p1_masks"
    vis_dir = args.out_dir / "p1_vis"
    mask_dir.mkdir(parents=True, exist_ok=True)
    vis_dir.mkdir(parents=True, exist_ok=True)

    engine = LisaEngine(
        model_path=str(args.model_path),
        clip_path=str(args.clip_path),
        precision=args.precision,
        quantization=args.quantization,
        sam_encoder_device=args.sam_encoder_device,
        sam_cpu_dtype=args.sam_cpu_dtype,
        quantize_seg_projection=args.quantize_seg_projection,
    )

    for idx, item in enumerate(items, 1):
        mask_path = mask_dir / f"{item['item_id']}__{item['prompt_id']}.png"
        if item["key"] in done and mask_path.exists():
            continue
        image = read_image_rgb(item["image"])
        if image is None:
            raise FileNotFoundError(item["image"])
        result = engine.segment(image, item["lisa_instruction"], args.max_new_tokens)
        pred = np.zeros(image.shape[:2], dtype=bool)
        for mask in result["masks"]:
            pred |= mask
        if not cv2.imwrite(str(mask_path), pred.astype(np.uint8) * 255):
            raise RuntimeError(f"Could not write {mask_path}")
        row = {
            "key": item["key"],
            "item_id": item["item_id"],
            "prompt_id": item["prompt_id"],
            "instruction": item["lisa_instruction"],
            "answer": result["text"],
            "emitted_seg": result["emitted_seg"],
            "n_seg": len(result["masks"]),
            "latency_s": float(result["latency_s"]),
            "mask": str(mask_path),
        }
        append_jsonl(rows_path, row)
        done[item["key"]] = row
        if idx <= args.save_vis:
            vis = cv2.cvtColor(overlay(image, pred, (255, 0, 0)), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(vis_dir / f"{item['item_id']}__{item['prompt_id']}.jpg"), vis)
        print(
            f"P1 {idx}/{len(items)} {item['key']} masks={len(result['masks'])} "
            f"px={int(pred.sum())} ({result['latency_s']:.2f}s)",
            flush=True,
        )

    write_json(
        args.out_dir / "p1_config.json",
        {
            "model": str(args.model_path),
            "precision": args.precision,
            "quantization": args.quantization,
            "sam_encoder_device": args.sam_encoder_device,
            "peak_vram_gb": round(engine.peak_vram_gb(), 3),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
    )


def relative_or_name(path: str, out_dir: Path) -> str:
    source = Path(path)
    try:
        return source.resolve().relative_to(out_dir.resolve()).as_posix()
    except ValueError:
        return source.name


def instance_coverage(pred: np.ndarray, paths: list[str]) -> tuple[float | None, int]:
    if not paths:
        return None, 0
    covered = 0
    valid = 0
    for path in paths:
        gt = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if gt is None or not (gt > 127).any():
            continue
        target = gt > 127
        valid += 1
        covered += float(np.logical_and(pred, target).sum()) / float(target.sum()) >= 0.5
    return (covered / valid if valid else None), valid


def person_detection_stats(pred: np.ndarray, paths: list[str]) -> dict[str, Any]:
    """Count labelled people covered by at least half of their visible pixels.

    P1 emits a semantic union mask rather than boxes or instance IDs, so this
    ground-truth-instance recall is the only identical person-level rule that
    can be applied to P1, P2, and the direct-DINO ablation.
    """
    bins = {
        "tiny_le_32px": {"total": 0, "detected": 0},
        "small_33_64px": {"total": 0, "detected": 0},
        "large_gt_64px": {"total": 0, "detected": 0},
    }
    total = detected = 0
    for path in paths:
        gt_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if gt_img is None:
            raise FileNotFoundError(path)
        target = gt_img > 127
        ys = np.flatnonzero(target.any(axis=1))
        if not len(ys):
            continue
        height = int(ys[-1] - ys[0] + 1)
        bucket = (
            "tiny_le_32px" if height <= 32
            else "small_33_64px" if height <= 64
            else "large_gt_64px"
        )
        coverage = float(np.logical_and(pred, target).sum()) / float(target.sum())
        hit = coverage >= 0.5
        total += 1
        detected += int(hit)
        bins[bucket]["total"] += 1
        bins[bucket]["detected"] += int(hit)
    return {
        "gt_people": total,
        "detected_people_50": detected,
        "missed_people_50": total - detected,
        "person_recall_50": detected / total if total else None,
        **{
            f"{name}_{field}": value
            for name, counts in bins.items()
            for field, value in counts.items()
        },
    }


def phase_direct_prepare(args: argparse.Namespace) -> None:
    direct_dir = args.out_dir / "p2_direct"
    direct_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(args.out_dir / "manifest.json")
    write_json(direct_dir / "manifest.json", manifest)
    answer_path = direct_dir / "blip2_answers.jsonl"
    done = keyed(read_jsonl(answer_path))
    for item in manifest["items"][: args.max_items or None]:
        if item["key"] in done:
            continue
        append_jsonl(answer_path, {
            "key": item["key"],
            "item_id": item["item_id"],
            "prompt_id": item["prompt_id"],
            "instruction": "Direct Grounding DINO class query: person.",
            "answer": "person",
            "grounding_query": "person.",
            "latency_s": 0.0,
        })
    write_json(direct_dir / "blip2_config.json", {
        "model": None,
        "mode": "fixed direct class query",
        "query": "person.",
        "peak_vram_gb": 0.0,
    })


def enhanced_surveillance_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stats = aggregate(rows)
    total = sum(int(row["gt_people"]) for row in rows)
    detected = sum(int(row["detected_people_50"]) for row in rows)
    stats.update(
        gt_people=total,
        detected_people_50=detected,
        missed_people_50=total - detected,
        person_recall_50=detected / total if total else None,
        false_positive_pixels=sum(int(row["false_positive_pixels"]) for row in rows),
        mean_boxes=(
            sum(int(row["n_boxes"]) for row in rows if row.get("n_boxes") is not None)
            / sum(1 for row in rows if row.get("n_boxes") is not None)
            if any(row.get("n_boxes") is not None for row in rows) else None
        ),
    )
    per_size = {}
    for name in ("tiny_le_32px", "small_33_64px", "large_gt_64px"):
        bucket_total = sum(int(row[f"{name}_total"]) for row in rows)
        bucket_detected = sum(int(row[f"{name}_detected"]) for row in rows)
        per_size[name] = {
            "gt_people": bucket_total,
            "detected_people_50": bucket_detected,
            "missed_people_50": bucket_total - bucket_detected,
            "person_recall_50": bucket_detected / bucket_total if bucket_total else None,
        }
    stats["by_person_size"] = per_size
    return stats


def phase_surveillance_score(args: argparse.Namespace) -> None:
    manifest = read_json(args.out_dir / "manifest.json")
    direct_dir = args.out_dir / "p2_direct"
    artifacts = {
        "p1": {
            "source": keyed(read_jsonl(args.out_dir / "p1_rows.jsonl")),
            "mask_dir": args.out_dir / "p1_masks",
        },
        "p2": {
            "answer": keyed(read_jsonl(args.out_dir / "blip2_answers.jsonl")),
            "boxes": keyed(read_jsonl(args.out_dir / "grounding_boxes.jsonl")),
            "sam": keyed(read_jsonl(args.out_dir / "sam_timings.jsonl")),
            "mask_dir": args.out_dir / "masks",
        },
        "p2_direct": {
            "answer": keyed(read_jsonl(direct_dir / "blip2_answers.jsonl")),
            "boxes": keyed(read_jsonl(direct_dir / "grounding_boxes.jsonl")),
            "sam": keyed(read_jsonl(direct_dir / "sam_timings.jsonl")),
            "mask_dir": direct_dir / "masks",
        },
    }
    rows_by_system: dict[str, list[dict[str, Any]]] = {name: [] for name in artifacts}

    for item in manifest["items"][: args.max_items or None]:
        key = item["key"]
        gt_img = cv2.imread(item["ground_truth"], cv2.IMREAD_GRAYSCALE)
        if gt_img is None:
            raise FileNotFoundError(item["ground_truth"])
        gt = gt_img > 127
        ignore = None
        if item.get("ignore_mask"):
            ignore_img = cv2.imread(item["ignore_mask"], cv2.IMREAD_GRAYSCALE)
            ignore = ignore_img > 127 if ignore_img is not None else None

        for system, parts in artifacts.items():
            mask_path = parts["mask_dir"] / f"{item['item_id']}__{item['prompt_id']}.png"
            pred_img = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if pred_img is None:
                raise RuntimeError(f"Incomplete {system} artifact for {key}: {mask_path}")
            pred = pred_img > 127
            metrics = per_image_metrics(pred, gt, ignore)
            people = person_detection_stats(pred, item.get("ground_truth_instances", []))
            if system == "p1":
                source = parts["source"].get(key)
                if source is None:
                    raise RuntimeError(f"Missing P1 row for {key}")
                instruction, answer = source["instruction"], source["answer"]
                latency = float(source["latency_s"])
                emitted, n_seg = bool(source["emitted_seg"]), int(source["n_seg"])
                n_boxes = grounding_query = None
            else:
                answer_row = parts["answer"].get(key)
                box_row = parts["boxes"].get(key)
                sam_row = parts["sam"].get(key)
                if answer_row is None or box_row is None or sam_row is None:
                    raise RuntimeError(f"Missing {system} stage row for {key}")
                instruction, answer = answer_row["instruction"], answer_row["answer"]
                latency = float(answer_row["latency_s"]) + float(box_row["latency_s"]) + float(sam_row["latency_s"])
                emitted = bool(box_row["boxes"])
                n_seg = n_boxes = len(box_row["boxes"])
                grounding_query = box_row["query"]

            rows_by_system[system].append({
                "dataset": "mots_surveillance_person60",
                "system": system,
                "item_id": item["item_id"],
                "prompt_id": item["prompt_id"],
                "expression": item.get("expression", "all visible people"),
                "case_type": "surveillance_all_people",
                "difficulty": item.get("difficulty", ""),
                "target_count": int(item.get("target_count", people["gt_people"])),
                "people_in_image": int(item.get("people_in_image", people["gt_people"])),
                "smallest_person_height_px": item.get("smallest_person_height_px"),
                "image": Path(item["image"]).name,
                "image_rel": relative_or_name(item["image"], args.out_dir),
                "ground_truth_rel": relative_or_name(item["ground_truth"], args.out_dir),
                "mask_rel": mask_path.relative_to(args.out_dir).as_posix(),
                "instruction": instruction,
                "answer": answer,
                "grounding_query": grounding_query,
                "emitted_seg": emitted,
                "n_seg": n_seg,
                "n_boxes": n_boxes,
                "latency_s": latency,
                "instance_coverage_50": people["person_recall_50"],
                "false_positive_pixels": int(metrics["pred_area"] - metrics["intersection"]),
                "false_positive_pixel_rate": (
                    (metrics["pred_area"] - metrics["intersection"]) / metrics["pred_area"]
                    if metrics["pred_area"] else 0.0
                ),
                **people,
                **metrics,
            })

    for system, rows in rows_by_system.items():
        with (args.out_dir / f"{system}_per_image.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    systems = {}
    for system, rows in rows_by_system.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[row["difficulty"]].append(row)
        systems[system] = {
            "overall": enhanced_surveillance_aggregate(rows),
            "by_difficulty": {
                name: enhanced_surveillance_aggregate(values)
                for name, values in sorted(groups.items())
            },
        }

    def paired(left: str, right: str) -> dict[str, Any]:
        left_rows, right_rows = rows_by_system[left], rows_by_system[right]
        deltas = np.asarray([r["iou"] - l["iou"] for l, r in zip(left_rows, right_rows)])
        return {
            f"{left}_better": int((deltas < -1e-12).sum()),
            f"{right}_better": int((deltas > 1e-12).sum()),
            "ties": int((np.abs(deltas) <= 1e-12).sum()),
            f"mean_iou_delta_{right}_minus_{left}": float(deltas.mean()),
        }

    configs = {}
    for name, path in {
        "p1": args.out_dir / "p1_config.json",
        "blip2": args.out_dir / "blip2_config.json",
        "grounding": args.out_dir / "grounding_config.json",
        "sam": args.out_dir / "sam_config.json",
        "direct_grounding": direct_dir / "grounding_config.json",
        "direct_sam": direct_dir / "sam_config.json",
    }.items():
        configs[name] = read_json(path) if path.exists() else None

    summary = {
        "dataset": "mots_surveillance_person60",
        "dataset_label": "MOTS surveillance person detection (60 frames)",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.node(),
        "selection": manifest.get("selection"),
        "detection_rule": "A labelled person is detected when >=50% of its visible ground-truth pixels are covered by the predicted union mask.",
        "n_items": len(manifest["items"][: args.max_items or None]),
        "systems": systems,
        "paired": {
            "p1_vs_p2": paired("p1", "p2"),
            "p2_vs_p2_direct": paired("p2", "p2_direct"),
        },
        "resources": configs,
    }
    write_json(args.out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2))


def phase_score(args: argparse.Namespace) -> None:
    manifest = read_json(args.out_dir / "manifest.json")
    p1_by_key = keyed(read_jsonl(args.out_dir / "p1_rows.jsonl"))
    answers = keyed(read_jsonl(args.out_dir / "blip2_answers.jsonl"))
    boxes = keyed(read_jsonl(args.out_dir / "grounding_boxes.jsonl"))
    sam = keyed(read_jsonl(args.out_dir / "sam_timings.jsonl"))
    rows_by_system: dict[str, list[dict[str, Any]]] = {"p1": [], "p2": []}

    for item in manifest["items"]:
        key = item["key"]
        if key not in p1_by_key or key not in answers or key not in boxes or key not in sam:
            raise RuntimeError(f"Incomplete artifacts for {key}")
        gt_img = cv2.imread(item["ground_truth"], cv2.IMREAD_GRAYSCALE)
        if gt_img is None:
            raise FileNotFoundError(item["ground_truth"])
        gt = gt_img > 127
        ignore = None
        if item.get("ignore_mask"):
            ignore_img = cv2.imread(item["ignore_mask"], cv2.IMREAD_GRAYSCALE)
            ignore = ignore_img > 127 if ignore_img is not None else None

        p1 = p1_by_key[key]
        p2_answer, p2_boxes, p2_sam = answers[key], boxes[key], sam[key]
        predictions = {
            "p1": (p1, args.out_dir / "p1_masks" / f"{item['item_id']}__{item['prompt_id']}.png"),
            "p2": (p2_sam, args.out_dir / "masks" / f"{item['item_id']}__{item['prompt_id']}.png"),
        }
        for system, (source, mask_path) in predictions.items():
            pred_img = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if pred_img is None:
                raise FileNotFoundError(mask_path)
            pred = pred_img > 127
            metrics = per_image_metrics(pred, gt, ignore)
            coverage, valid_instances = instance_coverage(
                pred, item.get("ground_truth_instances", [])
            )
            if system == "p1":
                answer = p1["answer"]
                instruction = p1["instruction"]
                latency = float(p1["latency_s"])
                emitted = bool(p1["emitted_seg"])
                n_seg = int(p1["n_seg"])
                n_boxes = None
                grounding_query = None
            else:
                answer = p2_answer["answer"]
                instruction = p2_answer["instruction"]
                latency = (
                    float(p2_answer["latency_s"])
                    + float(p2_boxes["latency_s"])
                    + float(p2_sam["latency_s"])
                )
                emitted = bool(p2_boxes["boxes"])
                n_seg = len(p2_boxes["boxes"])
                n_boxes = len(p2_boxes["boxes"])
                grounding_query = p2_boxes["query"]
            row = {
                "dataset": manifest["dataset"],
                "system": system,
                "item_id": item["item_id"],
                "prompt_id": item["prompt_id"],
                "expression": item.get("expression", ""),
                "case_type": item.get("case_type", "all_people"),
                "difficulty": item.get("difficulty", ""),
                "target_count": int(item.get("target_count", valid_instances)),
                "people_in_image": int(item.get("people_in_image", valid_instances)),
                "smallest_person_height_px": item.get("smallest_person_height_px"),
                "image": Path(item["image"]).name,
                "image_rel": relative_or_name(item["image"], args.out_dir),
                "ground_truth_rel": relative_or_name(item["ground_truth"], args.out_dir),
                "mask_rel": mask_path.relative_to(args.out_dir).as_posix(),
                "instruction": instruction,
                "answer": answer,
                "grounding_query": grounding_query,
                "emitted_seg": emitted,
                "n_seg": n_seg,
                "n_boxes": n_boxes,
                "latency_s": latency,
                "instance_coverage_50": coverage,
                "no_target_correct": bool(not gt.any() and not pred.any()) if not gt.any() else None,
                **metrics,
            }
            rows_by_system[system].append(row)

    def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    for system, rows in rows_by_system.items():
        write_csv(args.out_dir / f"{system}_per_image.csv", rows)

    def grouped(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(field) or "unspecified")].append(row)
        return {name: enhanced_aggregate(values) for name, values in sorted(groups.items())}

    def enhanced_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        stats = aggregate(rows)
        coverages = [r["instance_coverage_50"] for r in rows if r["instance_coverage_50"] is not None]
        no_targets = [r for r in rows if r["no_target_correct"] is not None]
        stats.update(
            mean_instance_coverage_50=(sum(coverages) / len(coverages) if coverages else None),
            no_target_accuracy=(
                sum(bool(r["no_target_correct"]) for r in no_targets) / len(no_targets)
                if no_targets
                else None
            ),
        )
        return stats

    system_summaries = {}
    for system, rows in rows_by_system.items():
        system_summaries[system] = {
            "overall": enhanced_aggregate(rows),
            "by_case_type": grouped(rows, "case_type"),
            "by_difficulty": grouped(rows, "difficulty"),
        }

    p1_map = {r["item_id"] + "::" + r["prompt_id"]: r for r in rows_by_system["p1"]}
    p2_map = {r["item_id"] + "::" + r["prompt_id"]: r for r in rows_by_system["p2"]}
    deltas = np.asarray([p2_map[key]["iou"] - row["iou"] for key, row in p1_map.items()])
    p2_better = int((deltas > 1e-12).sum())
    p1_better = int((deltas < -1e-12).sum())

    configs = {}
    for name in ("p1", "blip2", "grounding", "sam"):
        path = args.out_dir / f"{name}_config.json"
        configs[name] = read_json(path) if path.exists() else None
    p2_peaks = [
        config.get("peak_vram_gb")
        for name, config in configs.items()
        if name != "p1" and config and config.get("peak_vram_gb") is not None
    ]
    summary = {
        "dataset": manifest["dataset"],
        "dataset_label": manifest.get("dataset_label", manifest["dataset"]),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.node(),
        "selection": manifest.get("selection"),
        "n_items": len(manifest["items"]),
        "systems": system_summaries,
        "paired": {
            "p1_better": p1_better,
            "p2_better": p2_better,
            "ties": int(len(deltas) - p1_better - p2_better),
            "mean_iou_delta_p2_minus_p1": float(deltas.mean()),
            "median_iou_delta_p2_minus_p1": float(np.median(deltas)),
        },
        "resources": {
            "p1_peak_vram_gb": configs.get("p1", {}).get("peak_vram_gb") if configs.get("p1") else None,
            "p2_largest_stage_peak_vram_gb": max(p2_peaks) if p2_peaks else None,
        },
        "components": configs,
    }
    write_json(args.out_dir / "summary.json", summary)
    print(json.dumps({"dataset": summary["dataset"], "systems": summary["systems"], "paired": summary["paired"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=[
        "lisa", "blip2", "grounding", "sam", "score",
        "direct_prepare", "direct_grounding", "direct_sam", "surveillance_score",
    ])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--clip-path", type=Path, default=DEFAULT_CLIP)
    parser.add_argument("--quantization", default="4bit", choices=["none", "8bit", "4bit"])
    parser.add_argument("--sam-encoder-device", default="cpu", choices=["cuda", "cpu"])
    parser.add_argument("--sam-cpu-dtype", default="fp32", choices=["fp32", "bf16"])
    parser.add_argument("--precision", default="fp16", choices=["fp32", "fp16", "bf16"])
    parser.add_argument("--quantize-seg-projection", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--save-vis", type=int, default=12)
    parser.add_argument("--blip2-model", default=DEFAULT_BLIP2)
    parser.add_argument("--grounding-model", default=DEFAULT_GROUNDING)
    parser.add_argument("--sam-model", default=DEFAULT_SAM)
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.phase == "lisa":
        phase_lisa(args)
    elif args.phase == "blip2":
        phase_blip2(args.out_dir, args.blip2_model, args.max_items)
    elif args.phase == "grounding":
        phase_grounding(args.out_dir, args.grounding_model, args.box_threshold, args.text_threshold, args.max_items)
    elif args.phase == "sam":
        phase_sam(args.out_dir, args.sam_model, args.max_items)
    elif args.phase == "score":
        phase_score(args)
    elif args.phase == "direct_prepare":
        phase_direct_prepare(args)
    elif args.phase == "direct_grounding":
        phase_direct_prepare(args)
        phase_grounding(args.out_dir / "p2_direct", args.grounding_model, args.box_threshold, args.text_threshold, args.max_items)
    elif args.phase == "direct_sam":
        phase_direct_prepare(args)
        phase_sam(args.out_dir / "p2_direct", args.sam_model, args.max_items)
    else:
        phase_surveillance_score(args)


if __name__ == "__main__":
    main()
