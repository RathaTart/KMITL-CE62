# Session handoff — LISA track

**Read this first if you are a new session, a new AI, or a human picking the work
back up.** It is the operational companion to
[research-and-roadmap.md](research-and-roadmap.md): that file holds *findings*,
this one holds *how to run things and what state they are in*.

Last updated: **2026-08-24**.

New comparison: the complete remote BLIP-2/Q-Former -> Grounding DINO -> SAM
experiment and its website-ready artifacts are documented in
[blip2-vs-lisa-experiment.md](blip2-vs-lisa-experiment.md).

Website/report naming from 2026-08-24 onward: **P1 = LISA** and
**P2 = BLIP-2/Q-Former -> Grounding DINO -> SAM**.

---

## 1. State right now

Both machines are provisioned and were running the two evaluations at the end of
this session.

### Laptop (`LAPTOP-C3KE8MJ2`, RTX 3060 6 GB)

| Component | State |
| --- | --- |
| `code/.venv311` (Python 3.11.14) | ✅ complete, torch 2.4.1+cu121, CUDA live |
| LISA-7B-v1 checkpoint | ✅ 16121313367 bytes, **sha256 verified on both shards** |
| CLIP ViT-L/14 | ✅ complete (1.71 GB) |
| ReasonSeg val | ✅ 200 images |
| CamouflageData | ✅ 1000 img + 1000 gt |
| torch/torchvision cu121 **cp311** wheels | ✅ `code/wheels/` |
| Smoke test (5 README examples) | ✅ **5/5 emit masks**, verified correct on 2 inspected |

### Remote (`cenara70hx`, CMP 70HX 8 GB)

| Component | State |
| --- | --- |
| NVIDIA driver | ✅ installed this session (was broken — §4) |
| `~/lisa-eval/code/.venv` (Python 3.11.16) | ✅ torch 2.4.1+cu121, CUDA live |
| LISA-7B-v1 | ✅ 16121313367 bytes — **byte-identical to the laptop** |
| CLIP, ReasonSeg val, CamouflageData | ✅ all present |
| fp16 tensor cores + bitsandbytes NF4 | ✅ verified working on the mining card |

### Dead weight that can be deleted

- `code/.venv` — Python 3.12, cannot run this stack at all (§2.1)
- `code/wheels/torch-2.4.1+cu121-cp312-*.whl` — 2.44 GB, wrong Python version

---

## 0. Results (measured 2026-08-22)

Artifacts live in `code/results/<task>/`: `summary.json`, `per_image.csv`,
`per_image.jsonl`, `masks/`, `vis/`. All reproducible at `--seed 0`.

### CamouflageData — the headline result (180 inferences, 60 images × 3 prompts)

| prompt | gIoU | cIoU | Dice | Prec | Rec | IoU≥0.5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **overall** | **59.51** | **60.56** | 67.85 | 72.90 | 68.83 | 65.0 % |
| p1_referring "segment the person" | 52.43 | 53.79 | 60.16 | 72.33 | 58.72 | 55.0 % |
| **p2_explicit** "the camouflaged soldier hiding" | **65.01** | **68.62** | 72.98 | 75.42 | 72.84 | **75.0 %** |
| p3_reasoning "who is hiding… blends into background" | 61.09 | 59.36 | 70.41 | 70.93 | 74.95 | 65.0 % |

`[SEG]` emit rate 100 %. Peak VRAM 6.91 GB on the CMP 70HX, 46.8 s/inference,
2 h 20 m wall.

**Context that matters:** LISA's *published* score on its *own* benchmark is
gIoU 44.4. Camouflaged soldiers score ~15 points above that, zero-shot. But
~19 % of cases fail almost completely (IoU < 0.05) and that floor barely moves
with phrasing — report it separately, never let the mean hide it.

### ReasonSeg val — pipeline check only (200 images)

gIoU **87.81**, cIoU **93.86**, Dice 91.82, precision 94.03, recall 92.38,
IoU≥0.5 96.0 %, emit rate 100 %. Peak VRAM 5.30 GB, 33.2 s/image, 1 h 51 m.

⚠️ **Roughly double the paper's 44.4 / 46.0 because the `v1` checkpoint was
trained on ReasonSeg train+val.** Evidence the harness is correct; *never*
presentable as reproducing LISA. See §6.

### Drone stills — qualitative only (9 inferences, no ground truth)

9/9 emitted masks, 35.0 s each. Mask area as % of frame:

| still | plain | explicit | reasoning |
| --- | ---: | ---: | ---: |
| hidden car | 11.42 | 1.45 | 1.37 |
| hidden car far (1) | 0.14 | 0.46 | 0.57 |
| hidden car far (2) | 0.11 | 0.10 | 0.08 |

No GT exists, so **no IoU** — do not invent one. On `hidden car` the plain prompt
covers 8× the explicit prompt's area (almost certainly foliage). The two "far"
stills give sub-0.15 % masks that could be tiny correct detections or misses;
without GT it is unknowable. Annotating ~20 frames would fix that. The 5 videos
in `dataset/drone/` and 22 in `dataset/test data/` are untouched — the harness
reads only `.png`.

### The three findings worth writing up

1. **Prompt phrasing is worth +12.6 gIoU** (52.4 → 65.0) and +20 pts of usable
   masks (55 → 75 %), for four extra words. It pays most where the task is
   hardest: **+16.1** on the 5 hardest patterns vs **+3.4** on the 5 easiest.
   The *reasoning* phrasing (61.1) lands **below** the plain explicit one (65.0)
   — a notable negative result for a model sold on reasoning segmentation.

2. **A 3× spread across patterns that nothing measured predicts.** German Snow
   Camouflage 30.4 → Czech VZ 95 90.2. Spearman ρ against difficulty:
   contrast **+0.162**, target area **+0.361**, bbox side **+0.383**, GT
   fragmentation **−0.088**. British DPM has the 2nd-highest contrast and is the
   2nd-hardest pattern. So difficulty is *not* "the uniform blends in", and is
   only weakly about target size — which undercuts tiling/upscaling as the
   obvious first fix. Regenerate with `scripts/analyze_patterns.py`.

3. **Prediction fragmentation is a free failure signal.** Mean IoU by number of
   connected components in the *prediction*: 1 blob → **79.26** (n=85), 2–3 →
   68.00, 4–9 → 43.19, 10+ → **25.98** (n=41). Monotonic, and computable at
   inference time with **no ground truth**, so the model can flag its own likely
   failures. Note the distinction: *ground-truth* fragmentation predicts nothing
   (ρ −0.088); it is *prediction* fragmentation that carries the signal.
   Acting on it is a trade-off, not a free win — keeping only the largest
   component moves IoU≥0.5 **65.0 → 69.4 %** and cIoU **60.6 → 61.8**, but gIoU
   **59.5 → 59.2** and Dice **67.9 → 66.3**. Regenerate with
   `scripts/postprocess_experiment.py`.

### Why both metrics must always be reported

On ReasonSeg cIoU (93.9) **>** gIoU (87.8) — targets are large (median 6.3 % of
frame) and large objects are easier, so they dominate the pooled metric. On
CamouflageData (~1 % targets) the two converge (59.5 vs 60.6). The *ordering of
the metrics changes with the dataset*, which is the strongest possible argument
for never quoting one alone.

### Published summary

A results page with all tables, the per-pattern ranking, and the best / typical /
failure overlays: https://claude.ai/code/artifact/a61b23ba-e220-45c5-abed-c98e6c3fa1ac

---

## 0.1 The local website

A bilingual (English / ไทย) site for browsing every result and running the model
on new images. The site itself is local. P1 inference stays on this PC; when P2
is selected, the uploaded image is sent over Tailscale to `cenara70hx`, processed
there, returned to the page, and removed from the remote temporary job folder.

```powershell
.\start-website.ps1          # or: & $py code\webapp\server.py
```

Then <http://127.0.0.1:5000>. It binds **127.0.0.1 only**, so it is not reachable
from other machines on the network.

| Tab | What it does |
| --- | --- |
| **Results** | The full report — headline stats, prompt comparison, the 20-pattern ranking, correlations, the fragmentation finding, ReasonSeg calibration, drone table |
| **P1 vs P2 pipeline** | Walks through real saved P2 outputs: original image → BLIP-2/Q-Former phrase → Grounding DINO boxes → SAM mask, followed by the paired P1 overlay and scores. Includes all 180 cases and best/worst shortcuts |
| **Browse** | Shared final-output archive: P1 + P2 on CamouflageData (360 rows), plus P1-only ReasonSeg and drone results. Filter by system / dataset / pattern / prompt, sort by IoU, and inspect overlays with previous/next navigation. |
| **Try an image** | Drag-and-drop a photo, choose P1/LISA or P2/BLIP-2 -> DINO -> SAM, pick a studied prompt or write your own, and get the mask plus model diagnostics back |

Design decisions worth knowing before changing it:

- **Every number is fetched from `/api/analysis`**, which reads
  `code/results/*/summary.json` and `per_image.csv` at server start. Nothing is
  hard-coded in the JavaScript, so the page cannot drift from what was measured.
  Re-run an evaluation, restart the server, and the site updates itself.
- **Overlays are rendered per request** from the saved masks
  (`/api/overlay?task=&item=&prompt=&kind=`), not pre-generated. ~50 ms each,
  versus thousands of JPEGs on disk. Images are capped at 1400 px on the long
  edge because some ReasonSeg frames are 28 MP.
- **P1 loads lazily**, on the first P1 inference only, and then stays resident.
  Browsing results never pays the model-load cost.
- **P2 live inference runs remotely and serially.** The page uploads the resized
  image and a generated manifest over Tailscale, runs BLIP-2, Grounding DINO,
  and SAM as three separate processes, downloads the mask and diagnostics, then
  deletes that exact remote temporary job directory. The result card shows both
  component compute time and the complete wait including load/swap/transfer.
- **One inference job at a time**, enforced by a lock. Extra requests queue
  rather than overlapping GPU-heavy work.
- **Uploads are downscaled to 1600 px.** A 40 MP phone photo would otherwise
  spend minutes in the CPU-side SAM encoder for no accuracy gain.
- **Thai has its own faces** (Noto Sans/Serif Thai). Source Serif 4 has no Thai
  glyphs, so without that the Thai text falls back silently and looks broken.
  Strings live in `code/webapp/static/i18n.js`; numbers are never translated,
  only labels.

`flask` is the one dependency beyond `requirements-inference.txt`;
`start-website.ps1` installs it on first run.

---

## Bugs found and fixed this session

All four were silent: nothing crashed, and three of them produced
plausible-looking output that was wrong.

| # | Bug | Symptom | Fix |
| --- | --- | --- | --- |
| 1 | fp16 overflow → NaN in the SAM mask decoder | `[SEG]` emitted, coherent prose, **mask empty**. 3 of 5 results silently voided | prompt encoder + mask decoder in fp32 (§6.1) |
| 2 | `"cpu"` in `device_map` makes accelerate *offload* | `Cannot copy out of meta tensor` | load `device_map={"": 0}`, move afterwards |
| 3 | accelerate `AlignDevicesHook` left on a hand-placed module | `Input type (torch.cuda.FloatTensor) and weight type (torch.FloatTensor)` | `remove_hook_from_module(..., recurse=True)` |
| 4 | `robust_download.py` assumed `Content-Length` | `KeyError: 'content-length'` on HF's small non-LFS files | fall back to a single plain GET |

Plus two environment traps that cost real time: Python 3.12 cannot run this stack
(§2.1) and the resolver silently installs CPU-only torch (§2.2).

### Verified, not assumed

- **CPU vs GPU SAM encoder**: cosine similarity **0.99999**, relative mean
  difference 0.13% — pure fp16 rounding. `--sam_encoder_device cpu` does not
  change results, so its numbers are comparable with GPU ones.
- **`metrics.py`**: 17 checks against hand-computed gIoU / cIoU / ignore-region
  values, including the degenerate empty-mask cases.
- **Loaders**: 22 checks on real data. `--limit 60` gives exactly 3 images from
  each of the 20 patterns, seed-deterministic, median target area 0.98 %
  (dataset-wide median is 0.997 %).
- **Ablation — quantising the `[SEG]` projection**: `text_hidden_fcs` is NF4 by
  default upstream. Keeping it in fp16 costs 25.5 MB and changed mask area by
  **less than 0.2 % on all 5 smoke images**. A clean negative result: NF4 there
  is harmless, and bug #1 was the whole story. Flag: `--quantize_seg_projection`.

---

---

## 2. Commands

```powershell
$py = "code\.venv311\Scripts\python.exe"

# --- setup (idempotent, safe to re-run) -----------------------------------
uv python install 3.11
uv venv --python 3.11 code\.venv311
& $py -m pip install --find-links code\wheels -r code\requirements-inference.txt
& $py code\scripts\robust_download.py --manifest lisa    # 16.12 GB, sha256-verified
& $py code\scripts\robust_download.py --manifest clip    # 1.71 GB vision tower
& $py code\scripts\robust_download.py --manifest wheels  # torch cu121

# --- validate before trusting any number ---------------------------------
& $py code\scripts\smoke_test.py

# --- aggregate a run that is still going, or was interrupted --------------
# run_eval.py writes summary.json only at the end; this reads the incremental
# per_image.jsonl instead, so a 3-hour sweep can be reported on at any point.
& $py code\scripts\summarize.py camouflage --expected 180
& $py code\scripts\summarize.py reasonseg  --expected 200

# --- the runs ------------------------------------------------------------
& $py code\scripts\run_eval.py --task camouflage --limit 60   # 3/pattern x 3 prompts = 180
& $py code\scripts\run_eval.py --task reasonseg  --limit 200  # paper benchmark
& $py code\scripts\run_eval.py --task drone                   # qualitative, no GT
```

Flags that matter: `--quantization {none,8bit,4bit}`,
`--sam_encoder_device {cuda,cpu}`, `--limit`, `--seed`, `--save_vis`,
`--max_new_tokens`.

**Do not use the system Python.** It has a CPU-only torch. `LisaEngine.__init__`
raises on `torch.cuda.is_available() == False` specifically to catch this.

### 2.1 Python 3.11 is mandatory — 3.12 cannot run this stack

This cost real time this session, so it is worth stating flatly.

`transformers==4.31.0` requires `tokenizers<0.14`. **tokenizers never published a
cp312 wheel below 0.14** — 0.15.2 is the first. And 0.13.3 cannot be compiled from
source on 3.12 either: it pins PyO3 0.18, and PyO3 only gained 3.12 support in
0.20.

On 3.12 the install dies with `Failed building wheel for tokenizers` and a
suggestion to install a Rust toolchain. **That suggestion is a dead end** —
installing Rust does not make it compile. Do not spend time on it.

transformers cannot simply be bumped instead: `code/LISA/model/llava/` is a
vendored July-2023 LLaVA snapshot that breaks on newer APIs.

```powershell
uv python install 3.11              # ~25 MB, uv is already on PATH
uv venv --python 3.11 code\.venv311
```

The old `code/.venv` is Python 3.12 and is **unusable for inference**. It is left
in place only because a download was running out of it; it can be deleted.
`code/wheels/torch-2.4.1+cu121-cp312-*.whl` (2.44 GB) is likewise dead weight.

### 2.2 The CPU-torch trap

Several packages here (bitsandbytes among them) declare a bare `torch`
dependency. The resolver happily satisfies it from PyPI — which on Windows means
a **CPU-only** build that silently replaces the CUDA one. Installing the
requirements file without `--find-links code\wheels` produced `torch 2.13.0+cpu`
this session.

Always verify after any install that touches torch:

```powershell
& $py -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# want: 2.4.1+cu121 True     NOT: ...+cpu False
```

A `+cpu` suffix is the first thing to check whenever CUDA "disappears".

### 2.3 How `--limit` interacts with sampling

`--limit 60` on `camouflage` means **60 images**, stratified as `60 // 20 = 3`
per camouflage pattern, each run under all 3 prompt phrasings → **180
inferences**. The item count printed by `run_eval.py` is inferences, not images.
Sampling is seeded (`--seed 0`), so the same 60 images come back every time.

---

## 3. Downloads: the recurring problem

This link establishes TCP fine to every host but stalls mid-transfer. `pip` and
`huggingface_hub` both stream a whole file over one connection, so a stall at
9 GB of a 10 GB file throws the whole thing away.

**Always use `code/scripts/robust_download.py`.** It fetches 8–16 MB windows via
`Range:` headers and appends, so the destination is always a valid byte-prefix
and a stall costs one chunk. Re-running resumes exactly where it stopped and
verifies sha256 at the end.

Two environment facts that have cost time before:

- **Background tasks cannot reach the HF LFS CDN or PyPI's file host.** They
  stall silently at 0 bytes. Long downloads must run with the sandbox disabled.
- **PyPI has no CUDA build of torch for Windows.** Its wheel is 190 MB and
  CPU-only. `download.pytorch.org/whl/cu121` is the only source, which is why
  `code/wheels/` is kept.

Progress is best watched by file size, not by the log — the downloader's output
is pipe-buffered and only flushes at exit:

```powershell
ls code\weights\LISA-7B-v1\*.bin, code\weights\clip-vit-large-patch14\*.bin
```

---

## 4. Remote compute — `cenara70hx` over Tailscale

All measured this session, on the box itself.

| Property | Value |
| --- | --- |
| Login | `osta@100.69.21.71` (key `~/.ssh/lisa_cenara70hx`) |
| Tailnet name | `cenara70hx.tail452750.ts.net` |
| Ownership | **shared into** this tailnet by another user — not ours to administer |
| Path | DERP relay `sin`, ~83 ms RTT — relayed, not a direct connection |
| OS | Ubuntu 24.04.3 LTS, kernel 6.8.0-138 |
| CPU | Intel i7-8700K, 6 cores / 12 threads |
| RAM | **31 GB** (~30 GB free) |
| Disk | 419 GB free |
| GPU | **NVIDIA CMP 70HX, 8192 MiB**, compute capability 8.6 (GA104, Ampere) |
| Driver | 580.173.02, CUDA 13.0 |
| PCIe | **Gen 1 ×4** (~1 GB/s) — downgraded from the x16 slot by design |
| Python | 3.12.3 only; `uv` installs a private 3.11 (§2.1) |
| `sudo` | `osta` is in the `sudo` group, password required |

Against the laptop this is **+2 GB VRAM and +16 GB RAM**, at the cost of a weaker
CPU. The VRAM matters most: 8 GB is enough to keep the SAM ViT-H encoder on the
GPU, which removes the slowest part of the local configuration.

### The GPU is a mining card — what that does and does not cost

A CMP (Cryptocurrency Mining Processor) 70HX is a GA104 with the display engine
fused off and the PCIe link locked to **Gen 1 ×4**. Two consequences:

- **Compute is fine.** Compute capability 8.6 means Ampere tensor cores, fp16,
  and bitsandbytes NF4 all work normally. It is a real Ampere GPU for our
  purposes.
- **Host↔device bandwidth is ~1 GB/s**, roughly a tenth of a Gen 3 ×16 desktop
  card. This is almost irrelevant here: weights are uploaded once at load, and
  the only per-image traffic is the `[1,256,64,64]` SAM feature map (4 MB) and
  it only crosses at all under `--sam_encoder_device cpu`. Do **not** cite PCIe
  as a reason for any latency figure without measuring it.

Worth stating plainly in the report: this is a mining card, not a datacenter
accelerator, and its 8 GB still forces 4-bit quantisation of the LLM.

### Getting the GPU working (it was broken)

`nvidia-smi` failed on arrival. The cause was **not** a missing GPU but a
half-installed driver: `nvidia-utils-525/535/580` and `nvidia-kernel-common-580`
were present, yet no `nvidia-dkms`/`nvidia-driver` package, no `dkms` binary, and
no `nvidia.ko` anywhere under `/lib/modules`. Only userspace had been installed.

Secure Boot is disabled, so unsigned module loading is not an obstacle.

```bash
sudo apt-get update
sudo apt-get install -y nvidia-headless-580 nvidia-utils-580   # pulls dkms, builds the module
sudo modprobe nvidia
sudo nvidia-smi          # as root, once: this is what creates /dev/nvidia*
```

The last step matters. Loading the module alone gives no `/dev/nvidia*` nodes,
and `nvidia-smi` keeps failing until something creates them. Normally the setuid
`nvidia-modprobe` does it on demand, **but that binary is not installed here**,
so running `nvidia-smi` once as root is what brings the device nodes up. They end
up world-accessible (`crw-rw-rw-`), so `osta` then works unprivileged.

⚠️ **This does not survive a reboot.** The modules and device nodes would have to
be recreated. Making it persistent (a `/etc/modules-load.d/nvidia.conf`, the
`nvidia-modprobe` package, or enabling `nvidia-persistenced`) is a further system
change to a machine we do not own — ask the owner before doing it.

### Layout on the remote

```
~/lisa-eval/
  code/scripts/          <- pushed from the laptop
  code/requirements-inference.txt
  code/.venv/            <- python 3.11 via uv
  code/LISA/             <- cloned from GitHub by the remote
  code/weights/          <- downloaded by the remote
  code/data/reason_seg/  <- downloaded by the remote
  dataset/Military Personnel Dataset dataset/CamouflageData/
```

`code/scripts/setup_remote.sh` does all of this and is idempotent. Only two
things need to cross the tunnel — `code/scripts/` (188 KB) and CamouflageData
(123 MB); everything else the remote fetches from its own origin, which is the
entire reason for moving the work there.

Use `tar` piped over `ssh`, not `scp -r`, for the dataset. It is 2000 small
files and SFTP pays a round trip per file at 83 ms RTT.

```powershell
$K = "$HOME\.ssh\lisa_cenara70hx"
ssh -i $K osta@100.69.21.71 'mkdir -p ~/lisa-eval/code ~/lisa-eval/dataset'
tar -cf - -C code scripts requirements-inference.txt |
    ssh -i $K osta@100.69.21.71 'tar -xf - -C ~/lisa-eval/code'
cd dataset
tar -cf - "Military Personnel Dataset dataset/CamouflageData" |
    ssh -i $K osta@100.69.21.71 'tar -xf - -C ~/lisa-eval/dataset'
ssh -i $K osta@100.69.21.71 'bash ~/lisa-eval/code/scripts/setup_remote.sh'
```

With 8 GB, prefer `--sam_encoder_device cuda` there. Pull results back with:

```powershell
scp -i $K -r osta@100.69.21.71:~/lisa-eval/code/results/* code\results\
```

**Credentials are not recorded in this repository and must not be.** The sudo
password was shared over chat once and should be rotated (`passwd`).

---

## 5. Why the local machine needs the workarounds

The dev laptop is an **RTX 3060 Laptop, 6 GB VRAM**, Ryzen 7 5800H (8C/16T),
**15.4 GB RAM** (frequently only ~2 GB free), 20 GB pagefile. Upstream LISA
assumes ≥ 9 GB VRAM even at 4-bit.

| Component | Placement | ~Size |
| --- | --- | --- |
| LLaVA-7B LLM | GPU, NF4 double-quant | 3.6 GB |
| CLIP ViT-L/14 | GPU, fp16 | 0.6 GB |
| SAM ViT-H **image encoder** | CPU fp32 (default) or GPU fp16 | 1.3 GB + activations |
| SAM prompt encoder / mask decoder | GPU fp16 | negligible |

Three deliberate choices, none of which should be "cleaned up":

1. **`sam_encoder_device="cpu"`** patches `get_visual_embs` so the ViT-H runs on
   CPU and only the `[1,256,64,64]` feature map returns to the GPU. The encoder
   is **frozen** in LISA, so this trades wall-clock for VRAM **without changing
   outputs**.
2. **`visual_model` stays in `llm_int8_skip_modules`.** Quantising a ViT-H that
   never saw quantisation in training visibly degrades mask edges.
3. **`enable_mmap_checkpoint_loading()`** makes transformers 4.31 mmap the `.bin`
   shards. Without it the ~10 GB first shard is materialised in RAM before any
   tensor reaches the GPU, which pages catastrophically on 15 GB.

RAM is tight enough that `run_eval.py` resolves ground truth **lazily**, in the
scoring loop, via `resolve_gt(item, image)`. Items carry a `gt_spec` tuple
(`("reasonseg", json)` / `("binary_png", png)` / `None`), never a materialised
array — 200 ReasonSeg images at up to 28 MP would otherwise pin > 1 GB of masks
for no reason. **Keep it lazy.**

---

## 6. Reading the results honestly

Artifacts land in `code/results/<task>/`: `per_image.csv`, `summary.json`,
`masks/`, `vis/`. `make_report.py` regenerates the report tables from them.

Four things that must travel with any number:

- **`seg_emit_rate` belongs next to every gIoU.** LISA can answer in prose and
  emit no `[SEG]` token at all; `run_eval.py` records `emitted_seg` and scores
  that case as IoU 0. A high gIoU with a low emit rate is not a good result.
- **Report gIoU *and* cIoU.** `gIoU` = mean per-image IoU, `cIoU` =
  Σintersection / Σunion. On CamouflageData the targets are ~1 % of the frame
  (median 0.997 %), so the two diverge sharply and either alone is misleading.
- **ReasonSeg val with `LISA-7B-v1` is contaminated.** Upstream states the `v1`
  checkpoints were trained on ReasonSeg **train+val**. The paper's val row
  (LISA-7B gIoU 44.4 / cIoU 46.0) corresponds to `v0`. Numbers produced here are
  a *sanity check that the pipeline is correct*, not a clean reproduction — say
  so explicitly wherever they appear.
- **Latency scales badly with `--max_new_tokens`.** `LisaModel` forces
  `config.use_cache = False`, so generation re-runs the full sequence every step.
  Keep the budget small unless the prose explanation is itself the object of
  study.

CamouflageData has no natural-language instructions of its own; the three
phrasings are authored by us and live in `CAMO_PROMPTS` in `run_eval.py`. Record
them verbatim in the report — the prompt-sensitivity comparison is a genuine
contribution and costs nothing extra.

### 6.1 The fp16 NaN trap — read this before trusting any "empty mask"

Found and fixed this session. It is the single most important thing in this file,
because it silently voided **3 of 5** results while looking exactly like honest
model failure.

**Symptom.** `emitted_seg` is True, the model's prose is perfectly coherent
("Sure, the segmentation result is [SEG]."), and the mask has **zero** pixels.
Scored naively that is IoU 0 — indistinguishable from the model genuinely not
finding the target.

**Cause.** `text_hidden_fcs` projects the `[SEG]` hidden state to the 256-d SAM
prompt embedding. Measured norms are large:

| image | ‖pred_embedding‖ | value range | `low_res_masks` |
| --- | ---: | --- | --- |
| obama.jpg | 148.2 | −23.6 … +30.4 | finite |
| example1.jpg | 252.5 | −47.6 … +39.4 | **all NaN** |

The SAM two-way transformer decoder was running in **fp16**. A 256-dim dot
product at that scale reaches ~4×10⁵, past fp16's 65504 ceiling → `inf` → `NaN`
through the softmax. `pred_mask > 0` is then False everywhere.

This is **not** specific to this harness. Upstream's own 4-bit path loads with
`torch_dtype=torch.half`, so it carries the same exposure. The checkpoint's
`config.json` declares `torch_dtype: bfloat16`, and bf16 has fp32's exponent
range — which is why the released model does not hit this at its intended
precision. Anyone reproducing LISA at fp16 should check for it.

**Fix** (`LisaEngine._make_sam_head_fp32`, applied from outside so `code/LISA/`
stays vendored): prompt encoder and mask decoder in fp32, plus a forward hook
casting `text_hidden_fcs` output to fp32 so that evaluate()'s own
`sparse_embeddings.to(pred_embeddings[i].dtype)` keeps the whole path there. The
image encoder stays fp16 — its outputs sit in ~[−0.8, 0.7] and are in no danger.
LLM quantisation is untouched. VRAM cost is negligible.

**Guard for the future:** a NaN mask and a legitimately empty mask are different
results and must never be conflated. If `seg_emit_rate` is high while gIoU is
near zero, suspect arithmetic before concluding anything about the model.

### 6.2 A non-empty mask is not a correct mask

Separately worth knowing: on `obama.jpg` ("Who was the president of the US in
this image?") the pre-fix mask was finite but landed on a **background figure and
part of the podium seal**, not on Obama. Always look at `results/*/vis/` overlays
before believing an aggregate. A plausible-looking gIoU can be built out of
masks that are all in the wrong place.

---

## 7. Failure modes seen, and what they actually mean

| Symptom | Real cause |
| --- | --- |
| Unpickling / `EOFError` loading the checkpoint | shard truncated — check total against 16120985792 bytes |
| Load reaches out to `openai/clip-vit-large-patch14` on the network | `config.vision_tower` not repointed. The released `config.json` carries `train_mask_decoder`, so `LISAForCausalLM.__init__` **ignores** the `vision_tower` kwarg. `LisaEngine` rewrites `config.vision_tower` / `mm_vision_tower` before `initialize_vision_modules` for exactly this reason |
| CUDA OOM at load, before any inference | transient peak of LLM + ViT-H together. `--sam_encoder_device cpu` needs `llm_int8_enable_fp32_cpu_offload=True`, else transformers refuses a non-GPU module in a quantised model |
| `ImportError: cached_download` | `huggingface_hub` ≥ 0.26. It is pinned < 0.26 because transformers 4.31 still imports it |
| Anything breaking in `model/llava/` | `transformers` moved. It is pinned at **4.31.0**; `code/LISA/model/llava/` is a vendored July-2023 snapshot |
| Downloads sitting at 0 bytes forever | running inside the sandbox — disable it for network work |
| `Failed building wheel for tokenizers`, asks for Rust | Python 3.12. Installing Rust will **not** fix it; use 3.11 (§2.1) |
| `emitted_seg` True but mask has 0 pixels | fp16 overflow → NaN in the SAM decoder. See §6.1. Fixed, but check first if it reappears |
| `Cannot copy out of meta tensor` moving the SAM encoder | a `"cpu"` entry in `device_map` makes accelerate *offload* the module. Load with `device_map={"": 0}` and move it afterwards |
| `Input type (torch.cuda.FloatTensor) and weight type (torch.FloatTensor)` | accelerate's `AlignDevicesHook` is still on a module we moved by hand; `remove_hook_from_module(m, recurse=True)` |
| `torch.cuda.is_available()` False after an install | PyPI CPU wheel displaced the CUDA one (§2.2) |
| `KeyError: 'content-length'` in `robust_download.py` | fixed this session — HF serves small non-LFS blobs chunked, with no length header; those now fall back to a single plain GET |

`flash-attn`, `deepspeed` and `peft` are **not** needed. They appear only on the
training and MPT paths, never in `LISAForCausalLM.evaluate`. Do not add them
because upstream's `requirements.txt` lists them.

---

## 8. Decisions already made — don't re-litigate

- **Run scope:** CamouflageData at `--limit 60` (3 per pattern × 3 prompts = 180
  inferences) as the headline result, plus ReasonSeg val (200 images) as the
  calibration benchmark. Chosen with the project owner this session.
- **`--max_new_tokens 32` for the sweeps.** `[SEG]` lands within ~4 generated
  tokens ("Sure, the segmentation result is [SEG]."), and `use_cache=False`
  makes every extra token cost a full-sequence forward pass. 128 is only needed
  when the prose explanation is itself the object of study.
- **The SAM head runs in fp32 and that is not optional.** See §6.1 before
  "simplifying" it back to fp16.
- **The remote is not faster than the laptop** — measured 45.6 s vs 47.7 s per
  inference. Its value is 8 GB of VRAM (enough for the encoder on GPU), 31 GB of
  RAM, and a 16 GB checkpoint downloaded in **9 minutes** rather than an hour.
  The bottleneck on both machines is LLM generation under `use_cache=False`, not
  the SAM encoder, so do not expect throughput gains from GPU placement alone.
- **`code/LISA/` is vendored upstream.** Do not edit it. Device and precision
  changes belong in `lisa_engine.py`, which patches at runtime.
- **`code/weights/`, `code/data/`, `code/wheels/` are not for version control.**
- The graded deliverable is the progress report, so anything under
  `code/results/` is evidence for a report section and must stay reproducible:
  fixed seed, recorded prompts, recorded hardware. `summary.json` captures GPU
  name, quantisation, seed and peak VRAM for this reason.

---

## 9. Next steps

1. Finish the downloads, run `smoke_test.py`, then the two evaluations above.
2. Get the username + key installed on `cenara70hx` and re-run there at
   `--sam_encoder_device cuda`. Compare against the local numbers — if they
   differ, the CPU-offload claim in §5.1 is wrong and that matters.
3. Correlate per-pattern IoU against the `camo_contrast` ranking already in
   `code/results/dataset_analysis.json`. A statement about *which* camouflage
   defeats language-guided segmentation is worth more than one average IoU.
4. Lock the shared benchmark (refCOCO/+/g) and the per-image CSV format with the
   PixelLM and GLaMM owners **before** anyone runs anything. Note refCOCO needs
   COCO train2014 (~13 GB).

---

## 10. Completed 2026-08-24: multi-person and tiny-street-person pilots

Two fixed, self-contained P1/P2 pilots were completed on `cenara70hx` and copied
into the local website:

- `code/results/grefcoco_pilot_p1_p2`: 30 expressions (15 multi-target, 10
  single-target in a crowd, five no-target), exposed as 60 paired browse rows.
- `code/results/mots_small_person_pilot_p1_p2`: 12 MOTSChallenge frames with at
  least two pedestrians and a smallest person <=64 px, exposed as 24 paired
  browse rows.

Headline gRefCOCO result: P1 gIoU 62.66%, P2 20.31%; P1 won 24/30. P1 target
instance coverage was 90%, but it failed all five no-target cases. P2 rejected
all five no-target cases, but its VQA-answer-to-DINO bridge emitted a mask on
only 6.67% of all requests. Do not summarize this result without both facts.

Headline MOTS result: P2 gIoU 87.71%, P1 83.68%; P2 won 9/12. On the five
frames containing a person <=32 px, P1 nevertheless covered 76.00% of labeled
instances versus P2's 67.89%. Union IoU alone hides missed tiny people.

The exact method, tables, interpretation, caveats, and next tests are in
`docs/grefcoco-mots-pilot-report.md`. The prepared 150-expression gRefCOCO pool
remains for a later thesis-scale run. Website API, English/Thai rendering,
paired filters, overlays, and Previous/Next navigation were all validated after
importing the pilot artifacts.

---

## 11. Completed 2026-08-25: full MOTS surveillance person test

The full prepared pool of 60 MOTS frames was completed remotely on `cenara70hx`
and imported to `code/results/mots_small_person_p1_p2`. It contains 593 labeled
people. The website exposes 180 browse rows: 60 each for P1, unchanged P2, and
the P2-direct fixed-query ablation.

Using the identical per-person rule (a person is detected when at least 50% of
their visible ground-truth pixels are covered), P1 detected 405/593 (68.30%),
P2 detected 469/593 (79.09%), and P2-direct detected 488/593 (82.29%). P2 had
the best mask quality at 90.55% gIoU and the fewest false-positive pixels
(607,039). P2-direct's higher person recall came with 88.66% gIoU and 952,463
false-positive pixels.

Tiny-person detection remains the main failure: of 25 people <=32 px tall, P1
detected 7, P2 detected 3, and P2-direct detected 4. Never infer tiny-person
recall from union gIoU alone.

P2-direct is not a new complete pipeline. It removes BLIP-2/Q-Former and sends
`person.` directly into Grounding DINO, so it is evidence about the value and
cost of the VQA bridge only. The full 150-expression gRefCOCO pool remains the
next uncompleted full evaluation.
