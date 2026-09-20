"""Build a static evidence browser from already-scored remote experiment artifacts."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "webapp/static"
ASSETS = STATIC / "attribute-assets"
ASSETS.mkdir(exist_ok=True)
NAMES = {"LISA_existing":"LISA-7B-v1 (saved)", "BLIP2_existing":"BLIP-2 original prompt (saved)", "direct":"Original expression → DINO → SAM",
    "verified":"Person boxes → BLIP-2 crop verification → SAM", "prompt_fixed":"BLIP-2 corrected prompt → DINO → SAM",
    "YOLO_expression_SAM":"Expression → YOLO-World → SAM", "context":"Person boxes → Qwen2-VL scene selection → SAM", "top1":"Highest-confidence person → SAM (no text selection)"}


def read(p): return json.loads(p.read_text(encoding="utf-8"))


def local(p):
    p = str(p).replace("/home/osta/lisa-eval/code/", "")
    return ROOT / p


def asset(p, name):
    target = ASSETS / name
    shutil.copy2(p, target)
    return "attribute-assets/"+name


sets = []
for dirname, title in [("attribute_pilot_20260914", "30-expression development pilot"), ("attribute_custom_20260914", "Three prompts on one inspected image")]:
    folder = ROOT / "results" / dirname
    if not (folder / "comparison.json").exists(): continue
    summary = read(folder / "comparison.json")
    manifest = read(folder / "direct/manifest.json")
    records = [json.loads(l) for l in (folder / "per_expression.jsonl").read_text().splitlines() if l]
    items = []
    for item in manifest["items"]:
        itemid = item["item_id"]
        entry = dict(key=item["key"], expression=item["expression"], case_type=item["case_type"],
            image=asset(local(item["image"]), dirname+"_"+itemid+".jpg"),
            gt=asset(local(item["ground_truth"]), dirname+"_"+itemid+"_gt.png"), predictions={})
        for variant in summary:
            if variant == "LISA_existing": maskfolder = ROOT / "results/grefcoco_pilot_p1_p2/p1_masks"
            elif variant == "BLIP2_existing": maskfolder = ROOT / "results/grefcoco_pilot_p1_p2/masks"
            elif variant == "YOLO_expression_SAM": maskfolder = folder / "yolo/p3_expression/masks"
            else: maskfolder = folder / variant / "masks"
            mask = maskfolder / f'{itemid}__{item["prompt_id"]}.png'
            row = next(r for r in records if r["key"] == item["key"] and r["variant"] == variant)
            entry["predictions"][variant] = dict(src=asset(mask, dirname+"_"+itemid+"_"+variant+".png"), iou=row["iou"], pixels=row["predicted_pixels"])
        items.append(entry)
    sets.append(dict(title=title, summary=summary, items=items,
        data=asset(folder / "comparison.json", dirname+"_comparison.json"),
        protocol=asset(folder / "protocol.json", dirname+"_protocol.json"),
        resources=asset(folder / "resources.json", dirname+"_resources.json"),
        environment=asset(folder / "environment.json", dirname+"_environment.json")))

asset(ROOT.parent / "docs/attribute-research-20260914.md", "research-notes.md")

html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Detailed person descriptions · KMITL CE69-27</title>
<style>
:root{color-scheme:light;--ink:#152d37;--muted:#52656b;--teal:#006d70;--line:#d4dedb}*{box-sizing:border-box}body{margin:0;background:#f5f6f0;color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:36px 24px 70px}a{color:var(--teal)}header{padding:28px 0;border-bottom:2px solid var(--ink)}.eyebrow{letter-spacing:.14em;text-transform:uppercase;font-size:12px;font-weight:750;color:var(--teal)}h1{font:600 clamp(30px,5vw,52px)/1.1 Georgia,serif;max-width:850px;margin:16px 0}h2{font:600 27px/1.3 Georgia,serif;margin-top:36px}p{max-width:930px}.status{background:#fff1d4;border-left:4px solid #a56b09;padding:16px 20px;margin:24px 0}.muted,small{color:var(--muted)}.flow{border:1px solid var(--line);background:white;padding:20px;border-radius:8px}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}label{display:flex;flex-direction:column;gap:6px;flex:1;min-width:210px;font-size:13px;font-weight:650}select{font:inherit;padding:10px;border:1px solid #94aaa9;border-radius:5px;background:white;color:var(--ink);width:100%}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;background:white;font-size:14px}th,td{text-align:right;padding:13px 12px;border-bottom:1px solid var(--line);white-space:nowrap}th:first-child,td:first-child{text-align:left;white-space:normal;min-width:220px}th{background:#e6eeea;font-size:12px}.views{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:0;background:#e6eeea;padding:10px;border-radius:6px}figure img{width:100%;height:340px;object-fit:contain;background:#192326;display:block}figcaption{font-size:13px;margin-bottom:8px}.prompt{font-size:21px;font-weight:600}details{padding:14px 0;border-bottom:1px solid var(--line)}summary{cursor:pointer;font-weight:650}footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);font-size:13px}@media(max-width:700px){.views{grid-template-columns:1fr}figure img{height:300px}main{padding:18px 16px}td,th{padding:10px}}
</style><main><a href="index.html">← Project results</a><header><div class="eyebrow">KMITL · CE69-27 · Research notebook · 14 September 2026</div><h1>Detailed descriptions and person masks</h1><p>Can clothing attributes identify the right person in a crowded image? Compare executed experiments, inspect every prediction, and separate successful masks from correct rejection.</p></header>
<div class="status"><strong>Development evidence. No superiority or novelty claim.</strong><br>The 30-expression set was already used in earlier experiments and mixes original dataset splits. The custom set repeats one image with three prompts. Neither is an untouched final test.</div>
<h2>What is being tested</h2><div class="flow">Image + full description → candidate person boxes → optional language-based selection → SAM mask</div>
<p>The original BLIP-2 prompt often answered “no person” for positive examples, preventing detection. The corrected-prompt experiment removes that clause. Direct grounding bypasses rewriting. Crop verification and full-scene selection test whether a separate selection step helps.</p>
<div class="controls"><label>Evaluation set<select id="dataset"></select></label></div>
<h2>Measured mask results</h2><p class="muted">Mean IoU in percent. Positive cases exclude empty targets. No-match accuracy requires a valid response and an empty prediction on a no-target case. Invalid selector responses receive zero request IoU, including on no-target cases. These are mask metrics, not strict instance-identification accuracy. The pilot has 10 single-target, 15 multi-target and 5 no-target requests; the custom set has two positive and one no-target request on one image.</p><div class="tablewrap"><table><thead><tr><th>System</th><th>All</th><th>Positive</th><th>Single in crowd</th><th>Multi-target</th><th>No-match accuracy</th></tr></thead><tbody id="scores"></tbody></table></div><p id="downloads"></p>
<h2>Inspect the evidence</h2><div class="controls"><label>Expression<select id="expression"></select></label><label>System<select id="system"></select></label></div><p class="prompt" id="prompt"></p><p id="details"></p><div class="views"><figure><figcaption>Input image</figcaption><img id="input" alt="Input scene"></figure><figure><figcaption>Target mask · white = target</figcaption><img id="gt" alt="Ground truth mask"></figure><figure><figcaption>Predicted mask · white = selected pixels</figcaption><img id="pred" alt="Predicted mask"></figure></div>
<h2>Interpretation and next hypothesis</h2><p>A detector can return a plausible person box without satisfying all requested attributes. Crop verification loses spatial context and overlapping people can confuse attribute ownership. Full-scene selection also changes the language model, so its results do not isolate context alone.</p>
<p>The next defensible hypothesis is to check individual clothing attributes on the same candidate while retaining full-scene information for relationships, then calibrate rejection on separate negative examples. This still needs a controlled ablation and held-out evaluation.</p>
<details><summary>Baseline comparability</summary><p>LISA is an image-language segmentation model. YOLO-World supplies boxes and is paired with the same SAM here. ZoomNeXt is a camouflaged-object model with no native text input; its report results use different metrics, splits and hardware. A direct clothing-description ranking against unmodified ZoomNeXt would be misleading.</p></details>
<details><summary>Resources and reproducibility</summary><p>New inference and evaluation ran serially on cenara70hx, NVIDIA CMP 70HX, through Tailscale. Model loading is excluded from the original per-model timings. Stage logs and configuration files record available timing and memory; no fair end-to-end latency ranking is claimed. Saved LISA and original BLIP-2 masks are reused historical controls.</p><p>Script: code/scripts/attribute_pilot.py. Research record: docs/attribute-research-20260914.md. Invalid selector JSON is logged separately, becomes an empty prediction, and receives zero request IoU. It receives no credit for no-match accuracy.</p></details>
<details><summary>Primary sources and novelty</summary><p>See <a href="https://github.com/JIA-Lab-research/LISA">LISA</a>, <a href="https://github.com/lartpang/ZoomNeXt">ZoomNeXt</a>, <a href="https://github.com/AILab-CVC/YOLO-World">YOLO-World</a>, <a href="https://github.com/IDEA-Research/RexSeek">RexSeek / HumanRef</a>, and <a href="https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct">Qwen2-VL-2B</a>. See also <a href="https://github.com/microsoft/SoM">Set-of-Mark prompting</a> for numbered visual marks. Human referring and grounding-plus-SAM pipelines already exist. The proposed combination is not established as novel.</p></details>
<footer>Every displayed metric comes from a saved remote evaluation artifact. Valid empty-empty IoU is 100%; invalid selector responses score zero. Inspect positive and no-target results separately.</footer></main>
<script>const SETS=__DATA__, NAMES=__NAMES__;
const $=id=>document.getElementById(id),pct=x=>x==null?'—':(100*x).toFixed(1);
SETS.forEach((s,i)=>$('dataset').add(new Option(s.title,i)));
function refresh(){const s=SETS[$('dataset').value];$('scores').replaceChildren();for(const [k,v] of Object.entries(s.summary)){const tr=document.createElement('tr');[NAMES[k]||k,pct(v.all?.mean_iou),pct(v.positive?.mean_iou),pct(v.single_in_crowd?.mean_iou),pct(v.multi_target?.mean_iou),pct(v.no_target?.no_match_accuracy)].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td)});$('scores').append(tr)}$('expression').replaceChildren();s.items.forEach((r,i)=>$('expression').add(new Option(r.expression,i)));$('system').replaceChildren();Object.keys(s.summary).forEach(k=>$('system').add(new Option(NAMES[k]||k,k)));$('downloads').replaceChildren();for(const [label,url] of [['Download measured results',s.data],['Download protocol',s.protocol],['Resources',s.resources],['Environment',s.environment],['Research record','attribute-assets/research-notes.md']]){const a=document.createElement('a');a.href=url;a.textContent=label;a.style.marginRight='20px';$('downloads').append(a)}show()}
function show(){const s=SETS[$('dataset').value],r=s.items[$('expression').value],p=r.predictions[$('system').value];$('prompt').textContent='“'+r.expression+'”';$('details').textContent=r.case_type+' · IoU '+pct(p.iou)+'% · Predicted pixels '+p.pixels.toLocaleString();$('input').src=r.image;$('gt').src=r.gt;$('pred').src=p.src}
$('dataset').addEventListener('change',refresh);$('expression').addEventListener('change',show);$('system').addEventListener('change',show);refresh();
</script></html>'''
html = html.replace('__DATA__', json.dumps(sets).replace('</', '<\\/')).replace('__NAMES__', json.dumps(NAMES))
html = html.replace('<h2>What is being tested</h2>', '<p><a href="model-upgrade.html">New experiment: trained boundary layer and reserved-image evaluation →</a></p><h2>What is being tested</h2>')
html = html.replace('<h2>What is being tested</h2>', '<p><a href="training-free.html">Latest: training-free methods on 60 new images and CCTV research →</a></p><h2>What is being tested</h2>')
(STATIC / "attribute-research.html").write_text(html, encoding="utf-8")
print(STATIC / "attribute-research.html")
