"""Run on cenara70hx after scoring; verify artifacts and record provenance."""
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def load(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records = {}
def jsonlines(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
for name in ["attribute_pilot_20260914", "attribute_custom_20260914"]:
    folder = root / "results" / name
    manifest = load(folder / "direct/manifest.json")
    summary = load(folder / "comparison.json")
    rows = [json.loads(l) for l in (folder / "per_expression.jsonl").read_text().splitlines()]
    keys = {i["key"] for i in manifest["items"]}
    assert len(keys) == len(manifest["items"])
    for system in summary:
        selected = [r for r in rows if r["variant"] == system]
        assert len(selected) == len(keys) and {r["key"] for r in selected} == keys
        assert all(0 <= r["iou"] <= 1 for r in selected)
    if name == "attribute_pilot_20260914":
        old = load(root / "results/grefcoco_pilot_p1_p2/summary.json")
        assert abs(summary["LISA_existing"]["all"]["mean_iou"] - old["systems"]["p1"]["overall"]["gIoU"]) < 1e-12
        assert abs(summary["BLIP2_existing"]["all"]["mean_iou"] - old["systems"]["p2"]["overall"]["gIoU"]) < 1e-12
    hashes = {str(p.relative_to(folder)):digest(p) for p in folder.rglob("*") if p.is_file() and p.suffix in [".json", ".jsonl", ".png"] and p.name not in ["audit.json", "environment.json", "resources.json"]}
    inputs = {i["image"]:digest(Path(i["image"])) for i in manifest["items"]}
    records[name] = dict(items=len(keys), systems=list(summary), artifact_sha256=hashes, input_sha256=inputs)
    (folder / "audit.json").write_text(json.dumps(records[name], indent=2))
    resources = {}
    for variant in ['direct', 'verified', 'prompt_fixed', 'context', 'yolo/p3_expression']:
        target = folder / variant
        if not (target / 'sam_timings.jsonl').exists():
            continue
        ground = jsonlines(target / 'grounding_boxes.jsonl')
        sam = jsonlines(target / 'sam_timings.jsonl')
        blip = jsonlines(target / 'blip2_answers.jsonl') if variant == 'prompt_fixed' else []
        total = sum(r.get('latency_s',0)+r.get('verification_s',0) for r in ground)
        total += sum(r.get('latency_s',0) for r in sam+blip)
        configs = list(target.glob('*config.json'))
        if variant in ['verified','context']:
            configs += [folder/'candidates/grounding_config.json']
        if variant == 'verified':
            configs += [folder/'verification_config.json']
        peaks = []
        for config in configs:
            if config.exists():
                values=load(config)
                peak=values.get('peak_vram_gib',values.get('peak_vram_gb'))
                if peak is not None: peaks.append(peak)
        resources[variant]=dict(mean_recorded_component_s=total/len(keys),largest_stage_peak_allocated_gib=max(peaks) if peaks else None)
    resources['definition']='Sum of recorded component timers, averaged over all requests. Timer boundaries differ and exclude model loading and some preprocessing; NOT a fair end-to-end latency ranking. Memory is largest serial-stage PyTorch allocation, not total driver memory.'
    (folder/'resources.json').write_text(json.dumps(resources,indent=2))
cache = Path(os.environ["HF_HOME"]) / "hub"
environment = dict(host=platform.node(), python=platform.python_version(),
    packages={p:importlib.metadata.version(p) for p in ["torch", "transformers", "numpy", "Pillow", "bitsandbytes"]},
    cached_revisions={p.parent.parent.name:p.read_text().strip() for p in cache.glob("models--*/refs/main")},
    script_sha256={p.name:digest(p) for p in Path(__file__).parent.glob("*.py") if p.name in ["attribute_pilot.py", "context_selector.py", "run_blip2_grounded_sam.py", "audit_attribute_results.py"]})
external = Path("/home/osta/Yolo_World/scripts/yoloworld_backend.py")
environment["yolo_backend_sha256"] = digest(external)
environment["yolo_checkpoint_sha256"] = digest(Path("/home/osta/Yolo_World/weights/yolov8s-worldv2.pt"))
for name in records:
    (root / "results" / name / "environment.json").write_text(json.dumps(environment, indent=2))
print("PASS: key completeness, metric bounds, saved-baseline reproduction, artifact and input hashes")
