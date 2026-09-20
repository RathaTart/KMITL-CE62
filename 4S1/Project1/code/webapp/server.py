"""Local web app for browsing the LISA results and running the model on new images.

Serves four things:
  * the measured results (tables, per-pattern ranking, correlations, fragmentation)
  * the BLIP-2 -> Grounding DINO -> SAM pipeline compared with LISA
  * a browser over all 380 scored inferences, with overlays rendered on demand
  * drag-and-drop inference on a new image

Overlays are generated per request from the masks `run_eval.py` already saved,
rather than pre-rendering thousands of JPEGs. Rendering one costs ~50 ms.

Run it:
    code\\.venv311\\Scripts\\python.exe code\\webapp\\server.py
    -> http://127.0.0.1:5000

Nothing is exposed off this machine: it binds 127.0.0.1 only. The model is loaded
lazily on the first inference request (~35 s) and then kept resident, so browsing
results never pays that cost.
"""

import csv
import base64
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid

import cv2
import numpy as np
from flask import Flask, jsonify, request, send_file, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
CODE_ROOT = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(CODE_ROOT)
sys.path.insert(0, os.path.join(CODE_ROOT, "scripts"))

RESULTS = os.path.join(CODE_ROOT, "results")
PIPELINE_RESULTS = os.path.join(RESULTS, "blip2_grounded_sam")
EXTERNAL_RESULTS = {
    "grefcoco": os.path.join(RESULTS, "grefcoco_pilot_p1_p2"),
    "mots_small_person": os.path.join(RESULTS, "mots_small_person_pilot_p1_p2"),
    "mots_surveillance_person60": os.path.join(RESULTS, "mots_small_person_p1_p2"),
}
CAMO = os.path.join(
    PROJECT_ROOT, "dataset", "Military Personnel Dataset dataset", "CamouflageData"
)
REASONSEG = os.path.join(CODE_ROOT, "data", "reason_seg", "ReasonSeg", "val")
DRONE = os.path.join(PROJECT_ROOT, "dataset", "drone")

from metrics import aggregate, per_image_metrics  # noqa: E402

app = Flask(__name__, static_folder=os.path.join(HERE, "static"), static_url_path="")

MAX_SIDE = 1400  # cap on served image width, keeps big ReasonSeg frames sane

# ---------------------------------------------------------------------------
# model, loaded once, used by one request at a time (6 GB of VRAM allows no more)
# ---------------------------------------------------------------------------
_engine = None
_engine_err = None
_engine_lock = threading.Lock()
_gpu_lock = threading.Lock()

PROMPT_PRESETS = {
    "p1_referring": "Please segment the person in this image.",
    "p2_explicit": "Please segment the camouflaged soldier hiding in this image.",
    "p3_reasoning": (
        "Who is hiding in this scene by wearing clothing that blends into the "
        "background? Please output segmentation mask."
    ),
    "car_explicit": "Please segment the vehicle that is hidden or covered in this image.",
}

P2_VQA_PRESETS = {
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
    "car_explicit": (
        "Question: What hidden or covered vehicle is visible in this image? "
        "Answer with only a short noun phrase. Answer:"
    ),
}

# P2 cannot fit beside LISA on the local 6 GB GPU. Its three stages run
# serially on the same Tailscale machine used for the recorded benchmark.
P2_REMOTE_HOST = os.environ.get("P2_REMOTE_HOST", "osta@100.69.21.71")
P2_REMOTE_KEY = os.environ.get(
    "P2_REMOTE_KEY", os.path.join(os.path.expanduser("~"), ".ssh", "lisa_cenara70hx")
)
P2_REMOTE_BASE = "/home/osta/blip2-qformer-eval/live-web-jobs"
P2_REMOTE_PYTHON = "/home/osta/blip2-qformer-eval/.venv/bin/python"
P2_REMOTE_RUNNER = "/home/osta/lisa-eval/code/scripts/run_blip2_grounded_sam.py"
P2_REMOTE_HF_HOME = "/home/osta/blip2-qformer-eval/hf-cache"


def get_engine():
    """Build the engine on first use. Serialised so two requests can't both load."""
    global _engine, _engine_err
    with _engine_lock:
        if _engine is not None or _engine_err is not None:
            return _engine
        try:
            from lisa_engine import LisaEngine

            _engine = LisaEngine(
                model_path=os.path.join(CODE_ROOT, "weights", "LISA-7B-v1"),
                clip_path=os.path.join(CODE_ROOT, "weights", "clip-vit-large-patch14"),
                quantization="4bit",
                sam_encoder_device="cpu",
            )
        except Exception as exc:  # noqa: BLE001
            _engine_err = f"{type(exc).__name__}: {exc}"
        return _engine


# ---------------------------------------------------------------------------
# jobs
# ---------------------------------------------------------------------------
_jobs = {}
_jobs_lock = threading.Lock()


def set_job(jid, **kw):
    with _jobs_lock:
        _jobs.setdefault(jid, {}).update(kw)


def get_job(jid):
    with _jobs_lock:
        j = _jobs.get(jid)
        return dict(j) if j else None


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def shrink(rgb, max_side=MAX_SIDE):
    h, w = rgb.shape[:2]
    if max(h, w) <= max_side:
        return rgb
    s = max_side / max(h, w)
    return cv2.resize(rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)


def png_response(rgb, fmt=".jpg", quality=82):
    params = [int(cv2.IMWRITE_JPEG_QUALITY), quality] if fmt == ".jpg" else []
    ok, buf = cv2.imencode(fmt, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), params)
    if not ok:
        return jsonify(error="encode failed"), 500
    mime = "image/jpeg" if fmt == ".jpg" else "image/png"
    return send_file(io.BytesIO(buf.tobytes()), mimetype=mime)


def tint(rgb, mask, colour):
    """Half-blend colour into the masked pixels (same look as the saved overlays)."""
    out = rgb.copy()
    if mask is not None and mask.any():
        out[mask] = (
            rgb * 0.5 + mask[:, :, None].astype(np.uint8) * np.array(colour) * 0.5
        )[mask]
    return out


def read_rgb(path):
    img = cv2.imread(path)
    return None if img is None else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def external_rows(task, system=None):
    root = EXTERNAL_RESULTS.get(task)
    if root is None:
        return []
    available = ("p1", "p2", "p2_direct") if task == "mots_surveillance_person60" else ("p1", "p2")
    systems = (system,) if system in available else available
    rows = []
    float_fields = (
        "iou", "dice", "precision", "recall", "latency_s",
        "instance_coverage_50", "smallest_person_height_px", "person_recall_50",
        "false_positive_pixel_rate",
    )
    int_fields = (
        "intersection", "union", "pred_area", "gt_area", "n_seg", "n_boxes",
        "target_count", "people_in_image", "gt_people", "detected_people_50",
        "missed_people_50", "false_positive_pixels",
        "tiny_le_32px_total", "tiny_le_32px_detected",
        "small_33_64px_total", "small_33_64px_detected",
        "large_gt_64px_total", "large_gt_64px_detected",
    )
    for current in systems:
        path = os.path.join(root, f"{current}_per_image.csv")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            loaded = list(csv.DictReader(fh))
        for row in loaded:
            row["system"] = current
            for field in float_fields:
                try:
                    row[field] = float(row[field]) if row.get(field) not in (None, "") else None
                except ValueError:
                    row[field] = None
            for field in int_fields:
                try:
                    row[field] = int(float(row[field])) if row.get(field) not in (None, "") else None
                except ValueError:
                    row[field] = None
            row["emitted_seg"] = str(row.get("emitted_seg", "")).lower() in ("true", "1")
        rows.extend(loaded)
    return rows


def external_row(task, item, prompt, system="p1"):
    return next(
        (
            row for row in external_rows(task, system)
            if row["item_id"] == item and row["prompt_id"] == prompt
        ),
        None,
    )


def source_image(task, item):
    if task == "camouflage":
        return read_rgb(os.path.join(CAMO, "img", item + ".jpg"))
    if task == "reasonseg":
        return read_rgb(os.path.join(REASONSEG, item + ".jpg"))
    if task == "drone":
        return read_rgb(os.path.join(DRONE, item + ".png"))
    if task in EXTERNAL_RESULTS:
        row = next((r for r in external_rows(task, "p1") if r["item_id"] == item), None)
        if row:
            return read_rgb(os.path.join(EXTERNAL_RESULTS[task], row["image_rel"]))
    return None


def ground_truth(task, item, shape):
    """Target mask, or None when the task ships no labels."""
    if task == "camouflage":
        g = cv2.imread(os.path.join(CAMO, "gt", item + ".png"), cv2.IMREAD_GRAYSCALE)
        return None if g is None else (g > 127)
    if task == "reasonseg":
        sys.path.insert(0, os.path.join(CODE_ROOT, "LISA"))
        from utils.data_processing import get_mask_from_json

        jp = os.path.join(REASONSEG, item + ".json")
        if not os.path.exists(jp):
            return None
        m, _, _ = get_mask_from_json(jp, np.zeros(shape + (3,), dtype=np.uint8))
        return m == 1
    if task in EXTERNAL_RESULTS:
        row = next((r for r in external_rows(task, "p1") if r["item_id"] == item), None)
        if row:
            mask = cv2.imread(
                os.path.join(EXTERNAL_RESULTS[task], row["ground_truth_rel"]),
                cv2.IMREAD_GRAYSCALE,
            )
            return None if mask is None else (mask > 127)
    return None


def prediction(task, item, prompt):
    p = os.path.join(RESULTS, task, "masks", f"{item}__{prompt}.png")
    if not os.path.exists(p):
        return None
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    return None if m is None else (m > 127)


def pipeline_prediction(item, prompt):
    p = os.path.join(PIPELINE_RESULTS, "masks", f"{item}__{prompt}.png")
    if not os.path.exists(p):
        return None
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    return None if m is None else (m > 127)


def external_prediction(task, item, prompt, system):
    row = external_row(task, item, prompt, system)
    if row is None:
        return None
    path = os.path.join(EXTERNAL_RESULTS[task], row["mask_rel"])
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return None if mask is None else (mask > 127)


def read_jsonl_by_key(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["key"]] = row
    return rows


def load_pipeline_rows():
    """Join the saved pipeline stages into website-ready, read-only records."""
    p = os.path.join(PIPELINE_RESULTS, "per_image.csv")
    if not os.path.exists(p):
        return []
    boxes = read_jsonl_by_key(os.path.join(PIPELINE_RESULTS, "grounding_boxes.jsonl"))
    lisa = {
        f'{r["item_id"]}::{r["prompt_id"]}': r
        for r in load_rows("camouflage")
    }
    with open(p, encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    float_fields = (
        "iou", "dice", "precision", "recall", "lisa_iou", "iou_delta_vs_lisa",
        "blip2_latency_s", "grounding_latency_s", "sam_latency_s", "latency_s",
    )
    int_fields = ("n_boxes", "pred_area", "gt_area")
    rows = []
    for r in raw:
        key = f'{r["item_id"]}::{r["prompt_id"]}'
        b = boxes.get(key, {})
        out = {k: r.get(k, "") for k in (
            "item_id", "prompt_id", "instruction", "lisa_instruction", "answer",
            "grounding_query", "grounding_labels",
        )}
        for field in float_fields:
            try:
                out[field] = float(r[field])
            except (KeyError, TypeError, ValueError):
                out[field] = None
        for field in int_fields:
            try:
                out[field] = int(float(r[field]))
            except (KeyError, TypeError, ValueError):
                out[field] = None
        out["boxes"] = b.get("boxes", [])
        out["box_scores"] = b.get("scores", [])
        out["box_labels"] = b.get("labels", [])
        out["emitted_seg"] = str(r.get("emitted_seg", "")).lower() in ("true", "1")
        baseline = lisa.get(key, {})
        out["lisa_dice"] = baseline.get("dice")
        out["lisa_latency_s"] = baseline.get("latency_s")
        out["lisa_pred_area"] = baseline.get("pred_area")
        rows.append(out)
    return rows


PIPELINE_ROWS = None


def pipeline_rows():
    global PIPELINE_ROWS
    if PIPELINE_ROWS is None:
        PIPELINE_ROWS = load_pipeline_rows()
    return PIPELINE_ROWS


def pipeline_row(item, prompt):
    return next(
        (r for r in pipeline_rows() if r["item_id"] == item and r["prompt_id"] == prompt),
        None,
    )


# ---------------------------------------------------------------------------
# derived analyses, computed once at startup
# ---------------------------------------------------------------------------
def load_rows(task):
    p = os.path.join(RESULTS, task, "per_image.csv")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("iou", "dice", "precision", "recall", "latency_s"):
            if r.get(k):
                try:
                    r[k] = float(r[k])
                except ValueError:
                    r[k] = None
        for k in ("intersection", "union", "pred_area", "gt_area", "n_seg"):
            if r.get(k):
                try:
                    r[k] = int(float(r[k]))
                except ValueError:
                    pass
        r["emitted_seg"] = str(r.get("emitted_seg", "")).lower() in ("true", "1")
    return rows


def load_summary(task):
    p = os.path.join(RESULTS, task, "summary.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def build_analysis():
    out = {"summary": {}, "counts": {}}
    for t in ("camouflage", "reasonseg", "drone"):
        out["summary"][t] = load_summary(t)
        out["counts"][t] = len(load_rows(t))

    camo = load_rows("camouflage")
    scored = [r for r in camo if isinstance(r.get("iou"), float)]

    stats_path = os.path.join(RESULTS, "dataset_analysis.json")
    pstats = {}
    if os.path.exists(stats_path):
        pstats = json.load(open(stats_path, encoding="utf-8"))["camouflage"]["per_pattern"]

    per_pattern, by_prompt = {}, {}
    for r in scored:
        pat = r["item_id"].split("_")[0]
        per_pattern.setdefault(pat, []).append(r)
        by_prompt.setdefault(pat, {}).setdefault(r["prompt_id"], []).append(r["iou"])

    patterns = []
    for pat, rs in sorted(per_pattern.items()):
        st = pstats.get(pat, {})
        area = st.get("target_area_pct") or {}
        patterns.append(
            {
                "pattern": pat,
                "name": st.get("name", pat),
                "n": len(rs),
                "miou": 100 * sum(r["iou"] for r in rs) / len(rs),
                "contrast": st.get("camo_contrast_median"),
                "area_pct": area.get("median"),
                "bbox_px": st.get("bbox_side_px_median"),
                "prompts": {
                    k: 100 * sum(v) / len(v) for k, v in by_prompt.get(pat, {}).items()
                },
            }
        )
    patterns.sort(key=lambda p: p["miou"])
    out["patterns"] = patterns

    corr = []
    for key, label in (
        ("contrast", "camo_contrast"),
        ("area_pct", "target_area_pct"),
        ("bbox_px", "bbox_side_px"),
    ):
        pairs = [(p[key], p["miou"]) for p in patterns if p.get(key) is not None]
        if len(pairs) >= 5:
            corr.append(
                {
                    "key": label,
                    "rho": spearman([a for a, _ in pairs], [b for _, b in pairs]),
                    "n": len(pairs),
                }
            )
    out["correlations"] = corr

    # prediction fragmentation vs accuracy
    bands = [(1, 1, "1"), (2, 3, "2-3"), (4, 9, "4-9"), (10, 10**9, "10+")]
    frag = {lab: [] for _, _, lab in bands}
    empty = 0
    for r in scored:
        m = prediction("camouflage", r["item_id"], r["prompt_id"])
        if m is None:
            continue
        if not m.any():
            empty += 1
            continue
        n, _ = cv2.connectedComponents(m.astype(np.uint8), connectivity=4)
        c = n - 1
        for lo, hi, lab in bands:
            if lo <= c <= hi:
                frag[lab].append(r["iou"])
                break
    out["fragmentation"] = [
        {"band": lab, "n": len(v), "miou": 100 * sum(v) / len(v)}
        for _, _, lab in bands
        if (v := frag[lab])
    ]
    out["fragmentation_empty"] = empty

    hard, easy = patterns[:5], patterns[-5:]
    out["prompt_by_difficulty"] = {
        grp: {
            pid: sum(p["prompts"][pid] for p in sub if pid in p["prompts"])
            / max(1, len([p for p in sub if pid in p["prompts"]]))
            for pid in sorted({k for p in sub for k in p["prompts"]})
        }
        for grp, sub in (("hardest5", hard), ("easiest5", easy))
    }
    # Drone stills have no ground truth, so the only reportable number is mask
    # area as a share of frame. Frame size comes from the file header (PIL is
    # lazy about decoding), which is why this is cheap enough to do for all rows.
    # run_eval.py writes pred_area only when there is ground truth to score
    # against, so for the drone task it is absent from the CSV. Read the saved
    # mask instead - 9 small PNGs, once, at startup.
    drone = []
    for r in load_rows("drone"):
        m = prediction("drone", r["item_id"], r["prompt_id"])
        px = int(m.sum()) if m is not None else None
        drone.append(
            {
                "item_id": r["item_id"],
                "prompt_id": r["prompt_id"],
                "pred_area": px,
                "pct": (100.0 * float(m.mean())) if m is not None else None,
            }
        )
    out["drone_area"] = drone

    out["prompt_presets"] = PROMPT_PRESETS
    out["pattern_names"] = {p["pattern"]: p["name"] for p in patterns}
    out["summary"]["blip2_grounded_sam"] = load_summary("blip2_grounded_sam")
    out["counts"]["blip2_grounded_sam"] = len(pipeline_rows())
    out["external"] = {}
    for task, root in EXTERNAL_RESULTS.items():
        summary_path = os.path.join(root, "summary.json")
        summary = json.load(open(summary_path, encoding="utf-8")) if os.path.exists(summary_path) else None
        out["external"][task] = summary
        out["counts"][task] = len(external_rows(task, "p1"))
    return out


ANALYSIS = None


def analysis():
    global ANALYSIS
    if ANALYSIS is None:
        ANALYSIS = build_analysis()
    return ANALYSIS


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/analysis")
def api_analysis():
    return jsonify(analysis())


@app.get("/api/items")
def api_items():
    task = request.args.get("task", "camouflage")
    system = request.args.get("system", "both")
    if system not in ("both", "all3", "p1", "p2", "p2_direct"):
        return jsonify(error="system must be both, all3, p1, p2, or p2_direct"), 400

    rows = []
    if task in EXTERNAL_RESULTS:
        if system in ("both", "all3", "p1"):
            rows.extend(external_rows(task, "p1"))
        if system in ("both", "all3", "p2"):
            rows.extend(external_rows(task, "p2"))
        if system in ("all3", "p2_direct") and task == "mots_surveillance_person60":
            rows.extend(external_rows(task, "p2_direct"))
    else:
        if system in ("both", "p1"):
            rows.extend({**r, "system": "p1"} for r in load_rows(task))
        if system in ("both", "p2") and task == "camouflage":
            rows.extend({**r, "system": "p2"} for r in pipeline_rows())
    pattern = request.args.get("pattern")
    prompt = request.args.get("prompt")
    if pattern:
        rows = [r for r in rows if r["item_id"].split("_")[0] == pattern]
    if prompt:
        rows = [r for r in rows if r["prompt_id"] == prompt]
    order = request.args.get("sort", "iou")
    desc = request.args.get("desc", "0") == "1"
    if order in ("iou", "dice", "latency_s"):
        rows.sort(key=lambda r: (r.get(order) is None, r.get(order) or 0), reverse=desc)
    return jsonify(
        {
            "task": task,
            "system": system,
            "n": len(rows),
            "rows": [
                {
                    "system": r["system"],
                    "item_id": r["item_id"],
                    "prompt_id": r["prompt_id"],
                    "instruction": r.get("instruction", ""),
                    "answer": r.get("answer", ""),
                    "iou": r.get("iou"),
                    "dice": r.get("dice"),
                    "precision": r.get("precision"),
                    "recall": r.get("recall"),
                    "pred_area": r.get("pred_area"),
                    "gt_area": r.get("gt_area"),
                    "latency_s": r.get("latency_s"),
                    "emitted_seg": r.get("emitted_seg"),
                    "expression": r.get("expression", ""),
                    "case_type": r.get("case_type", ""),
                    "difficulty": r.get("difficulty", ""),
                    "target_count": r.get("target_count"),
                    "people_in_image": r.get("people_in_image"),
                    "smallest_person_height_px": r.get("smallest_person_height_px"),
                    "instance_coverage_50": r.get("instance_coverage_50"),
                    "gt_people": r.get("gt_people"),
                    "detected_people_50": r.get("detected_people_50"),
                    "missed_people_50": r.get("missed_people_50"),
                    "person_recall_50": r.get("person_recall_50"),
                    "false_positive_pixels": r.get("false_positive_pixels"),
                    "false_positive_pixel_rate": r.get("false_positive_pixel_rate"),
                    "n_boxes": r.get("n_boxes"),
                    "grounding_query": r.get("grounding_query"),
                }
                for r in rows
            ],
        }
    )


@app.get("/api/overlay")
def api_overlay():
    """Render one result. kind: image | pred | gt | both"""
    task = request.args.get("task", "camouflage")
    system = request.args.get("system", "p1")
    item = request.args.get("item", "")
    prompt = request.args.get("prompt", "")
    kind = request.args.get("kind", "both")

    if system not in ("p1", "p2", "p2_direct"):
        return jsonify(error="system must be p1, p2, or p2_direct"), 400
    if system in ("p2", "p2_direct") and task != "camouflage" and task not in EXTERNAL_RESULTS:
        return jsonify(error="P2 results are unavailable for this dataset"), 404
    if system == "p2_direct" and task != "mots_surveillance_person60":
        return jsonify(error="P2-direct results are unavailable for this dataset"), 404

    img = source_image(task, item)
    if img is None:
        return jsonify(error=f"no source image for {task}/{item}"), 404

    if kind == "image":
        return png_response(shrink(img))

    gt = ground_truth(task, item, img.shape[:2]) if kind in ("gt", "both") else None
    pred = None
    if kind in ("pred", "both"):
        if task in EXTERNAL_RESULTS:
            pred = external_prediction(task, item, prompt, system)
        else:
            pred = (
                pipeline_prediction(item, prompt)
                if system == "p2"
                else prediction(task, item, prompt)
            )

    out = img
    if kind == "gt":
        out = tint(img, gt, (0, 255, 0))
    elif kind == "pred":
        out = tint(img, pred, (255, 0, 0))
    else:
        out = img
        if gt is not None:
            out = tint(out, gt, (0, 255, 0))
        if pred is not None:
            out = tint(out, pred, (255, 0, 0))
    return png_response(shrink(out))


@app.get("/api/pipeline")
def api_pipeline():
    """Saved stage outputs and metrics for the 180 paired comparison cases."""
    return jsonify({"n": len(pipeline_rows()), "rows": pipeline_rows()})


@app.get("/api/pipeline/image")
def api_pipeline_image():
    """Render a real saved stage: original, DINO boxes, SAM, or LISA."""
    item = request.args.get("item", "")
    prompt = request.args.get("prompt", "")
    stage = request.args.get("stage", "original")
    row = pipeline_row(item, prompt)
    if row is None:
        return jsonify(error="unknown pipeline item or prompt"), 404
    if stage not in ("original", "dino", "sam", "lisa"):
        return jsonify(error="unknown pipeline stage"), 400

    img = source_image("camouflage", item)
    if img is None:
        return jsonify(error=f"no source image for camouflage/{item}"), 404
    if stage == "original":
        return png_response(shrink(img))

    if stage == "dino":
        out = img.copy()
        h, w = out.shape[:2]
        for i, box in enumerate(row["boxes"]):
            x1, y1, x2, y2 = [int(round(v)) for v in box]
            x1, x2 = max(0, min(w - 1, x1)), max(0, min(w - 1, x2))
            y1, y2 = max(0, min(h - 1, y1)), max(0, min(h - 1, y2))
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 166, 48), 3)
            label = row["box_labels"][i] if i < len(row["box_labels"]) else "target"
            score = row["box_scores"][i] if i < len(row["box_scores"]) else None
            text = label if score is None else f"{label} {score:.2f}"
            cv2.putText(
                out, text, (x1, max(18, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (255, 166, 48), 2, cv2.LINE_AA,
            )
        return png_response(shrink(out))

    pred = (
        pipeline_prediction(item, prompt)
        if stage == "sam"
        else prediction("camouflage", item, prompt)
    )
    gt = ground_truth("camouflage", item, img.shape[:2])
    out = tint(img, gt, (0, 150, 70))
    out = tint(out, pred, (255, 55, 30))
    return png_response(shrink(out))


@app.get("/api/status")
def api_status():
    import torch

    return jsonify(
        {
            "model_loaded": _engine is not None,
            "model_error": _engine_err,
            "busy": _gpu_lock.locked(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "cuda": torch.cuda.is_available(),
        }
    )


def encoded_overlay(img_rgb, mask):
    n_comp = 0
    if mask.any():
        n, _ = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
        n_comp = n - 1
    ov = shrink(tint(img_rgb, mask, (255, 0, 0)))
    ok, buf = cv2.imencode(
        ".jpg", cv2.cvtColor(ov, cv2.COLOR_RGB2BGR),
        [int(cv2.IMWRITE_JPEG_QUALITY), 85],
    )
    return n_comp, base64.b64encode(buf.tobytes()).decode("ascii") if ok else None


def run_p1_job(jid, img_rgb, prompts, max_new_tokens):
    set_job(jid, state="loading", message="loading P1 · LISA")
    eng = get_engine()
    if eng is None:
        raise RuntimeError(_engine_err or "P1 engine unavailable")
    results = []
    for i, (pid, text) in enumerate(prompts):
        set_job(
            jid,
            state="running",
            message=f"P1 · {pid} ({i + 1}/{len(prompts)})",
            done=i,
            total=len(prompts),
        )
        t0 = time.time()
        response = eng.segment(img_rgb, text, max_new_tokens)
        mask = np.zeros(img_rgb.shape[:2], dtype=bool)
        for predicted in response["masks"]:
            mask |= predicted
        n_comp, overlay = encoded_overlay(img_rgb, mask)
        results.append(
            {
                "system": "p1",
                "prompt_id": pid,
                "prompt": text,
                "answer": response["text"],
                "emitted_seg": response["emitted_seg"],
                "mask_px": int(mask.sum()),
                "mask_pct": 100 * float(mask.mean()),
                "components": n_comp,
                "latency_s": round(time.time() - t0, 1),
                "overlay": overlay,
            }
        )
        set_job(jid, results=list(results))
    return results


def checked_process(args, label, timeout):
    try:
        return subprocess.run(
            args, check=True, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"{label}: required SSH command is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label} timed out") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown remote error").strip()[-1200:]
        raise RuntimeError(f"{label} failed: {detail}") from exc


def p2_ssh_base():
    if not os.path.isfile(P2_REMOTE_KEY):
        raise RuntimeError(f"P2 SSH key is missing: {P2_REMOTE_KEY}")
    return [
        "ssh", "-i", P2_REMOTE_KEY, "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=12", "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=6", P2_REMOTE_HOST,
    ]


def p2_scp_base():
    if not os.path.isfile(P2_REMOTE_KEY):
        raise RuntimeError(f"P2 SSH key is missing: {P2_REMOTE_KEY}")
    return [
        "scp", "-i", P2_REMOTE_KEY, "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=12", "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=6",
    ]


def read_keyed_jsonl(path):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                rows[row["key"]] = row
    return rows


def p2_vqa_instruction(pid, text):
    if pid in P2_VQA_PRESETS:
        return P2_VQA_PRESETS[pid]
    cleaned = " ".join(text.split())
    return (
        f'Question: The user asks, "{cleaned}" What visible object or person '
        "should be located? Answer with only a short noun phrase. Answer:"
    )


def run_p2_job(jid, img_rgb, prompts):
    if not re.fullmatch(r"[0-9a-f]{12}", jid):
        raise RuntimeError("invalid P2 job id")
    remote_dir = f"{P2_REMOTE_BASE}/{jid}"
    ssh = p2_ssh_base()
    scp = p2_scp_base()
    cleanup_command = f"rm -rf -- {remote_dir}"
    wall_started = time.time()

    with tempfile.TemporaryDirectory(prefix="lisa-p2-") as temp_name:
        temp_root = Path(temp_name)
        upload_dir = temp_root / "upload"
        download_dir = temp_root / "download"
        upload_dir.mkdir()
        download_dir.mkdir()
        image_path = upload_dir / "input.jpg"
        ok = cv2.imwrite(str(image_path), cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        if not ok:
            raise RuntimeError("could not prepare the image for P2")

        items = []
        for pid, text in prompts:
            items.append(
                {
                    "key": f"upload::{pid}",
                    "item_id": "upload",
                    "prompt_id": pid,
                    "image": f"{remote_dir}/input.jpg",
                    "lisa_instruction": text,
                    "blip2_instruction": p2_vqa_instruction(pid, text),
                }
            )
        manifest = {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "selection": "website Try an image upload",
            "n_unique_images": 1,
            "n_inferences": len(items),
            "prompt_ids": [pid for pid, _ in prompts],
            "items": items,
        }
        with (upload_dir / "manifest.json").open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)

        try:
            set_job(jid, state="running", message="P2 · uploading to cenara70hx", done=0, total=3)
            checked_process(ssh + [f"mkdir -p -- {remote_dir}"], "P2 remote setup", 60)
            checked_process(
                scp + [str(image_path), str(upload_dir / "manifest.json"), f"{P2_REMOTE_HOST}:{remote_dir}/"],
                "P2 upload", 120,
            )

            phases = (
                ("blip2", "P2 · BLIP-2 / Q-Former (1/3)"),
                ("grounding", "P2 · Grounding DINO (2/3)"),
                ("sam", "P2 · SAM mask (3/3)"),
            )
            for done, (phase, message) in enumerate(phases):
                set_job(jid, state="running", message=message, done=done, total=3)
                remote_command = (
                    f"export HF_HOME={P2_REMOTE_HF_HOME}; "
                    f"{P2_REMOTE_PYTHON} {P2_REMOTE_RUNNER} --phase {phase} "
                    f"--out-dir {remote_dir}"
                )
                checked_process(ssh + [remote_command], message, 1800)

            set_job(jid, state="running", message="P2 · downloading results", done=3, total=3)
            checked_process(
                scp + ["-r", f"{P2_REMOTE_HOST}:{remote_dir}", str(download_dir)],
                "P2 result download", 180,
            )
            result_dir = download_dir / jid
            answers = read_keyed_jsonl(result_dir / "blip2_answers.jsonl")
            boxes = read_keyed_jsonl(result_dir / "grounding_boxes.jsonl")
            sam_rows = read_keyed_jsonl(result_dir / "sam_timings.jsonl")

            results = []
            for pid, text in prompts:
                key = f"upload::{pid}"
                answer_row, box_row, sam_row = answers[key], boxes[key], sam_rows[key]
                mask_img = cv2.imread(
                    str(result_dir / "masks" / f"upload__{pid}.png"),
                    cv2.IMREAD_GRAYSCALE,
                )
                if mask_img is None:
                    raise RuntimeError(f"P2 returned no mask file for {pid}")
                mask = mask_img > 127
                n_comp, overlay = encoded_overlay(img_rgb, mask)
                results.append(
                    {
                        "system": "p2",
                        "prompt_id": pid,
                        "prompt": text,
                        "answer": answer_row["answer"],
                        "grounding_query": box_row["query"],
                        "n_boxes": len(box_row["boxes"]),
                        "emitted_seg": bool(box_row["boxes"]),
                        "mask_px": int(mask.sum()),
                        "mask_pct": 100 * float(mask.mean()),
                        "components": n_comp,
                        "latency_s": round(
                            float(answer_row["latency_s"])
                            + float(box_row["latency_s"])
                            + float(sam_row["latency_s"]),
                            1,
                        ),
                        "wall_time_s": round(time.time() - wall_started, 1),
                        "overlay": overlay,
                    }
                )
            return results
        finally:
            # The path is derived only from a validated random hex job id and is
            # kept under the dedicated live-job directory.
            try:
                subprocess.run(
                    ssh + [cleanup_command], capture_output=True, text=True, timeout=60
                )
            except Exception:
                pass


def run_job(jid, img_rgb, prompts, max_new_tokens, system):
    try:
        with _gpu_lock:
            results = (
                run_p1_job(jid, img_rgb, prompts, max_new_tokens)
                if system == "p1"
                else run_p2_job(jid, img_rgb, prompts)
            )
        total = len(prompts) if system == "p1" else 3
        set_job(
            jid, state="done", message="complete", done=total,
            total=total, results=results, system=system,
        )
    except Exception as exc:  # noqa: BLE001
        set_job(jid, state="error", message=f"{type(exc).__name__}: {exc}")


@app.post("/api/segment")
def api_segment():
    f = request.files.get("image")
    if f is None:
        return jsonify(error="no image uploaded"), 400
    data = np.frombuffer(f.read(), np.uint8)
    bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if bgr is None:
        return jsonify(error="could not decode that file as an image"), 400
    img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    # A very large upload costs minutes of CPU in the SAM encoder for no gain.
    img = shrink(img, 1600)

    custom = (request.form.get("prompt") or "").strip()
    preset_ids = [p for p in request.form.getlist("presets") if p in PROMPT_PRESETS]
    prompts = [(p, PROMPT_PRESETS[p]) for p in preset_ids]
    if custom:
        prompts.append(("custom", custom))
    if not prompts:
        prompts = [("p2_explicit", PROMPT_PRESETS["p2_explicit"])]

    system = (request.form.get("system") or "p1").strip().lower()
    if system not in ("p1", "p2"):
        return jsonify(error="system must be p1 or p2"), 400

    try:
        mnt = max(8, min(128, int(request.form.get("max_new_tokens", 32))))
    except ValueError:
        mnt = 32

    jid = uuid.uuid4().hex[:12]
    total = len(prompts) if system == "p1" else 3
    set_job(
        jid, state="queued", message="queued", done=0, total=total,
        results=[], system=system,
    )
    threading.Thread(
        target=run_job, args=(jid, img, prompts, mnt, system), daemon=True
    ).start()
    return jsonify(job_id=jid, n_prompts=len(prompts), system=system)


@app.get("/api/job/<jid>")
def api_job(jid):
    j = get_job(jid)
    if j is None:
        return jsonify(error="unknown job"), 404
    return jsonify(j)


if __name__ == "__main__":
    print("building analysis from results/ ...", flush=True)
    a = analysis()
    print(
        f"  camouflage {a['counts']['camouflage']} rows, "
        f"reasonseg {a['counts']['reasonseg']}, drone {a['counts']['drone']}",
        flush=True,
    )
    print("\n  http://127.0.0.1:5000\n", flush=True)
    print(
        "P1 loads on first use and stays resident; P2 runs remotely on cenara70hx.\n",
        flush=True,
    )
    app.run(host="127.0.0.1", port=5000, threaded=True, debug=False)
