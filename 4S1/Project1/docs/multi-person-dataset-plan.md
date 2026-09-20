# Multi-person dataset expansion plan

Updated: 2026-08-24

Systems under test:

- **P1:** LISA
- **P2:** BLIP-2/Q-Former -> Grounding DINO -> SAM

All GPU inference must run on the Tailscale host `cenara70hx`. At the time of
this review the host had 367 GB free, but COCO/gRefCOCO was not installed.

## Recommended benchmark order

### 1. gRefCOCO — primary benchmark

Use this first. It is a generalized referring-expression segmentation dataset
with pixel masks and three important cases: single target, multiple targets, and
no target. It uses MS COCO `train2014` images. The complete dataset contains
278,232 expressions, including 80,022 multi-target and 32,202 no-target
expressions over 19,994 images.

Official sources:

- Dataset/API: https://github.com/henghuiding/gRefCOCO
- Paper: https://openaccess.thecvf.com/content/CVPR2023/papers/Liu_GRES_Generalized_Referring_Expression_Segmentation_CVPR_2023_paper.pdf

Recommended first pilot: 150 expressions, stratified as follows.

| Group | Samples | Purpose |
|---|---:|---|
| Multi-target person | 75 | Can the system return every requested person? |
| Single-target person in a multi-person image | 50 | Can it select the correct person rather than the whole group? |
| No-target person expression | 25 | Can it correctly return an empty mask? |

Within the multi-target group, balance images containing 2, 3–5, and 6+ target
people where the annotations permit it. Do not tune thresholds on these pilot
samples; create a separate development subset if tuning is needed.

### 2. RefCOCO / RefCOCO+ testA — selection benchmark

The testA splits contain person targets. These are mostly single-target
expressions and are useful for checking whether a model can select one described
person when other people are present. They do not replace gRefCOCO because they
do not test expressions that intentionally refer to several people.

Reference: https://github.com/tensorflow/datasets/blob/master/docs/catalog/ref_coco.md

### 3. COCO 2017 person subset — simple all-person stress test

Filter validation images to category `person`, retain images with two or more
non-crowd person instances, and union the ground-truth instance masks. Use the
same fixed prompt (for example, `segment all people`) for both systems. COCO has
detailed instance masks, but no referring expression for this derived task, so
report it as a synthetic stress test rather than a language benchmark.

Official source: https://cocodataset.org/dataset/detection-2017.htm

### 4. PhraseCut miniv — optional quick generalization smoke test

PhraseCut supplies binary masks for phrase-region pairs and a downloadable
100-image `miniv` split. It is useful for a small out-of-domain check. Its
expressions and construction differ from gRefCOCO, so it should be secondary.

Official source: https://github.com/ChenyunWu/PhraseCutDataset

### 5. MHP v2 / CIHP — optional crowd and occlusion stress test

These datasets contain multiple people with instance-level, fine-grained human
part annotations. MHP v2 has 25,403 images, each with at least two people. They
do not provide referring expressions, so body-part labels must be merged into
person masks and prompts must be synthesized. Use only as an additional
human-crowd robustness test, not the main P1-vs-P2 benchmark.

Official MHP source: https://github.com/ZhaoJ9014/Multi-Human-Parsing

CrowdHuman is not suitable for mask-IoU comparison because its official labels
are bounding boxes, not person segmentation masks. It can test DINO detection,
but not the complete P1-vs-P2 segmentation pipeline fairly.

## Metrics to report

Use the same metrics and image/prompt pairs for P1 and P2:

- gIoU and cIoU of the union target mask
- Dice
- precision and recall
- target-instance coverage: percentage of ground-truth people with at least 50%
  of their mask covered
- no-target accuracy and false-positive mask area
- latency and peak VRAM

Report results separately for single-target, multi-target, and no-target cases,
then split multi-target results by target count (2, 3–5, and 6+). A single
overall IoU can hide the failure to segment a small person in a group.

## Required pipeline checks

- P2 already passes every DINO box to SAM and unions the resulting masks.
- P1 already unions every mask emitted by LISA.
- Preserve individual GT person masks for target-instance coverage even though
  the principal segmentation score uses their union.
- Record P2's detected-box count as a diagnostic only; it is not a fair primary
  metric because P1 does not expose boxes.
- Freeze prompts and thresholds before the held-out benchmark.

## Recommended decision

Run the 150-expression gRefCOCO pilot first. Add RefCOCO testA only if the team
also wants a focused test of selecting one person from a group. Use COCO-person
or MHP v2 afterward for crowd stress testing, clearly labelled as synthetic
language tasks.
