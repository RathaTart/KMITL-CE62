"""Benchmark a BLIP-2/Q-Former -> Grounding DINO -> SAM pipeline against LISA.

This is intentionally a staged runner.  The three models do not comfortably fit
together on the 8 GB cenara70hx GPU, so each stage is a separate process and
writes resumable JSONL artifacts:

    prepare   exact item/prompt manifest copied from the existing LISA run
    blip2     VQA answers used as target phrases
    grounding text-conditioned boxes from those answers
    sam       masks generated from the boxes
    score     per-image CSV, summary JSON, and a LISA comparison

The output schema follows run_eval.py closely so the results can later be added
to the local website without translating the core metrics.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import os
import platform
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
CODE_ROOT = HERE.parent
PROJECT_ROOT = CODE_ROOT.parent
sys.path.insert(0, str(HERE))

from metrics import aggregate, per_image_metrics  # noqa: E402

CAMO_ROOT = (
    PROJECT_ROOT
    / "dataset"
    / "Military Personnel Dataset dataset"
    / "CamouflageData"
)
LISA_RESULTS = CODE_ROOT / "results" / "camouflage"

LISA_PROMPTS = {
    "p1_referring": "Please segment the person in this image.",
    "p2_explicit": "Please segment the camouflaged soldier hiding in this image.",
    "p3_reasoning": (
        "Who is hiding in this scene by wearing clothing that blends into the "
        "background? Please output segmentation mask."
    ),
}

# BLIP-2 is a text-output model, not a segmentation model.  These prompts ask it
# for the short target phrase that the grounding model needs while preserving
# the semantic progression of the three LISA prompts.
BLIP2_PROMPTS = {
    "p1_referring": (
        "Question: What person is shown in this image? "
        "Answer with only a short noun phrase. Answer:"
    ),
    "p2_explicit": (
        "Question: What camouflaged person is hiding in this image? "
        "Answer with only a short noun phrase. Answer:"
    ),
    "p3_reasoning": (
        "Question: Who is hiding in this scene by wearing clothing that blends "
        "into the background? Answer with only a short noun phrase. Answer:"
    ),
}

DEFAULT_BLIP2 = "Salesforce/blip2-flan-t5-xl"
DEFAULT_GROUNDING = "IDEA-Research/grounding-dino-tiny"
DEFAULT_SAM = "facebook/sam-vit-huge"


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def keyed(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["key"]): row for row in rows}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(value, fh, ensure_ascii=False, indent=2)


def gpu_info() -> dict[str, Any]:
    import torch

    if not torch.cuda.is_available():
        return {"gpu": None, "vram_gb": 0.0}
    props = torch.cuda.get_device_properties(0)
    return {
        "gpu": props.name,
        "vram_gb": round(props.total_memory / 1024**3, 3),
        "cuda": torch.version.cuda,
        "torch": torch.__version__,
    }


def clear_cuda() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass
    gc.collect()


def image_path(item_id: str) -> Path:
    return CAMO_ROOT / "img" / f"{item_id}.jpg"


def gt_path(item_id: str) -> Path:
    return CAMO_ROOT / "gt" / f"{item_id}.png"


def load_rgb(path: Path) -> np.ndarray:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def normalise_grounding_query(answer: str) -> str:
    """Keep BLIP-2's semantics while removing formatting-only noise."""
    text = answer.strip().lower()
    text = re.sub(r"^(answer|assistant)\s*:\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" \t\r\n.,;:!?\"'")
    if not text:
        return ""
    # A negative VQA answer is a rejection, not a text prompt for a detector.
    # Grounding models do not model logical negation reliably: the phrase
    # "no person" can still activate the token "person" and create boxes.
    negative_patterns = (
        r"\bno person\b",
        r"\bno one\b",
        r"\bnobody\b",
        r"\bnone\b",
        r"\bnot (?:a |any )?person\b",
        r"\bthere (?:is|are) no\b",
    )
    if any(re.search(pattern, text) for pattern in negative_patterns):
        return ""
    return text + "."


def phase_prepare(out_dir: Path, limit: int) -> None:
    baseline_csv = LISA_RESULTS / "per_image.csv"
    if not baseline_csv.exists():
        raise FileNotFoundError(f"LISA baseline not found: {baseline_csv}")

    with baseline_csv.open(encoding="utf-8") as fh:
        lisa_rows = list(csv.DictReader(fh))
    item_ids = sorted({row["item_id"] for row in lisa_rows})
    if limit:
        item_ids = item_ids[:limit]

    missing = [
        item_id
        for item_id in item_ids
        if not image_path(item_id).exists() or not gt_path(item_id).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing image/GT for: {missing[:5]}")

    items = []
    for item_id in item_ids:
        for prompt_id in LISA_PROMPTS:
            items.append(
                {
                    "key": f"{item_id}::{prompt_id}",
                    "item_id": item_id,
                    "prompt_id": prompt_id,
                    "image": str(image_path(item_id)),
                    "ground_truth": str(gt_path(item_id)),
                    "lisa_instruction": LISA_PROMPTS[prompt_id],
                    "blip2_instruction": BLIP2_PROMPTS[prompt_id],
                }
            )

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selection": "exact unique item_ids from code/results/camouflage/per_image.csv",
        "n_unique_images": len(item_ids),
        "n_inferences": len(items),
        "prompt_ids": list(LISA_PROMPTS),
        "items": items,
    }
    write_json(out_dir / "manifest.json", manifest)
    print(
        f"Prepared {len(item_ids)} unique images x {len(LISA_PROMPTS)} prompts "
        f"= {len(items)} inferences"
    )


def load_manifest(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"Run --phase prepare first: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def phase_blip2(out_dir: Path, model_id: str, max_items: int) -> None:
    import torch
    from PIL import Image
    from transformers import AutoProcessor, BitsAndBytesConfig, Blip2ForConditionalGeneration

    manifest = load_manifest(out_dir)
    items = manifest["items"][: max_items or None]
    output_path = out_dir / "blip2_answers.jsonl"
    done = keyed(read_jsonl(output_path))

    quant = BitsAndBytesConfig(load_in_8bit=True)
    processor = AutoProcessor.from_pretrained(model_id)
    model = Blip2ForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quant,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    model.eval()
    clear_cuda()

    for idx, item in enumerate(items, 1):
        if item["key"] in done:
            continue
        image = Image.open(item["image"]).convert("RGB")
        inputs = processor(
            images=image,
            text=item["blip2_instruction"],
            return_tensors="pt",
        )
        for name, value in list(inputs.items()):
            if not hasattr(value, "to"):
                continue
            if value.is_floating_point():
                inputs[name] = value.to("cuda", dtype=torch.float16)
            else:
                inputs[name] = value.to("cuda")

        torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=16,
                do_sample=False,
                num_beams=1,
            )
        torch.cuda.synchronize()
        latency = time.perf_counter() - started
        answer = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        row = {
            "key": item["key"],
            "item_id": item["item_id"],
            "prompt_id": item["prompt_id"],
            "instruction": item["blip2_instruction"],
            "answer": answer,
            "grounding_query": normalise_grounding_query(answer),
            "latency_s": latency,
        }
        append_jsonl(output_path, row)
        done[item["key"]] = row
        print(
            f"BLIP2 {idx}/{len(items)} {item['key']} -> "
            f"{answer!r} ({latency:.2f}s)",
            flush=True,
        )

    write_json(
        out_dir / "blip2_config.json",
        {
            "model": model_id,
            "quantization": "8bit",
            "max_new_tokens": 16,
            "do_sample": False,
            "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
            "gpu": gpu_info(),
        },
    )


def phase_grounding(
    out_dir: Path,
    model_id: str,
    box_threshold: float,
    text_threshold: float,
    max_items: int,
) -> None:
    import torch
    from PIL import Image
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    manifest = load_manifest(out_dir)
    items = manifest["items"][: max_items or None]
    answers = keyed(read_jsonl(out_dir / "blip2_answers.jsonl"))
    output_path = out_dir / "grounding_boxes.jsonl"
    done = keyed(read_jsonl(output_path))

    processor = AutoProcessor.from_pretrained(model_id)
    # The HF Grounding DINO text enhancer produces fp32 features.  Loading the
    # detector in fp16 makes its Linear layers reject those features
    # (Float/Half dtype mismatch) in transformers 4.49.  The tiny checkpoint
    # comfortably fits cenara70hx in fp32, so keep this stage consistently fp32.
    model = AutoModelForZeroShotObjectDetection.from_pretrained(
        model_id, torch_dtype=torch.float32, low_cpu_mem_usage=True
    ).to("cuda")
    model.eval()
    clear_cuda()

    for idx, item in enumerate(items, 1):
        if item["key"] in done:
            continue
        answer = answers.get(item["key"])
        if answer is None:
            raise RuntimeError(f"Missing BLIP-2 answer for {item['key']}")
        # Recompute from the immutable raw answer so query-normalisation fixes
        # can be applied without rerunning the expensive BLIP-2 stage.
        query = normalise_grounding_query(answer["answer"])
        image = Image.open(item["image"]).convert("RGB")

        if not query:
            row = {
                "key": item["key"],
                "item_id": item["item_id"],
                "prompt_id": item["prompt_id"],
                "query": query,
                "boxes": [],
                "scores": [],
                "labels": [],
                "latency_s": 0.0,
            }
        else:
            inputs = processor(images=image, text=query, return_tensors="pt")
            for name, value in list(inputs.items()):
                if not hasattr(value, "to"):
                    continue
                if value.is_floating_point():
                    inputs[name] = value.to("cuda", dtype=torch.float32)
                else:
                    inputs[name] = value.to("cuda")

            torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                outputs = model(**inputs)
            result = processor.post_process_grounded_object_detection(
                outputs,
                inputs["input_ids"],
                box_threshold=box_threshold,
                text_threshold=text_threshold,
                target_sizes=[image.size[::-1]],
            )[0]
            torch.cuda.synchronize()
            latency = time.perf_counter() - started
            row = {
                "key": item["key"],
                "item_id": item["item_id"],
                "prompt_id": item["prompt_id"],
                "query": query,
                "boxes": result["boxes"].detach().cpu().tolist(),
                "scores": result["scores"].detach().float().cpu().tolist(),
                "labels": [str(label) for label in result["labels"]],
                "latency_s": latency,
            }

        append_jsonl(output_path, row)
        done[item["key"]] = row
        print(
            f"DINO {idx}/{len(items)} {item['key']} query={query!r} "
            f"boxes={len(row['boxes'])}",
            flush=True,
        )

    write_json(
        out_dir / "grounding_config.json",
        {
            "model": model_id,
            "box_threshold": box_threshold,
            "text_threshold": text_threshold,
            "precision": "fp32",
            "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
            "gpu": gpu_info(),
        },
    )


def phase_sam(out_dir: Path, model_id: str, max_items: int) -> None:
    import torch
    from PIL import Image
    from transformers import SamModel, SamProcessor

    manifest = load_manifest(out_dir)
    items = manifest["items"][: max_items or None]
    boxes_by_key = keyed(read_jsonl(out_dir / "grounding_boxes.jsonl"))
    timing_path = out_dir / "sam_timings.jsonl"
    done = keyed(read_jsonl(timing_path))
    masks_dir = out_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)

    processor = SamProcessor.from_pretrained(model_id)
    model = SamModel.from_pretrained(
        model_id, torch_dtype=torch.float16, low_cpu_mem_usage=True
    ).to("cuda")
    model.eval()
    clear_cuda()

    for idx, item in enumerate(items, 1):
        mask_path = masks_dir / f"{item['item_id']}__{item['prompt_id']}.png"
        if item["key"] in done and mask_path.exists():
            continue
        box_row = boxes_by_key.get(item["key"])
        if box_row is None:
            raise RuntimeError(f"Missing grounding boxes for {item['key']}")

        image = Image.open(item["image"]).convert("RGB")
        width, height = image.size
        boxes = box_row["boxes"]
        if not boxes:
            mask = np.zeros((height, width), dtype=np.uint8)
            latency = 0.0
            iou_scores: list[float] = []
        else:
            inputs = processor(images=image, input_boxes=[boxes], return_tensors="pt")
            for name, value in list(inputs.items()):
                if not hasattr(value, "to"):
                    continue
                if value.is_floating_point():
                    inputs[name] = value.to("cuda", dtype=torch.float16)
                else:
                    inputs[name] = value.to("cuda")

            torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                outputs = model(**inputs, multimask_output=False)
            torch.cuda.synchronize()
            latency = time.perf_counter() - started
            post = processor.image_processor.post_process_masks(
                outputs.pred_masks.detach().cpu(),
                inputs["original_sizes"].detach().cpu(),
                inputs["reshaped_input_sizes"].detach().cpu(),
            )[0]
            # [n_boxes, 1, H, W].  A prompt can locate multiple people; union
            # their masks so evaluation matches the binary person GT.
            mask = (post[:, 0] > 0).any(dim=0).numpy().astype(np.uint8) * 255
            iou_scores = outputs.iou_scores.detach().float().cpu().reshape(-1).tolist()

        if not cv2.imwrite(str(mask_path), mask):
            raise RuntimeError(f"Could not write {mask_path}")
        row = {
            "key": item["key"],
            "item_id": item["item_id"],
            "prompt_id": item["prompt_id"],
            "n_boxes": len(boxes),
            "sam_iou_scores": iou_scores,
            "latency_s": latency,
            "mask": str(mask_path),
        }
        append_jsonl(timing_path, row)
        done[item["key"]] = row
        print(
            f"SAM {idx}/{len(items)} {item['key']} boxes={len(boxes)} "
            f"mask_px={int((mask > 0).sum())}",
            flush=True,
        )

    write_json(
        out_dir / "sam_config.json",
        {
            "model": model_id,
            "precision": "fp16",
            "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
            "gpu": gpu_info(),
        },
    )


def lisa_rows_by_key() -> dict[str, dict[str, Any]]:
    with (LISA_RESULTS / "per_image.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {f"{row['item_id']}::{row['prompt_id']}": row for row in rows}


def phase_score(out_dir: Path) -> None:
    manifest = load_manifest(out_dir)
    answers = keyed(read_jsonl(out_dir / "blip2_answers.jsonl"))
    boxes = keyed(read_jsonl(out_dir / "grounding_boxes.jsonl"))
    sam_times = keyed(read_jsonl(out_dir / "sam_timings.jsonl"))
    lisa_rows = lisa_rows_by_key()

    scored: list[dict[str, Any]] = []
    for item in manifest["items"]:
        key = item["key"]
        answer = answers.get(key)
        box_row = boxes.get(key)
        sam_row = sam_times.get(key)
        if not answer or not box_row or not sam_row:
            raise RuntimeError(f"Incomplete staged artifacts for {key}")

        pred = cv2.imread(sam_row["mask"], cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(item["ground_truth"], cv2.IMREAD_GRAYSCALE)
        if pred is None or gt is None:
            raise FileNotFoundError(f"Could not read mask/GT for {key}")
        metrics = per_image_metrics(pred > 127, gt > 127)
        lisa = lisa_rows.get(key)
        lisa_iou = float(lisa["iou"]) if lisa else None
        total_latency = (
            float(answer["latency_s"])
            + float(box_row["latency_s"])
            + float(sam_row["latency_s"])
        )
        row = {
            "item_id": item["item_id"],
            "prompt_id": item["prompt_id"],
            "image": os.path.basename(item["image"]),
            "instruction": item["blip2_instruction"],
            "lisa_instruction": item["lisa_instruction"],
            "answer": answer["answer"],
            "grounding_query": box_row["query"],
            "grounding_labels": " | ".join(box_row["labels"]),
            "n_boxes": len(box_row["boxes"]),
            "emitted_seg": bool(box_row["boxes"]),
            "n_seg": len(box_row["boxes"]),
            "blip2_latency_s": float(answer["latency_s"]),
            "grounding_latency_s": float(box_row["latency_s"]),
            "sam_latency_s": float(sam_row["latency_s"]),
            "latency_s": total_latency,
            "lisa_iou": lisa_iou,
            "iou_delta_vs_lisa": metrics["iou"] - lisa_iou if lisa_iou is not None else None,
            **metrics,
        }
        scored.append(row)

    fields = list(scored[0]) if scored else []
    with (out_dir / "per_image.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(scored)

    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        by_prompt[row["prompt_id"]].append(row)

    # Aggregate only the LISA rows represented in this manifest.  This matters
    # for smoke tests and ensures future reduced samples are always paired.
    lisa_matched: list[dict[str, Any]] = []
    lisa_by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in manifest["items"]:
        source = lisa_rows.get(item["key"])
        if source is None:
            raise RuntimeError(f"Missing matched LISA row for {item['key']}")
        row = {
            "intersection": int(source["intersection"]),
            "union": int(source["union"]),
            "pred_area": int(source["pred_area"]),
            "gt_area": int(source["gt_area"]),
            "iou": float(source["iou"]),
            "dice": float(source["dice"]),
            "precision": float(source["precision"]),
            "recall": float(source["recall"]),
            "latency_s": float(source["latency_s"]),
            "emitted_seg": str(source["emitted_seg"]).lower() in ("true", "1"),
        }
        lisa_matched.append(row)
        lisa_by_prompt[item["prompt_id"]].append(row)

    lisa_overall = aggregate(lisa_matched)
    lisa_prompt_stats = {
        prompt_id: aggregate(rows) for prompt_id, rows in lisa_by_prompt.items()
    }
    pipeline_overall = aggregate(scored)
    pipeline_by_prompt = {pid: aggregate(rows) for pid, rows in by_prompt.items()}

    def paired_details(
        pipeline_rows: list[dict[str, Any]],
        pipeline_stats: dict[str, Any],
        baseline_stats: dict[str, Any],
        seed: int,
    ) -> dict[str, Any]:
        deltas = np.asarray(
            [float(row["iou_delta_vs_lisa"]) for row in pipeline_rows], dtype=float
        )
        rng = np.random.default_rng(seed)
        bootstrap_means = np.asarray(
            [rng.choice(deltas, size=len(deltas), replace=True).mean() for _ in range(10000)]
        )
        tolerance = 1e-12
        return {
            "n": int(len(deltas)),
            "pipeline_better": int((deltas > tolerance).sum()),
            "lisa_better": int((deltas < -tolerance).sum()),
            "ties": int((np.abs(deltas) <= tolerance).sum()),
            "mean_iou_delta": float(deltas.mean()),
            "median_iou_delta": float(np.median(deltas)),
            "mean_iou_delta_bootstrap_95ci": [
                float(np.quantile(bootstrap_means, 0.025)),
                float(np.quantile(bootstrap_means, 0.975)),
            ],
            "gIoU_delta": pipeline_stats["gIoU"] - baseline_stats["gIoU"],
            "cIoU_delta": pipeline_stats["cIoU"] - baseline_stats["cIoU"],
            "dice_delta": pipeline_stats["mean_dice"] - baseline_stats["mean_dice"],
            "latency_delta_s": pipeline_stats["mean_latency_s"]
            - baseline_stats["mean_latency_s"],
            "compute_speedup_vs_lisa": (
                baseline_stats["mean_latency_s"] / pipeline_stats["mean_latency_s"]
                if pipeline_stats["mean_latency_s"]
                else None
            ),
        }

    paired = {
        "overall": paired_details(scored, pipeline_overall, lisa_overall, 0),
        "by_prompt": {
            prompt_id: paired_details(
                by_prompt[prompt_id],
                pipeline_by_prompt[prompt_id],
                lisa_prompt_stats[prompt_id],
                index + 1,
            )
            for index, prompt_id in enumerate(sorted(by_prompt))
        },
    }
    comparison = {
        "overall": {
            "blip2_pipeline_gIoU": pipeline_overall.get("gIoU"),
            "lisa_gIoU": lisa_overall["gIoU"],
            "delta_gIoU": pipeline_overall.get("gIoU", 0) - lisa_overall["gIoU"],
            "blip2_pipeline_wins": pipeline_overall.get("gIoU", 0)
            > lisa_overall["gIoU"],
        },
        "by_prompt": {},
    }
    for pid, stats in pipeline_by_prompt.items():
        lisa_stats = lisa_prompt_stats[pid]
        comparison["by_prompt"][pid] = {
            "blip2_pipeline_gIoU": stats["gIoU"],
            "lisa_gIoU": lisa_stats["gIoU"],
            "delta_gIoU": stats["gIoU"] - lisa_stats["gIoU"],
            "blip2_pipeline_wins": stats["gIoU"] > lisa_stats["gIoU"],
        }

    configs = {}
    for name in ("blip2", "grounding", "sam"):
        config_path = out_dir / f"{name}_config.json"
        configs[name] = (
            json.loads(config_path.read_text(encoding="utf-8"))
            if config_path.exists()
            else None
        )
    summary = {
        "task": "camouflage",
        "pipeline": "BLIP-2/Q-Former -> Grounding DINO -> SAM ViT-H",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.node(),
        "sample_source": manifest["selection"],
        "n_unique_images": manifest["n_unique_images"],
        "overall": pipeline_overall,
        "by_prompt": pipeline_by_prompt,
        "lisa_matched": {"overall": lisa_overall, "by_prompt": lisa_prompt_stats},
        "comparison_to_lisa": comparison,
        "paired_analysis": paired,
        "pipeline_diagnostics": {
            "answer_counts": dict(Counter(row["answer"].strip().lower() for row in scored)),
            "zero_box_rate": sum(row["n_boxes"] == 0 for row in scored) / len(scored),
            "mean_boxes": sum(row["n_boxes"] for row in scored) / len(scored),
            "mean_blip2_latency_s": sum(row["blip2_latency_s"] for row in scored)
            / len(scored),
            "mean_grounding_latency_s": sum(
                row["grounding_latency_s"] for row in scored
            )
            / len(scored),
            "mean_sam_latency_s": sum(row["sam_latency_s"] for row in scored)
            / len(scored),
            "largest_improvements": sorted(
                (
                    {
                        "item_id": row["item_id"],
                        "prompt_id": row["prompt_id"],
                        "answer": row["answer"],
                        "n_boxes": row["n_boxes"],
                        "pipeline_iou": row["iou"],
                        "lisa_iou": row["lisa_iou"],
                        "iou_delta": row["iou_delta_vs_lisa"],
                    }
                    for row in scored
                ),
                key=lambda row: row["iou_delta"],
                reverse=True,
            )[:10],
            "largest_regressions": sorted(
                (
                    {
                        "item_id": row["item_id"],
                        "prompt_id": row["prompt_id"],
                        "answer": row["answer"],
                        "n_boxes": row["n_boxes"],
                        "pipeline_iou": row["iou"],
                        "lisa_iou": row["lisa_iou"],
                        "iou_delta": row["iou_delta_vs_lisa"],
                    }
                    for row in scored
                ),
                key=lambda row: row["iou_delta"],
            )[:10],
        },
        "components": configs,
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(comparison, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        required=True,
        choices=["prepare", "blip2", "grounding", "sam", "score"],
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Smoke-test only: process at most this many item/prompt rows.",
    )
    parser.add_argument("--blip2-model", default=DEFAULT_BLIP2)
    parser.add_argument("--grounding-model", default=DEFAULT_GROUNDING)
    parser.add_argument("--sam-model", default=DEFAULT_SAM)
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        phase_prepare(args.out_dir, args.limit)
    elif args.phase == "blip2":
        phase_blip2(args.out_dir, args.blip2_model, args.max_items)
    elif args.phase == "grounding":
        phase_grounding(
            args.out_dir,
            args.grounding_model,
            args.box_threshold,
            args.text_threshold,
            args.max_items,
        )
    elif args.phase == "sam":
        phase_sam(args.out_dir, args.sam_model, args.max_items)
    elif args.phase == "score":
        phase_score(args.out_dir)


if __name__ == "__main__":
    main()
