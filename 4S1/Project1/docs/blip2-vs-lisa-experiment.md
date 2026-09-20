# BLIP-2/Q-Former versus LISA on camouflaged-person segmentation

Experiment completed **2026-08-24**. All model inference, mask generation,
metric calculation, paired comparison, and bootstrap analysis ran on the remote
Tailscale host **`cenara70hx`** (NVIDIA CMP 70HX, 8 GB). The local copies in this
repository are report and website artifacts.

## Answer in one paragraph

**Yes, the tested modular pipeline outperformed LISA on mean per-image IoU
(gIoU), but not on every metric.** BLIP-2/Q-Former alone cannot draw a mask. We
used it to name the target, Grounding DINO to turn that name into bounding boxes,
and SAM ViT-H to turn the boxes into masks. On the same 180 prompt-image pairs,
this pipeline achieved **72.21 gIoU**, versus **59.51 for LISA** (+12.70 points).
However, its overall area-weighted cIoU was **53.51**, versus **60.56 for LISA**
(-7.05 points), because one generic-prompt prediction covered an extremely large
false-positive area. With the explicit and reasoning prompts, the pipeline beat
LISA on both gIoU and cIoU.

This is therefore evidence for a strong **BLIP-2 + detector + segmenter
pipeline**, not evidence that BLIP-2 itself is a segmentation model.

## Model relationship

LISA and BLIP-2 are neither the same model nor subsets of one another.

- **BLIP-2** connects a frozen image encoder to a frozen language model through
  a learned **Q-Former**. It produces text, such as `a person` or `a soldier`.
- **LISA** is a language-instructed segmentation model. Its language model emits
  a special `[SEG]` token whose embedding drives a SAM-derived mask decoder.
- In this experiment, BLIP-2 supplied semantic target identification, while two
  separate models supplied localization and pixel masks.

The tested flow was:

```text
image + adapted question
        |
        v
BLIP-2 FLAN-T5-XL (Q-Former) -> short target phrase
        |
        v
Grounding DINO Tiny -> target bounding box(es)
        |
        v
SAM ViT-H -> binary mask -> same metrics and ground truth as LISA
```

## Test protocol

| Property | Value |
| --- | --- |
| Dataset | CamouflageData |
| Unique images | 60: the exact image IDs used by the completed LISA run |
| Prompt conditions | 3 per image: generic referring, explicit camouflage, reasoning |
| Total paired requests | 180 |
| LISA baseline | LISA-7B-v1, 4-bit, existing completed remote run |
| BLIP-2 | `Salesforce/blip2-flan-t5-xl`, 8-bit, deterministic decoding |
| Localization | `IDEA-Research/grounding-dino-tiny`, FP32 |
| Segmentation | `facebook/sam-vit-huge`, FP16 |
| Box/text thresholds | 0.25 / 0.25, fixed before the full run |
| Multiple boxes | All accepted boxes unioned; no ground-truth-guided selection |
| Explicit negative answer | Produces an empty mask and scores IoU 0 when GT is present |
| Metrics | gIoU, cIoU, Dice, precision, recall, IoU thresholds, emit rate, compute time |
| Randomness | Model decoding disabled; bootstrap seed fixed |

The original LISA prompts ask the model to segment. Because BLIP-2 only returns
text, each prompt was semantically adapted into a target-identification question
that requests a short noun phrase. This adaptation is necessary, but means the
two systems do not receive byte-identical text.

## Main results

All values below are percentages except latency. Bold identifies the better
segmentation score in each comparison.

| Prompt | System | gIoU | cIoU | Dice | IoU >= 0.5 | Mask emitted | Component compute |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | **BLIP-2 pipeline** | **72.21** | 53.51 | **80.36** | **89.44** | 97.22 | 8.25 s |
| Overall | LISA | 59.51 | **60.56** | 67.85 | 65.00 | **100.00** | 46.80 s |
| Generic referring | **BLIP-2 pipeline** | **70.16** | 35.27 | **77.93** | **86.67** | 95.00 | 8.09 s |
| Generic referring | LISA | 52.43 | **53.79** | 60.16 | 55.00 | **100.00** | 44.76 s |
| Explicit camouflage | **BLIP-2 pipeline** | **73.05** | **71.37** | **81.34** | **90.00** | 98.33 | 8.33 s |
| Explicit camouflage | LISA | 65.01 | 68.62 | 72.98 | 75.00 | **100.00** | 44.76 s |
| Reasoning | **BLIP-2 pipeline** | **73.42** | **71.80** | **81.79** | **91.67** | 98.33 | 8.31 s |
| Reasoning | LISA | 61.09 | 59.36 | 70.41 | 65.00 | **100.00** | 50.87 s |

The pipeline's best prompt was reasoning: **73.42 gIoU / 71.80 cIoU**. LISA's
best gIoU and cIoU were both from the explicit prompt: **65.01 / 68.62**. Thus,
best-versus-best gains were **+8.41 gIoU** and **+3.18 cIoU** points.

## Paired analysis

Every pipeline row was matched to the same LISA image and prompt.

| Scope | Pipeline wins | LISA wins | Ties | Mean IoU gain | Bootstrap 95% interval | cIoU change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall (n=180) | 110 | 62 | 8 | **+12.70** | **+8.82 to +16.75** | -7.05 |
| Generic (n=60) | 38 | 19 | 3 | **+17.74** | **+9.10 to +26.38** | -18.52 |
| Explicit (n=60) | 33 | 24 | 3 | **+8.04** | **+2.80 to +14.08** | +2.75 |
| Reasoning (n=60) | 39 | 19 | 2 | **+12.33** | **+6.73 to +18.74** | +12.44 |

The intervals use 10,000 paired bootstrap resamples. They exclude zero for all
three prompt conditions, supporting a real per-image IoU improvement on this
sample. This does not remove the cIoU warning: gIoU weights each request equally,
whereas cIoU pools pixels and is highly sensitive to a very large false mask.

## What succeeded and what failed

The pipeline produced a mask for 175 of 180 requests. Its IoU was at least 0.5
on 161 requests (89.44%), compared with 117 for LISA (65.00%). It was especially
strong with the explicit and reasoning prompts.

BLIP-2's answers also show that the Q-Former stage is not a dependable semantic
oracle. The most common answers were `a person` (76), `person` (51),
`a hunter` (17), `a soldier` (14), and `a man` (11). Mistakes included
`no person` (2), `a fox`, `a wolf`, `a gorilla` (2), `a sailor`, and
`a person riding a bike` (2). The two `no person` answers correctly yielded
empty masks rather than accidentally grounding the word `person`.

The worst generic-prompt failure returned a huge false mask. It raised the
pooled union enough to pull generic-prompt cIoU down to 35.27 even though its
mean per-image gIoU was 70.16. This single-mode weakness is a useful research
gap: confidence-based rejection or box/mask-size filtering could improve cIoU,
but must be evaluated with rules fixed without looking at ground truth.

## Compute interpretation

The measured mean component times were 0.72 s for BLIP-2, 2.57 s for Grounding
DINO, and 4.95 s for SAM, totaling 8.25 s. The arithmetic ratio to LISA's 46.80
s is 5.67x. Treat this as **indicative component compute**, not production
end-to-end latency: the 8 GB GPU cannot hold all three models simultaneously, so
the benchmark ran them as resumable stages and excluded model loading and model
swap time. A live service needs either more VRAM, CPU/offload, or a different
pipeline design before its latency can be compared fairly.

Peak VRAM by isolated stage was 5.231 GB (BLIP-2), 1.956 GB (Grounding DINO),
and 3.262 GB (SAM). LISA's completed run peaked at 6.91 GB.

## Integrity decisions

- In the first grounding attempt, an answer of `no person` was sent literally
  to Grounding DINO, which could still activate its `person` token. That attempt
  was stopped, preserved as
  `grounding_boxes.invalid_negation_attempt.jsonl`, and excluded. The full 180
  rows were regenerated with explicit negative answers mapped to no boxes.
- Grounding DINO Tiny was changed from FP16 to FP32 after a remote smoke test
  exposed an input/weight dtype mismatch. Its measured peak remained below 2 GB.
- Empty predictions score zero when a person is present. Multiple accepted
  boxes are unioned. Neither rule uses ground truth.
- LISA and the new pipeline use the same ground-truth masks and the same local
  `metrics.py` implementation.
- No threshold tuning or post-processing search was performed on these 60
  evaluation images.

## Limitations

1. This is a 60-image, single-dataset experiment, with three correlated prompts
   per image. The paired bootstrap resamples rows, not unique images, so its
   interval may be narrower than an image-clustered analysis.
2. The comparison is a modular three-model pipeline versus an integrated LISA
   model; it does not isolate how much gain comes from Q-Former, Grounding DINO,
   or standalone SAM.
3. The LISA decoder is language-conditioned and task-tuned; SAM here is
   box-prompted by a separate detector. Their supervision and interfaces differ.
4. The prompt intent is matched, but exact text is necessarily adapted for a
   VQA-only text output.
5. Component compute is not staged end-to-end wall time, as explained above.

## Research gaps worth testing next

These follow directly from the measured failures and are stronger than simply
studying LISA's architecture again:

1. **Failure-gated pipeline:** reject implausibly large masks, low-confidence
   boxes, or contradictory BLIP-2 answers using thresholds selected on a
   separate validation split. Primary hypothesis: recover cIoU without lowering
   gIoU.
2. **Ablate Q-Former:** compare BLIP-2 phrases against fixed `person`, fixed
   `camouflaged soldier`, an open-vocabulary detector alone, and oracle GT class
   text. This measures whether BLIP-2 adds value or merely often outputs
   `person`.
3. **Component attribution:** replace one component at a time: BLIP-2 variants,
   Grounding DINO Base/Tiny, and SAM/ SAM 2 variants, under a fixed protocol.
4. **Image-clustered uncertainty:** bootstrap 60 unique images while retaining
   all three prompt rows per draw.
5. **True end-to-end latency and memory:** test on a GPU that holds all
   components together, including loading, transfers, and post-processing.
6. **External validation:** freeze every rule, then run a larger unseen
   camouflage split and a non-camouflage referring-segmentation set.

## Reproduction and website artifacts

The following local artifacts are ready for later website integration:

- `code/results/blip2_grounded_sam/summary.json`: headline metrics, matched LISA
  metrics, paired analysis, failure diagnostics, model configuration, and GPU.
- `code/results/blip2_grounded_sam/per_image.csv`: all 180 result rows, including
  pipeline and matched LISA values.
- `code/results/blip2_grounded_sam/masks/`: 180 binary prediction masks.
- `code/results/blip2_grounded_sam/blip2_answers.jsonl`: raw target phrases and
  BLIP-2 timings.
- `code/results/blip2_grounded_sam/grounding_boxes.jsonl`: accepted boxes,
  scores, and grounding timings.
- `code/results/blip2_grounded_sam/sam_timings.jsonl`: mask paths and SAM
  timings.
- `code/results/blip2_grounded_sam/remote_benchmark.log`: remote execution log.
- `code/scripts/run_blip2_grounded_sam.py`: resumable five-stage benchmark.
- `code/scripts/setup_blip2_remote.sh` and
  `code/scripts/run_blip2_benchmark_remote.sh`: isolated remote setup and runner.

For the website, add this result directory as a second system beside
`code/results/camouflage`. The report page should show gIoU and cIoU together,
label latency as component compute, and identify the system as
**BLIP-2/Q-Former -> Grounding DINO -> SAM**, never as BLIP-2 alone.
