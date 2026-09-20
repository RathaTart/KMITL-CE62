"""Exploratory full-scene candidate selection with cached Qwen2-VL-2B.

Run on cenara70hx after attribute_pilot candidates. No ground truth is read.
"""
import argparse
import json
import time
from pathlib import Path
import torch
from PIL import Image, ImageDraw, ImageFont
from torchvision.ops import nms
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from attribute_pilot import read, write, lines, jsonl

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, default=Path("results/attribute_pilot_20260914"))
a = parser.parse_args()
folder = a.out / "context"
manifest = read(a.out / "candidates/manifest.json")
write(folder / "manifest.json", manifest)
model_id = "Qwen/Qwen2-VL-2B-Instruct"
processor = AutoProcessor.from_pretrained(model_id, local_files_only=True, min_pixels=256*28*28, max_pixels=512*28*28)
model = Qwen2VLForConditionalGeneration.from_pretrained(model_id, local_files_only=True,
    torch_dtype=torch.float16, attn_implementation="sdpa").to("cuda").eval()
torch.manual_seed(20260914)
torch.cuda.reset_peak_memory_stats()
boxes = {r["key"]:r for r in lines(a.out / "candidates/grounding_boxes.jsonl")}
rows, audits = [], []
for item in manifest["items"]:
    row = boxes[item["key"]]
    keep = nms(torch.tensor(row["boxes"], dtype=torch.float32).reshape(-1,4), torch.tensor(row["scores"]), .5).tolist()[:12]
    image = Image.open(item["image"]).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(15, image.height//28))
    for label, index in enumerate(keep):
        box = row["boxes"][index]
        draw.rectangle(box, outline="red", width=2)
        x,y = max(0,box[0]), max(0,box[1])
        bounds = draw.textbbox((x,y), str(label), font=font)
        draw.rectangle(bounds, fill="white")
        draw.text((x,y), str(label), fill="black", font=font)
    marked = folder / (item["item_id"]+"_candidates.jpg")
    image.save(marked)
    prompt = (f'The red boxes label candidate people with IDs 0 to {len(keep)-1}. '
        f'Select the people matching this description: "{item["expression"]}". '
        'Every clothing attribute must belong to the same selected person. Use the full scene for spatial relations. '
        'Return only a JSON array of matching integer IDs, such as [0] or [0, 2]. If no person matches, return [].')
    messages = [{"role":"user", "content":[{"type":"image"}, {"type":"text", "text":prompt}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to("cuda")
    torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=48, do_sample=False)
    torch.cuda.synchronize()
    answer = processor.batch_decode(output[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip()
    valid = True
    try:
        selected = json.loads(answer)
        if not isinstance(selected, list) or any(type(x) is not int or x < 0 or x >= len(keep) for x in selected):
            raise ValueError("Invalid candidate IDs")
        selected = sorted(set(selected))
    except (ValueError, TypeError):
        selected, valid = [], False
    accepted = [keep[j] for j in selected]
    elapsed = time.perf_counter() - start
    rows.append(dict(row, boxes=[row["boxes"][j] for j in accepted], scores=[row["scores"][j] for j in accepted], labels=["context selected"]*len(accepted), verification_s=elapsed))
    audits.append(dict(key=item["key"], prompt=prompt, raw_answer=answer, valid_json=valid, candidate_indices=keep, selected_indices=accepted, latency_s=elapsed))
    print(item["key"], answer, flush=True)
jsonl(folder / "grounding_boxes.jsonl", rows)
jsonl(folder / "selection_audit.jsonl", audits)
write(folder / "selector_config.json", dict(model=model_id, precision="fp16", max_pixels=512*28*28, max_candidates=12, nms=.5,
    peak_vram_gib=torch.cuda.max_memory_allocated()/1024**3, gpu=torch.cuda.get_device_name(),
    caveat="Exploratory: model and context both changed; invalid JSON is recorded and scored as empty, not a confident no-match."))
