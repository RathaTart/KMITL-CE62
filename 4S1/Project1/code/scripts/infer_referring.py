"""Run an arbitrary image + expression on cenara70hx; save mask and intermediate decisions.

Example (inside the P2 venv, HF_HOME set):
python scripts/infer_referring.py --image /absolute/image.jpg \
  --text 'person wearing a blue hat and a black jacket' \
  --method direct --out results/my_query
"""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--image", required=True, type=Path)
parser.add_argument("--text", required=True)
parser.add_argument("--method", choices=["direct", "crop", "context"], default="direct")
parser.add_argument("--out", required=True, type=Path)
a = parser.parse_args()
if platform.node().split(".")[0].lower() != "cenara70hx":
    parser.error("Project instructions require inference on cenara70hx through Tailscale.")
if not a.image.is_file() or not a.text.strip():
    parser.error("Provide an existing image and nonempty description.")
if a.out.exists():
    parser.error("Choose a fresh output directory to preserve existing evidence.")
scripts = Path(__file__).resolve().parent
a.out.mkdir(parents=True)
item = dict(key="query::expression", item_id="query", prompt_id="expression", image=str(a.image.resolve()), expression=a.text)
manifest = dict(status="Unscored user query; no ground truth", items=[item])
for variant in ["direct", "candidates", "verified"]:
    folder = a.out / variant
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (folder / "blip2_answers.jsonl").write_text(json.dumps(dict(key=item["key"], answer=a.text if variant == "direct" else "person"))+"\n")

def run(script, *args):
    subprocess.run([sys.executable, str(scripts / script), *map(str,args)], check=True)

if a.method == "direct":
    run("attribute_pilot.py", "direct", "--out", a.out)
    selected = a.out / "direct"
else:
    run("attribute_pilot.py", "candidates", "--out", a.out)
    if a.method == "crop":
        run("attribute_pilot.py", "verify", "--out", a.out)
        selected = a.out / "verified"
    else:
        run("context_selector.py", "--out", a.out)
        selected = a.out / "context"
run("run_blip2_grounded_sam.py", "--phase", "sam", "--out-dir", selected)
print(json.dumps(dict(mask=str((selected / "masks/query__expression.png").resolve()),
    decisions=str((selected / "grounding_boxes.jsonl").resolve()),
    status="Prediction only; inspect for attribute mismatches, missed targets and ambiguous multiple matches."), indent=2))
