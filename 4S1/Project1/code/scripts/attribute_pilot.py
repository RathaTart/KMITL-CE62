"""Remote-only development experiment; never treat this reused pilot as final test.

Run from /home/osta/lisa-eval/code with the BLIP-2 venv and HF_HOME set.
Stages: prepare, direct, candidates, verify, masks, score.
"""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
from PIL import Image

from run_blip2_grounded_sam import phase_blip2, phase_grounding, phase_sam, DEFAULT_BLIP2, DEFAULT_GROUNDING, DEFAULT_SAM


def read(p):
    return json.loads(Path(p).read_text())


def write(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2), encoding="utf-8")


def lines(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def jsonl(p, rows):
    Path(p).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def prepare(a):
    source = read(a.source / "manifest.json")
    if a.custom:
        import copy
        original = next(i for i in source["items"] if i["item_id"] == "gref_197965")
        items = []
        for label, expression, instance in [
            ("hat_light_shirt", "person wearing a blue hat and a white shirt", 2),
            ("hat_black_jacket", "person wearing a blue hat and a black jacket", None),
            ("brown_shirt", "person wearing a brown shirt", 1),
        ]:
            item = copy.deepcopy(original)
            item.update(item_id=label, key=label+"::expression", expression=expression,
                case_type="single_in_crowd" if instance else "no_target", target_count=1 if instance else 0,
                lisa_instruction=expression+" Please output segmentation mask.",
                blip2_instruction=f"Question: Which person matches this description: {expression}? Answer with only a short noun phrase. Answer:")
            if instance:
                item["ground_truth"] = original["ground_truth_instances"][instance-1]
            else:
                empty = a.out.resolve() / "empty_gt.png"
                empty.parent.mkdir(parents=True, exist_ok=True)
                Image.new("L", Image.open(original["image"]).size).save(empty)
                item["ground_truth"] = str(empty)
            item["ground_truth_instances"] = [item["ground_truth"]] if instance else []
            items.append(item)
        source["items"] = items
        source["custom_annotation"] = "One visually inspected COCO image; instance 2 blue/white hat with light shirt, instance 1 brown shirt; black jacket is a visible no-match counterfactual. Diagnostic only, not independent samples."
    for item in source["items"]:
        for field in ["image", "ground_truth"]:
            item[field] = str(Path(item[field]).resolve())
    source["status"] = "development only: three diagnostic prompts on one inspected image" if a.custom else "development only: reused 30-expression pilot, mixed original splits"
    source["original_source"] = str(a.source.resolve())
    source["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    source["host"] = platform.node()
    for variant in ["direct", "candidates", "verified", "prompt_fixed"]:
        folder = a.out / variant
        write(folder / "manifest.json", source)
        jsonl(folder / "blip2_answers.jsonl", [dict(key=i["key"], answer=i["expression"] if variant == "direct" else "person") for i in source["items"]])
        if variant == "prompt_fixed":
            for item in source["items"]:
                item["blip2_instruction"] = item["blip2_instruction"].replace("If nobody matches, answer no person. ", "")
            write(folder / "manifest.json", source)
            (folder / "blip2_answers.jsonl").unlink()
    write(a.out / "protocol.json", {
        "status": source["status"], "seed": 20260914,
        "thresholds": {"box": .25, "text": .25, "nms": .5},
        "selection": "all candidates with exact yes answer; no forced top-1",
        "limitations": ["crop verification loses scene relationships", "yes/no is not calibrated", "no tuning or final-test claim", "candidate cap 12 by detector confidence"],
        "source_sha256": hashlib.sha256((a.source / "manifest.json").read_bytes()).hexdigest(),
        "script_sha256": source["script_sha256"],
    })


def verify(a):
    import torch
    from torchvision.ops import nms
    from transformers import AutoProcessor, BitsAndBytesConfig, Blip2ForConditionalGeneration
    torch.manual_seed(20260914)
    model_id = "Salesforce/blip2-flan-t5-xl"
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
    model = Blip2ForConditionalGeneration.from_pretrained(model_id, local_files_only=True,
        device_map="auto", quantization_config=BitsAndBytesConfig(load_in_8bit=True), torch_dtype=torch.float16).eval()
    boxes = {r["key"]: r for r in lines(a.out / "candidates/grounding_boxes.jsonl")}
    rows, audit = [], []
    torch.cuda.reset_peak_memory_stats()
    for item in read(a.out / "verified/manifest.json")["items"]:
        image = Image.open(item["image"]).convert("RGB")
        row = boxes[item["key"]]
        keep = nms(torch.tensor(row["boxes"], dtype=torch.float32).reshape(-1, 4), torch.tensor(row["scores"]), .5).tolist()[:12]
        accepted = []
        torch.cuda.synchronize()
        start = time.perf_counter()
        for idx in keep:
            b = row["boxes"][idx]
            crop = image.crop((max(0, int(b[0])), max(0, int(b[1])), min(image.width, int(b[2])+1), min(image.height, int(b[3])+1)))
            prompt = f'Question: Does the person in this image match the description "{item["expression"]}"? Answer yes or no. Answer:'
            inp = processor(images=crop, text=prompt, return_tensors="pt")
            inp = {k:v.to("cuda", dtype=torch.float16) if v.is_floating_point() else v.to("cuda") for k,v in inp.items()}
            with torch.inference_mode():
                output = model.generate(**inp, max_new_tokens=4, do_sample=False)
            answer = processor.batch_decode(output, skip_special_tokens=True)[0].strip().lower().rstrip(".! ")
            audit.append(dict(key=item["key"], candidate=idx, box=b, prompt=prompt, answer=answer))
            if answer == "yes":
                accepted.append(idx)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        rows.append(dict(row, boxes=[row["boxes"][j] for j in accepted], scores=[row["scores"][j] for j in accepted], labels=["verified person"]*len(accepted), verification_s=elapsed))
        print(item["key"], "accepted", len(accepted), "of", len(keep), flush=True)
    jsonl(a.out / "verified/grounding_boxes.jsonl", rows)
    jsonl(a.out / "verification.jsonl", audit)
    write(a.out / "verification_config.json", dict(model=model_id, peak_vram_gib=torch.cuda.max_memory_allocated()/1024**3, torch=torch.__version__, gpu=torch.cuda.get_device_name()))


def score(a):
    items = read(a.out / "direct/manifest.json")["items"]
    summary, allrows = {}, []
    variants = [("LISA_existing", a.source / "p1_masks"), ("BLIP2_existing", a.source / "masks"), ("direct", a.out / "direct/masks"), ("verified", a.out / "verified/masks")]
    if (a.out / "prompt_fixed/masks").exists():
        variants.append(("prompt_fixed", a.out / "prompt_fixed/masks"))
    if (a.out / "yolo/p3_expression/masks").exists():
        variants.append(("YOLO_expression_SAM", a.out / "yolo/p3_expression/masks"))
    if (a.out / "context/masks").exists():
        variants.append(("context", a.out / "context/masks"))
    if (a.out / "top1/masks").exists():
        variants.append(("top1", a.out / "top1/masks"))
    for variant, folder in variants:
        if variant.endswith("_existing") and a.custom:
            continue
        response_validity = {}
        if variant == "context":
            response_validity = {r["key"]:r["valid_json"] for r in lines(a.out / "context/selection_audit.jsonl")}
        rows = []
        for i in items:
            p = np.asarray(Image.open(folder / f'{i["item_id"]}__{i["prompt_id"]}.png')) > 0
            g = np.asarray(Image.open(i["ground_truth"])) > 0
            if p.shape != g.shape:
                raise ValueError("Mask dimensions differ")
            intersection, union = int((p & g).sum()), int((p | g).sum())
            valid = response_validity.get(i["key"], True)
            mask_iou = intersection/union if union else 1.
            rows.append(dict(key=i["key"], expression=i["expression"], case_type=i["case_type"], variant=variant, intersection=intersection, union=union,
                iou=mask_iou if valid else 0., mask_iou=mask_iou, response_valid=valid, predicted_pixels=int(p.sum()), target_pixels=int(g.sum())))
        allrows.extend(rows)
        summary[variant] = {}
        for group in ["all", "positive", "single_in_crowd", "multi_target", "no_target"]:
            subset = [r for r in rows if group == "all" or r["case_type"] == group or (group == "positive" and r["case_type"] != "no_target")]
            if not subset:
                continue
            total_union = sum(r["union"] for r in subset)
            summary[variant][group] = dict(n=len(subset), mean_iou=float(np.mean([r["iou"] for r in subset])),
                cumulative_iou=sum(r["intersection"] for r in subset)/total_union if total_union else None,
                success_iou50=sum(r["iou"] >= .5 for r in subset)/len(subset),
                empty_prediction_rate=sum(r["predicted_pixels"] == 0 for r in subset)/len(subset),
                invalid_response_rate=sum(not r["response_valid"] for r in subset)/len(subset),
                no_match_accuracy=sum(r["predicted_pixels"] == 0 and r["response_valid"] for r in subset)/len(subset) if group == "no_target" else None)
    write(a.out / "comparison.json", summary)
    jsonl(a.out / "per_expression.jsonl", allrows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "direct", "candidates", "verify", "masks", "score", "prompt_fixed"])
    parser.add_argument("--source", type=Path, default=Path("results/grefcoco_pilot_p1_p2"))
    parser.add_argument("--out", type=Path, default=Path("results/attribute_pilot_20260914"))
    parser.add_argument("--custom", action="store_true", help="Three manually specified diagnostic prompts on one inspected image")
    a = parser.parse_args()
    invocation_start = time.perf_counter()
    invocation_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if a.stage == "prepare": prepare(a)
    elif a.stage in ["direct", "candidates"]: phase_grounding(a.out / a.stage, DEFAULT_GROUNDING, .25, .25, 0)
    elif a.stage == "verify": verify(a)
    elif a.stage == "prompt_fixed":
        folder = a.out / "prompt_fixed"
        source = read(a.out / "direct/manifest.json")
        for item in source["items"]:
            item["blip2_instruction"] = item["blip2_instruction"].replace("If nobody matches, answer no person. ", "")
        write(folder / "manifest.json", source)
        phase_blip2(folder, DEFAULT_BLIP2, 0)
        phase_grounding(folder, DEFAULT_GROUNDING, .25, .25, 0)
        phase_sam(folder, DEFAULT_SAM, 0)
    elif a.stage == "masks":
        for variant in ["direct", "verified"]: phase_sam(a.out / variant, DEFAULT_SAM, 0)
    else: score(a)
    import resource
    write(a.out / ("stage_" + a.stage + ".json"), {
        "host": platform.node(), "script_sha256": invocation_hash,
        "stage_wall_s_including_loading": time.perf_counter() - invocation_start,
        "process_peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "note": "Linux process peak RSS; stage wall time includes loading, not an interactive end-to-end request latency",
    })
