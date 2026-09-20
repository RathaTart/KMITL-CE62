# CE69-27 — Research findings and roadmap

Prepared for progress item 2, *ทดสอบผลตามงานที่ศึกษาด้วยตนเอง*.
Scope: the LISA track (ราธา). Everything below is sourced from the official
repositories and papers, or measured locally — no estimated numbers.

---

## 1. What LISA was trained and tested on

Verified against `dvlab-research/LISA` (official repo) and Lai et al., CVPR 2024.

| Role | Datasets | Notes |
| --- | --- | --- |
| Semantic segmentation | ADE20K, COCO-Stuff, **Mapillary Vistas**, PACO-LVIS, PASCAL-Part | COCO-Stuff uses `stuffthingmaps_trainval2017`; only the PACO-LVIS part of PACO |
| Referring segmentation | refCOCO, refCOCO+, refCOCOg, refCLEF | refCLEF images come from saiapr_tc-12 |
| VQA | LLaVA-Instruct-150k | no masks; preserves LLaVA's language ability |
| Reasoning segmentation | **ReasonSeg** — 1218 images (239 train / 200 val / 779 test) | also the *evaluation* benchmark |

Training mixes these four groups at sample rates **9 : 3 : 3 : 1**
(`--dataset="sem_seg||refer_seg||vqa||reason_seg"`).

**Evaluation** is on ReasonSeg, scored with **gIoU** (mean of per-image IoU) and
**cIoU** (Σintersection / Σunion). Paper Table 1, val overall:

| Method | gIoU | cIoU |
| --- | ---: | ---: |
| OVSeg | 28.5 | 18.6 |
| GRES | 22.4 | 19.9 |
| X-Decoder | 22.6 | 17.9 |
| SEEM | 25.5 | 21.2 |
| **LISA-7B** | **44.4** | **46.0** |
| LISA-7B (ft) | 52.9 | 54.0 |
| LISA-13B | 48.9 | 46.9 |
| LISA-Llama2-13B (ft) | 60.0 | 67.8 |

### Two corrections for the progress report

1. **Reference [3] cites the wrong repository.** The report lists
   `github.com/JIA-Lab-research/LISA`. The official repository is
   **`github.com/dvlab-research/LISA`**.
2. **§5.3.2.2 omits Mapillary Vistas** from the semantic-segmentation list. The
   repo lists five datasets (ADE20K, COCO-Stuff, Mapillary, PACO-LVIS,
   PASCAL-Part); the report names only ADE20K, COCO-Stuff and "object-part
   datasets".

A third point worth adding to §5.3.2: LISA sets `config.use_cache = False`, so
text generation recomputes the whole sequence at every step. This is why LISA is
far from real-time — a fact that supports the report's existing argument in §6.

---

## 2. Local dataset characterisation (measured)

Run with `python code/scripts/analyze_datasets.py` — needs no GPU and no
downloads. Full output in `code/results/dataset_analysis.json`.

### ReasonSeg val (200 images)

| Property | Value |
| --- | --- |
| Query type | 87 short phrase / 113 long sentence |
| Query length | median 19 words (max 42) |
| Target area | median **6.32 %** of frame (p25 1.99 / p75 16.25) |
| Images with *ignore* regions | 76 of 200 |
| Resolution | median 1.81 MP |

### CamouflageData (1000 images, 20 patterns, 854×480)

| Property | Value |
| --- | --- |
| Target area | median **0.997 %** of frame (p25 0.519 / p75 2.142) |
| Target size | bounding box ≈ **63–75 px** per side on most patterns |
| Camouflage contrast | median **48.2** RGB units vs. local background ring |

Hardest subsets by target size:

| Set | Pattern | Target area | Box side | Contrast |
| --- | --- | ---: | ---: | ---: |
| dataset05 | Desert Digital MARPAT | 0.503 % | 63 px | 40.7 |
| dataset06 | Desert DPM | 0.644 % | 71 px | 34.5 |
| dataset18 | German WWII 44 Dot | 0.647 % | 69 px | 42.1 |
| dataset09 | MARPAT Digital Woodland | 0.658 % | 74 px | 57.7 |
| dataset08 | German Snow Camouflage | 0.712 % | 71 px | 34.7 |

Best-blended (lowest contrast with surroundings):

| Set | Pattern | Contrast | Target area |
| --- | --- | ---: | ---: |
| dataset01 | Arid Fleck | 25.9 | 0.920 % |
| dataset20 | Kryptek Mandrake | 28.4 | 0.785 % |
| dataset12 | British Multi-Terrain Pattern | 32.6 | 1.502 % |
| dataset06 | Desert DPM | 34.5 | 0.644 % |
| dataset08 | German Snow Camouflage | 34.7 | 0.712 % |

### Why this matters for the experiment design

**CamouflageData targets are ~6× smaller than what LISA was benchmarked on**
(0.997 % vs 6.32 % of frame). Three consequences:

1. **Expect a large drop versus the published 44.4 gIoU.** This is a genuine
   domain shift (small, low-contrast targets), not a bug. Document it as a
   finding rather than treating it as a failed reproduction.
2. **gIoU and cIoU will diverge sharply.** cIoU is area-weighted, so the handful
   of images with large targets (max 32 % of frame) will dominate it while the
   median 0.5 % target contributes almost nothing. Report both, and say which
   one the conclusion rests on.
3. **SAM's mask decoder outputs at 256×256 before upsampling.** A 63 px target in
   an 854×480 frame is roughly 19 px at decoder resolution — near the resolution
   floor. This is a concrete, defensible hypothesis for *why* performance drops,
   and it suggests tiling/upscaling as the improvement to try in item 6.

The `camo_contrast` metric (mean RGB distance between target pixels and a
15-px dilated background ring) is our own; it gives a per-pattern difficulty
ranking that can be correlated against per-pattern IoU once the model runs. That
correlation would be a legitimate contribution for the draft paper.

---

## 3. The three models compared

All three are CVPR 2024 papers built on LLaVA. Sourced from official repos.

| | **LISA** | **PixelLM** | **GLaMM** |
| --- | --- | --- | --- |
| Repo | `dvlab-research/LISA` | `MaverickRen/PixelLM` | `mbzuai-oryx/groundingLMM` |
| Mask generator | **SAM ViT-H** (external, frozen encoder) | **lightweight pixel decoder** (no SAM) | SAM-based grounding decoder |
| Mask mechanism | `[SEG]` token → embedding-as-mask | segmentation **codebook**, multi-scale tokens | grounded caption → per-phrase masks |
| Targets per query | single | **multiple / open-set** | multiple, tied to caption phrases |
| Own benchmark | **ReasonSeg** (1218 img) | **MUSE** (246k QA, 0.9M instances) | **GranD-f** GCG (~214k pairs) |
| Own dataset scale | small | medium | **GranD: 7.5M concepts / 810M regions** |
| Vision tower | CLIP ViT-L/14 @224 | CLIP ViT-L/14-336, resized to **448** | CLIP ViT-H |
| 7B checkpoint | 15.0 GB | **12.8 GB** | 15.6 GB (13B-class) |
| Extra input | image + text | image + text | image + text **+ region/bbox prompts** |

### The key finding for a fair comparison

**The three models do not share a benchmark.** LISA reports ReasonSeg, PixelLM
reports MUSE, GLaMM reports GCG on GranD-f. Comparing published headline numbers
would be meaningless.

**The common ground is referring expression segmentation on refCOCO / refCOCO+ /
refCOCOg.** All three train on it and all three report it. That is the axis on
which a fair, citable comparison can be built — and it is also the closest task
to the project's actual goal ("segment the person wearing a black hat").

Recommended comparison design:

- **Axis A — published common benchmark:** refCOCO/+/g validation. Reproduce, do
  not re-train. Confirms the setup is correct before trusting anything else.
- **Axis B — the project's own data:** CamouflageData (has masks) with an
  identical prompt template for all three models. This is progress item 4.
- **Axis C — cost:** VRAM, latency per image, checkpoint size. PixelLM should win
  here because it has no SAM ViT-H; that is a prediction worth testing.

### Practical notes per model

- **PixelLM is the cheapest to run** (12.8 GB, no SAM) and the only one designed
  for *multiple* targets — relevant for surveillance frames containing several
  people. Its inference needs several non-default flags
  (`--seg_token_num=3 --resize_vision_tower_size=448 --image_feature_scale_num=2
  --separate_mm_projector`); omitting them silently produces wrong results.
- **GLaMM is the heaviest but most flexible** — it accepts region/bbox prompts in
  addition to text, so it can be driven by an upstream person detector. All GLaMM
  variants are fine-tuned from `GLaMM-GranD-Pretrained`; use **GLaMM-RefSeg** for
  Axis A and **GLaMM-FullScope** for demos.
- **LISA is the best-documented and the simplest** to reproduce, which is why it
  is the right first model — the pipeline built for it (`code/scripts/`)
  generalises to the other two with only a loader swap.

---

## 4. The hardware constraint — the project's real bottleneck

Measured on the dev machine:

| Resource | Available | Needed for a 7B language-guided segmenter |
| --- | --- | --- |
| GPU | RTX 3060 Laptop, **6.0 GB** | LISA-7B NF4 ≈ **5.75 GB of weights alone** |
| RAM | 15.4 GB total, **0.7 GB free** | 10 GB transient just to load one shard |
| Disk | 91 GB free | fine |

LISA-7B at 4-bit breaks down as: LLM 3.86 GB + CLIP 0.61 GB + SAM ViT-H 1.28 GB
= 5.75 GB, leaving ~0.1 GB for activations on a 6 GB card. Upstream's own README
states 4-bit 13B needs 9 GB, and 7B is not far below that.

**This constraint applies to all three models, not just LISA.** GLaMM (15.6 GB)
and PixelLM (12.8 GB) are in the same class. Planning compute is therefore a
whole-project decision, not a LISA detail.

Options, best first:

1. **Free cloud T4/P100 (Google Colab, Kaggle) — 16 GB VRAM.** Fits all three at
   4-bit with room for activations, and downloads run on a datacentre link
   instead of a home connection. **Strongly recommended** — it removes both the
   VRAM and the bandwidth problem at once.
2. **A KMITL lab GPU**, if the department has one. Best for the final numbers,
   since results should be produced on one fixed machine for comparability.
3. **Local 6 GB fallback** — works only with the SAM encoder on CPU (already
   implemented in `code/scripts/lisa_engine.py --sam_encoder_device cpu`).
   Expect ~30–60 s per image and heavy paging unless RAM is freed.

Whatever is chosen, **record it once and keep it fixed** — latency/FPS numbers
are only comparable within one machine, and the report promises a
latency-vs-accuracy trade-off analysis.

---

## 5. Status of the reproduction attempt

| Component | State |
| --- | --- |
| ReasonSeg val (200 images + annotations) | ✅ downloaded, verified |
| CamouflageData | ✅ local, characterised |
| Inference + evaluation code | ✅ written, syntax-checked, metrics unit-tested |
| LISA-7B-v1 weights | ✅ complete, sha256 verified (16.12 GB) |
| CUDA PyTorch wheel | ✅ complete (cp311 — **not** cp312, see CLAUDE.md) |
| Actual LISA results | ✅ **obtained 2026-08-22** — CamouflageData gIoU 59.5 / cIoU 60.6, ReasonSeg val gIoU 87.8 (contaminated), drone qualitative |

**Item 2 is now complete.** Full numbers, the three findings, and the
reproducibility table are in [session-handoff.md](session-handoff.md) §0; a
published summary page is linked there. Headlines:

- CamouflageData, 180 inferences: **gIoU 59.51 / cIoU 60.56**, 65.0 % at
  IoU ≥ 0.5, `[SEG]` emit rate 100 %.
- Prompt phrasing is worth **+12.6 gIoU**; the reasoning phrasing loses to the
  plain explicit one.
- Pattern difficulty spans **3×** and correlates with *nothing* measured
  (contrast ρ = +0.16) — this replaces the roadmap's item 9 hypothesis, which
  predicted a contrast correlation and was **wrong**.
- Prediction fragmentation predicts accuracy (79.3 → 26.0 mean IoU) and needs no
  ground truth — a new improvement lead that did not exist when this roadmap was
  written.

One correction to §6 item 8: **tiling / upscaling for small targets is no longer
the top-ranked idea.** Target size correlates only weakly with difficulty
(ρ = +0.36 area, +0.38 bbox side), so the expected payoff is much lower than
assumed. Prompt engineering measured **+12.6 gIoU** for free, and the
fragmentation signal is the better second lead.

---

## 6. Roadmap

### Immediate (before the next progress report)

1. **Move to Colab/Kaggle.** Port `code/scripts/` — it is already
   device-configurable. On a 16 GB T4, use `--quantization 4bit
   --sam_encoder_device cuda` and drop the CPU-offload path entirely.
2. **Run the reproduction:** `run_eval.py --task reasonseg`. Compare against
   44.4 / 46.0.
   ⚠️ **Upstream states the `v1` checkpoints were trained on ReasonSeg
   train+val.** Results on val are therefore contaminated and will look
   optimistic. To reproduce the paper's val row honestly you need the **`v0`**
   checkpoint (`LISA-13B-llama2-v0`) with the legacy repo at commit `0e26916`.
   Report this explicitly — noticing it is itself a good finding.
3. **Run the smoke test first** (`scripts/smoke_test.py`) — five README examples
   with published expected outputs. If those look wrong, the benchmark numbers
   are meaningless.
4. **Run CamouflageData with the three prompt variants** already defined in
   `run_eval.py`. The prompt-sensitivity result is a genuine contribution and
   costs nothing extra.

### Short term (items 3–5)

5. **Decide the common benchmark now — refCOCO/+/g.** Getting this wrong later
   invalidates the whole comparison. Note the refCOCO series needs COCO
   train2014 images (~13 GB), so plan bandwidth for it.
6. **Have สรศักดิ์ and พัฒน์กุลธร claim PixelLM and GLaMM.** Both are LISA
   derivatives; the loaders differ but the evaluation harness in
   `code/scripts/metrics.py` and `run_eval.py` is shared. Agree on the output
   format (per-image CSV with the same columns) *before* anyone starts running.
7. **Fix the protocol in writing:** one prompt template per task, fixed seed,
   fixed image preprocessing, one machine, gIoU + cIoU + Dice + latency + peak
   VRAM. Include `seg_emit_rate` — a model that answers in prose without
   emitting a mask token must count as a failure, not be silently skipped.

### Medium term (items 6–7)

8. **Improvement hypothesis, ranked by expected payoff:**
   - **Tiling / upscaling for small targets** — directly attacks the measured
     0.997 % target-area problem and the 256×256 decoder floor. Highest expected
     gain, needs no training.
   - **Prompt engineering** — cheapest; the three-variant experiment already
     measures its ceiling.
   - **LoRA fine-tune on CamouflageData** — highest gain but needs a GPU the team
     may not have, plus image–instruction–mask triples that must be authored.
9. **Correlate per-pattern IoU against the `camo_contrast` ranking** already
   computed. If they correlate, the report gains a quantitative statement about
   *which camouflage defeats language-guided segmentation*, which is more
   interesting than a single average IoU.

### Risks

| Risk | Mitigation |
| --- | --- |
| Bandwidth (≈45 GB of checkpoints across three models) | Do downloads in the cloud, not locally |
| `v1` checkpoint contamination on ReasonSeg val | Use v0 for the reproduction claim, or report the caveat prominently |
| Three models never becoming comparable | Lock the refCOCO axis and the output format now |
| CamouflageData has no natural-language instructions | Prompt templates are authored by us — record them verbatim in the report |
| Person-detection framing vs. mask output | Convert masks to bounding boxes for a secondary box-level comparison (already in the proposal) |

---

## 7. Files produced

| Path | Purpose |
| --- | --- |
| `code/scripts/lisa_engine.py` | batch-capable LISA inference; device/quantisation control for 6 GB GPUs |
| `code/scripts/run_eval.py` | ReasonSeg / CamouflageData / drone evaluation driver |
| `code/scripts/metrics.py` | gIoU, cIoU, Dice, with ReasonSeg *ignore*-region handling |
| `code/scripts/analyze_datasets.py` | dataset characterisation (no GPU needed) |
| `code/scripts/smoke_test.py` | five published README examples, for validating the setup |
| `code/scripts/robust_download.py` | chunked resumable downloader with SHA-256 verification |
| `code/scripts/make_report.py` | regenerates the report tables from run artifacts |
| `code/results/dataset_analysis.json` | measured dataset statistics |
| `CLAUDE.md` | environment, architecture and pinning rationale |

---

## ภาคผนวก — สรุปภาษาไทยสำหรับหัวข้อที่ 2

**สิ่งที่ทำสำเร็จ**

1. ยืนยันชุดข้อมูลที่ LISA ใช้ฝึกและทดสอบจากคลังโค้ดทางการ ได้แก่ ADE20K, COCO-Stuff,
   Mapillary Vistas, PACO-LVIS, PASCAL-Part (semantic segmentation); refCOCO,
   refCOCO+, refCOCOg, refCLEF (referring segmentation); LLaVA-Instruct-150k
   (VQA); และ **ReasonSeg** (reasoning segmentation) ซึ่งเป็นทั้งชุดฝึกและชุดทดสอบหลัก
   โดยผสมข้อมูลด้วยอัตรา 9:3:3:1
2. ดาวน์โหลด ReasonSeg val จำนวน 200 ภาพพร้อม annotation ครบถ้วน
3. พัฒนาโปรแกรมทดสอบและวัดผล (gIoU, cIoU, Dice, latency) ที่ใช้รูปแบบคำสั่งตรงกับ
   `ValDataset` ของ LISA เพื่อให้เทียบกับผลในบทความได้อย่างเป็นธรรม
4. วิเคราะห์คุณลักษณะชุดข้อมูลเชิงปริมาณ พบว่าเป้าหมายใน CamouflageData มีขนาดเฉลี่ย
   **0.997%** ของภาพ ซึ่งเล็กกว่า ReasonSeg (**6.32%**) ประมาณ 6 เท่า

**สิ่งที่ยังไม่สำเร็จและเหตุผล**

การทดสอบจริงยังไม่เสร็จ เนื่องจากความเร็วอินเทอร์เน็ตลดลงเหลือประมาณ 0.03 MB/s
ระหว่างดาวน์โหลดน้ำหนักแบบจำลอง (15 GB) ทำให้ต้องใช้เวลาเกิน 60 ชั่วโมง
จึงหยุดการดาวน์โหลดไว้ก่อน (ข้อมูลที่ดาวน์โหลดแล้ว 4.2 GB ยังใช้ต่อได้)

**ข้อจำกัดด้านฮาร์ดแวร์ที่ต้องแก้ก่อน**

GPU ที่ใช้มีหน่วยความจำ 6 GB แต่ LISA-7B แบบ 4-bit ต้องใช้ประมาณ 5.75 GB
เฉพาะน้ำหนักแบบจำลอง จึงเหลือพื้นที่ไม่พอสำหรับการคำนวณ และข้อจำกัดนี้ใช้กับ
PixelLM (12.8 GB) และ GLaMM (15.6 GB) เช่นกัน **จึงเสนอให้ย้ายไปใช้ Google Colab
หรือ Kaggle (T4 16 GB) หรือเครื่องของภาควิชา**

**ข้อค้นพบสำคัญสำหรับการเปรียบเทียบ 3 แบบจำลอง**

แบบจำลองทั้งสามไม่ได้ใช้ชุดทดสอบเดียวกัน (LISA→ReasonSeg, PixelLM→MUSE,
GLaMM→GranD-f) จึงไม่สามารถนำตัวเลขในบทความมาเทียบกันโดยตรง **จุดร่วมที่ใช้เทียบได้
คือ refCOCO / refCOCO+ / refCOCOg** ซึ่งทั้งสามแบบจำลองฝึกและรายงานผลไว้
และเป็นงานที่ใกล้เคียงวัตถุประสงค์ของโครงงานมากที่สุด
