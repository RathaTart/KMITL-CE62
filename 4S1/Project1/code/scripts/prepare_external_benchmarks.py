"""Prepare self-contained gRefCOCO and MOTSChallenge benchmark manifests."""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from pycocotools import mask as mask_utils
from pycocotools.coco import COCO


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def ann_ids(ref: dict[str, Any]) -> list[int]:
    value = ref.get("ann_id", [])
    if not isinstance(value, list):
        value = [value]
    return [int(item) for item in value]


def ann_to_mask(coco: COCO, ann: dict[str, Any]) -> np.ndarray:
    return coco.annToMask(ann).astype(bool)


def person_language(text: str) -> bool:
    return bool(
        re.search(
            r"\b(person|people|man|men|woman|women|boy|boys|girl|girls|kid|kids|"
            r"child|children|pedestrian|pedestrians|player|players|guy|guys|lady|ladies)\b",
            text.lower(),
        )
    )


def select_unique(
    candidates: list[dict[str, Any]], count: int, rng: random.Random, used_images: set[int]
) -> list[dict[str, Any]]:
    shuffled = candidates[:]
    rng.shuffle(shuffled)
    chosen = []
    for row in shuffled:
        if row["image_id"] in used_images:
            continue
        chosen.append(row)
        used_images.add(row["image_id"])
        if len(chosen) == count:
            return chosen
    # If a category has too few unique images, allow another expression from a
    # previously used image rather than silently reducing the benchmark.
    for row in shuffled:
        if row in chosen:
            continue
        chosen.append(row)
        if len(chosen) == count:
            return chosen
    raise RuntimeError(f"Only found {len(chosen)} of {count} requested samples")


def prepare_grefcoco(args: argparse.Namespace) -> None:
    data_root = args.data_root.resolve()
    refs_path = data_root / "grefs(unc).json"
    instances_path = data_root / "instances.json"
    refs = json.loads(refs_path.read_text(encoding="utf-8"))
    coco = COCO(str(instances_path))
    person_cat = next(cat["id"] for cat in coco.dataset["categories"] if cat["name"] == "person")
    person_anns_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ann in coco.dataset["annotations"]:
        if ann["category_id"] == person_cat and not ann.get("iscrowd", 0):
            person_anns_by_image[int(ann["image_id"])].append(ann)

    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ref in refs:
        split = ref.get("split")
        if split not in {args.split, args.single_split}:
            continue
        ids = ann_ids(ref)
        positive = [coco.anns[item] for item in ids if item != -1 and item in coco.anns]
        sentences = ref.get("sentences") or []
        for sentence in sentences:
            expression = safe_text(sentence.get("sent", ""))
            if not expression:
                continue
            base = {
                "ref_id": int(ref["ref_id"]),
                "sent_id": int(sentence.get("sent_id", ref["ref_id"])),
                "image_id": int(ref["image_id"]),
                "expression": expression,
                "target_ann_ids": [int(ann["id"]) for ann in positive],
            }
            if split == args.split and ids == [-1] and person_language(expression):
                candidates["no_target"].append(base)
            elif positive and all(ann["category_id"] == person_cat for ann in positive):
                if split == args.split and len(positive) >= 2:
                    candidates["multi_target"].append(base)
                elif (
                    split == args.single_split
                    and len(positive) == 1
                    and len(person_anns_by_image[base["image_id"]]) >= 2
                ):
                    candidates["single_in_crowd"].append(base)

    rng = random.Random(args.seed)
    used_images: set[int] = set()
    selected = []
    for name, count in (
        ("multi_target", args.multi),
        ("single_in_crowd", args.single),
        ("no_target", args.no_target),
    ):
        print(f"gRefCOCO candidates {name}: {len(candidates[name])}")
        selected.extend(select_unique(candidates[name], count, rng, used_images))
    selected.sort(key=lambda row: (row["image_id"], row["sent_id"]))

    image_dir = args.out_dir / "inputs" / "images"
    gt_dir = args.out_dir / "inputs" / "gt"
    instance_dir = args.out_dir / "inputs" / "instances"
    for directory in (image_dir, gt_dir, instance_dir):
        directory.mkdir(parents=True, exist_ok=True)

    def download_image(row: dict[str, Any]) -> str:
        image_info = coco.imgs[row["image_id"]]
        file_name = image_info["file_name"]
        image_path = image_dir / file_name
        if not image_path.exists():
            # COCO's HTTP endpoint is intentional: this remote campus network
            # presents a mismatched TLS certificate for the image CDN.
            url = f"http://images.cocodataset.org/train2014/{file_name}"
            urllib.request.urlretrieve(url, image_path)
        return file_name

    print(f"Downloading {len(selected)} selected COCO images (8 workers)", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for index, file_name in enumerate(pool.map(download_image, selected), 1):
            print(f"downloaded {index}/{len(selected)} {file_name}", flush=True)

    items = []
    for index, row in enumerate(selected, 1):
        image_info = coco.imgs[row["image_id"]]
        file_name = image_info["file_name"]
        image_path = image_dir / file_name

        target_anns = [coco.anns[item] for item in row["target_ann_ids"]]
        target_masks = [ann_to_mask(coco, ann) for ann in target_anns]
        if target_masks:
            union = np.logical_or.reduce(target_masks)
        else:
            union = np.zeros((image_info["height"], image_info["width"]), dtype=bool)
        item_id = f"gref_{row['sent_id']}"
        gt_path = gt_dir / f"{item_id}.png"
        cv2.imwrite(str(gt_path), union.astype(np.uint8) * 255)
        instance_paths = []
        heights = []
        for instance_index, (ann, mask) in enumerate(zip(target_anns, target_masks), 1):
            path = instance_dir / f"{item_id}__{instance_index}.png"
            cv2.imwrite(str(path), mask.astype(np.uint8) * 255)
            instance_paths.append(str(path))
            heights.append(float(ann["bbox"][3]))

        expression = row["expression"]
        case_type = (
            "no_target" if not target_anns else "multi_target" if len(target_anns) >= 2 else "single_in_crowd"
        )
        items.append(
            {
                "key": f"{item_id}::expression",
                "item_id": item_id,
                "prompt_id": "expression",
                "image": str(image_path),
                "ground_truth": str(gt_path),
                "ground_truth_instances": instance_paths,
                "expression": expression,
                "case_type": case_type,
                "difficulty": case_type,
                "target_count": len(target_anns),
                "people_in_image": len(person_anns_by_image[row["image_id"]]),
                "smallest_person_height_px": min(heights) if heights else None,
                "lisa_instruction": f"{expression} Please output segmentation mask.",
                "blip2_instruction": (
                    "Question: Which person or people match this description: "
                    f"{expression}? If nobody matches, answer no person. "
                    "Answer with only a short noun phrase. Answer:"
                ),
            }
        )

    write_json(
        args.out_dir / "manifest.json",
        {
            "dataset": "grefcoco",
            "dataset_label": "gRefCOCO multi-person",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "selection": (
                f"fixed seed {args.seed}; {args.split} split for multi/no-target and "
                f"{args.single_split} for single-target; {args.multi} multi-target person, "
                f"{args.single} single-target person in crowd, {args.no_target} no-target person expressions"
            ),
            "source": "https://github.com/henghuiding/gRefCOCO",
            "seed": args.seed,
            "items": items,
        },
    )
    print(f"Prepared gRefCOCO manifest with {len(items)} items in {args.out_dir}")


def decode_rle(height: int, width: int, counts: str) -> np.ndarray:
    rle = {"size": [height, width], "counts": counts.encode("ascii")}
    return mask_utils.decode(rle).astype(bool)


def locate_mots(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    images: dict[str, Path] = {}
    for directory in root.rglob("img1"):
        if directory.parent.name.startswith(("MOTS20-", "MOT17-", "MOT16-")):
            images[directory.parent.name] = directory
    for directory in root.rglob("images/*"):
        if directory.is_dir() and any(directory.glob("*.jpg")):
            images[directory.name] = directory
    annotations: dict[str, Path] = {}
    for path in root.rglob("*.txt"):
        if path.parent.name == "instances_txt":
            annotations[path.stem] = path
        elif path.name == "gt.txt" and path.parent.parent.name in images:
            # Accept this only if it is the six-column MOTS RLE format.
            first = next((line for line in path.read_text().splitlines() if line.strip()), "")
            if len(first.split()) >= 6 and "," not in first:
                annotations[path.parent.parent.name] = path
    common = sorted(set(images) & set(annotations))
    if not common:
        raise RuntimeError(
            f"Could not find matching MOTS img1 and instance annotation directories under {root}"
        )
    return ({name: images[name] for name in common}, {name: annotations[name] for name in common})


def prepare_mots(args: argparse.Namespace) -> None:
    image_dirs, annotation_files = locate_mots(args.data_root.resolve())
    frames_by_sequence: dict[str, dict[int, dict[str, Any]]] = {}
    for sequence, path in annotation_files.items():
        frames: dict[int, dict[str, Any]] = defaultdict(lambda: {"people": [], "ignore": []})
        with path.open() as fh:
            for line in fh:
                parts = line.strip().split(maxsplit=5)
                if len(parts) != 6:
                    continue
                frame, track_id, class_id, height, width = map(int, parts[:5])
                record = {
                    "height": height,
                    "width": width,
                    "counts": parts[5],
                    "track_id": track_id,
                }
                if class_id == 2:
                    bbox = mask_utils.toBbox(
                        {"size": [height, width], "counts": parts[5].encode("ascii")}
                    ).tolist()
                    record["bbox"] = bbox
                    frames[frame]["people"].append(record)
                elif track_id == 10000 or class_id == 10:
                    frames[frame]["ignore"].append(record)
        frames_by_sequence[sequence] = dict(frames)
        print(f"MOTS {sequence}: {len(frames)} annotated frames")

    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sequence, frames in frames_by_sequence.items():
        for frame, record in frames.items():
            if len(record["people"]) < 2:
                continue
            heights = [float(person["bbox"][3]) for person in record["people"]]
            smallest = min(heights)
            difficulty = "tiny_le_32px" if smallest <= 32 else "small_33_64px" if smallest <= 64 else "medium_gt_64px"
            candidates[sequence].append(
                {
                    "sequence": sequence,
                    "frame": frame,
                    "smallest": smallest,
                    "difficulty": difficulty,
                    **record,
                }
            )

    rng = random.Random(args.seed)
    chosen = []
    target_per_sequence = max(1, args.count // len(candidates))
    for sequence in sorted(candidates):
        preferred = [row for row in candidates[sequence] if row["smallest"] <= args.max_height]
        rng.shuffle(preferred)
        accepted = []
        for row in preferred:
            if all(abs(row["frame"] - old["frame"]) >= args.min_frame_gap for old in accepted):
                accepted.append(row)
            if len(accepted) == target_per_sequence:
                break
        chosen.extend(accepted)
    if len(chosen) < args.count:
        remainder = [
            row
            for rows in candidates.values()
            for row in rows
            if row not in chosen and row["smallest"] <= args.max_height
        ]
        remainder.sort(key=lambda row: (row["smallest"], row["sequence"], row["frame"]))
        chosen.extend(remainder[: args.count - len(chosen)])
    chosen = chosen[: args.count]
    if len(chosen) < args.count:
        raise RuntimeError(f"Only selected {len(chosen)} of {args.count} requested MOTS frames")
    chosen.sort(key=lambda row: (row["sequence"], row["frame"]))

    image_out = args.out_dir / "inputs" / "images"
    gt_out = args.out_dir / "inputs" / "gt"
    instance_out = args.out_dir / "inputs" / "instances"
    ignore_out = args.out_dir / "inputs" / "ignore"
    for directory in (image_out, gt_out, instance_out, ignore_out):
        directory.mkdir(parents=True, exist_ok=True)

    items = []
    for row in chosen:
        sequence, frame = row["sequence"], row["frame"]
        image_candidates = list(image_dirs[sequence].glob(f"{frame:06d}.*"))
        if not image_candidates:
            image_candidates = list(image_dirs[sequence].glob(f"{frame + 1:06d}.*"))
        if not image_candidates:
            raise FileNotFoundError(f"Frame {frame} for {sequence}")
        source_image = image_candidates[0]
        display_sequence = f"MOTS20-{int(sequence):02d}" if sequence.isdigit() else sequence
        item_id = f"{display_sequence}_{frame:06d}"
        image_path = image_out / f"{item_id}{source_image.suffix.lower()}"
        shutil.copy2(source_image, image_path)
        masks = [decode_rle(p["height"], p["width"], p["counts"]) for p in row["people"]]
        union = np.logical_or.reduce(masks)
        gt_path = gt_out / f"{item_id}.png"
        cv2.imwrite(str(gt_path), union.astype(np.uint8) * 255)
        instance_paths = []
        for index, mask in enumerate(masks, 1):
            path = instance_out / f"{item_id}__{index}.png"
            cv2.imwrite(str(path), mask.astype(np.uint8) * 255)
            instance_paths.append(str(path))
        ignore_masks = [decode_rle(p["height"], p["width"], p["counts"]) for p in row["ignore"]]
        ignore = np.logical_or.reduce(ignore_masks) if ignore_masks else np.zeros_like(union)
        ignore_path = ignore_out / f"{item_id}.png"
        cv2.imwrite(str(ignore_path), ignore.astype(np.uint8) * 255)
        expression = "all people walking or standing in the street"
        items.append(
            {
                "key": f"{item_id}::all_people",
                "item_id": item_id,
                "prompt_id": "all_people",
                "image": str(image_path),
                "ground_truth": str(gt_path),
                "ground_truth_instances": instance_paths,
                "ignore_mask": str(ignore_path),
                "expression": expression,
                "case_type": "all_people",
                "difficulty": row["difficulty"],
                "target_count": len(masks),
                "people_in_image": len(masks),
                "smallest_person_height_px": row["smallest"],
                "sequence": display_sequence,
                "frame": frame,
                "lisa_instruction": "Please segment all people visible in this street scene.",
                "blip2_instruction": (
                    "Question: Who is visible in this street scene? "
                    "Answer with only a short plural noun phrase. Answer:"
                ),
            }
        )

    write_json(
        args.out_dir / "manifest.json",
        {
            "dataset": "mots_small_person",
            "dataset_label": "MOTSChallenge small street pedestrians",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "selection": (
                f"fixed seed {args.seed}; {args.count} labeled training frames; at least 2 people; "
                f"smallest person height <= {args.max_height}px; temporal gap >= {args.min_frame_gap} frames"
            ),
            "source": "https://motchallenge.net/data/CVPR_2020_MOTS_Challenge/",
            "seed": args.seed,
            "items": items,
        },
    )
    print(f"Prepared MOTS manifest with {len(items)} frames in {args.out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="dataset", required=True)
    gref = sub.add_parser("grefcoco")
    gref.add_argument("--data-root", type=Path, required=True)
    gref.add_argument("--out-dir", type=Path, required=True)
    gref.add_argument("--split", default="val")
    gref.add_argument("--single-split", default="testA")
    gref.add_argument("--multi", type=int, default=75)
    gref.add_argument("--single", type=int, default=50)
    gref.add_argument("--no-target", type=int, default=25)
    gref.add_argument("--seed", type=int, default=20260824)
    mots = sub.add_parser("mots")
    mots.add_argument("--data-root", type=Path, required=True)
    mots.add_argument("--out-dir", type=Path, required=True)
    mots.add_argument("--count", type=int, default=60)
    mots.add_argument("--max-height", type=float, default=64.0)
    mots.add_argument("--min-frame-gap", type=int, default=20)
    mots.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.dataset == "grefcoco":
        prepare_grefcoco(args)
    else:
        prepare_mots(args)


if __name__ == "__main__":
    main()
