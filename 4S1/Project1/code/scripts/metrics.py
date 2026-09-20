"""Mask-quality metrics, matching what the LISA paper reports.

The paper scores reasoning segmentation with gIoU and cIoU:

    gIoU = mean over images of per-image IoU        (every image weighs the same)
    cIoU = (sum of intersections) / (sum of unions)  (large objects dominate)

cIoU is the reason a model can look strong on gIoU and weak on cIoU (or the
reverse) on datasets with very uneven object sizes - which is exactly the case
for CamouflageData, where targets cover ~0.5% of the frame.

ReasonSeg ground truth carries a third state: pixels labelled 255 are "ignore"
regions (ambiguous boundaries) and must be excluded from both numerator and
denominator, so every function here takes an optional `ignore` mask.
"""

from typing import Dict, Optional

import numpy as np


def confusion(
    pred: np.ndarray, gt: np.ndarray, ignore: Optional[np.ndarray] = None
) -> Dict[str, int]:
    pred = pred.astype(bool)
    gt = gt.astype(bool)
    if ignore is not None:
        keep = ~ignore.astype(bool)
        pred, gt = pred & keep, gt & keep
    inter = int(np.logical_and(pred, gt).sum())
    union = int(np.logical_or(pred, gt).sum())
    return {
        "intersection": inter,
        "union": union,
        "pred_area": int(pred.sum()),
        "gt_area": int(gt.sum()),
    }


def per_image_metrics(
    pred: np.ndarray, gt: np.ndarray, ignore: Optional[np.ndarray] = None
) -> Dict[str, float]:
    c = confusion(pred, gt, ignore)
    inter, union = c["intersection"], c["union"]
    p_area, g_area = c["pred_area"], c["gt_area"]

    # An empty prediction on an empty ground truth is a correct answer, not a
    # zero - guard the degenerate case explicitly instead of dividing by zero.
    iou = 1.0 if union == 0 else inter / union
    dice = 1.0 if (p_area + g_area) == 0 else 2 * inter / (p_area + g_area)
    precision = 1.0 if p_area == 0 else inter / p_area
    recall = 1.0 if g_area == 0 else inter / g_area

    out = dict(c)
    out.update(iou=iou, dice=dice, precision=precision, recall=recall)
    return out


def aggregate(rows) -> Dict[str, float]:
    """Roll per-image rows up into the paper's gIoU/cIoU plus supporting means."""
    rows = [r for r in rows if r is not None]
    if not rows:
        return {}
    tot_i = sum(r["intersection"] for r in rows)
    tot_u = sum(r["union"] for r in rows)
    n = len(rows)
    return {
        "n_images": n,
        "gIoU": sum(r["iou"] for r in rows) / n,
        "cIoU": (tot_i / tot_u) if tot_u else 0.0,
        "mean_dice": sum(r["dice"] for r in rows) / n,
        "mean_precision": sum(r["precision"] for r in rows) / n,
        "mean_recall": sum(r["recall"] for r in rows) / n,
        "seg_emit_rate": sum(1.0 for r in rows if r.get("emitted_seg", True)) / n,
        "iou_at_50": sum(1.0 for r in rows if r["iou"] >= 0.5) / n,
        "iou_at_25": sum(1.0 for r in rows if r["iou"] >= 0.25) / n,
        "mean_latency_s": sum(r.get("latency_s", 0.0) for r in rows) / n,
    }
