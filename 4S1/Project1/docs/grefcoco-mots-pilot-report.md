# P1 vs P2 multi-person and small-person pilot

Date: 2026-08-24  
Remote host: `cenara70hx` over Tailscale (NVIDIA CMP 70HX, 8 GB)

## Systems

- **P1:** LISA-7B-v1, 4-bit; SAM image encoder on CPU; maximum 16 generated
  tokens.
- **P2:** BLIP-2 FLAN-T5-XL 8-bit -> Grounding DINO Tiny FP32 -> SAM ViT-H
  FP16. The three stages run in separate processes because the GPU cannot hold
  them concurrently.

No model was fine-tuned on either pilot. Thresholds were frozen at 0.25 for
Grounding DINO boxes and text.

## Pilot 1: gRefCOCO

Official dataset: https://github.com/henghuiding/gRefCOCO  
Paper: https://openaccess.thecvf.com/content/CVPR2023/papers/Liu_GRES_Generalized_Referring_Expression_Segmentation_CVPR_2023_paper.pdf

The fixed seed-20260824 pilot contains 30 expressions:

- 15 multi-target person expressions from `val`
- 10 single-target person expressions in images containing at least two people
  from `testA`
- 5 no-target person expressions from `val`

One expression is used per image. P1 receives the dataset expression followed
by a request for a segmentation mask. P2 receives the same expression through
a VQA question; BLIP-2's answer becomes the Grounding DINO query. The union of
all target-person masks is the principal ground truth.

## Pilot 2: MOTSChallenge small street pedestrians

Official dataset: https://www.vision.rwth-aachen.de/page/mots  
Challenge description: https://motchallenge.net/data/CVPR_2020_MOTS_Challenge/

The fixed seed-20260824 pilot contains 12 labeled training frames, three from
each of the four sequences. Every frame contains at least two pedestrians, the
smallest labeled person is at most 64 pixels tall, and selected frames are at
least 20 frames apart within each sequence. The fixed intent is "all visible
people" because MOTS supplies masks but no referring expressions.

## Metrics

- gIoU: mean per-image union-mask IoU
- cIoU: pooled intersection divided by pooled union
- Dice, precision, and recall
- target-person coverage: fraction of ground-truth person instances for which
  at least 50% of its pixels are covered by the predicted union mask
- no-target accuracy for gRefCOCO
- model compute time and peak VRAM

Target-person coverage is included because union IoU can hide a missed small
person beside a correctly segmented large person. P2 box count is diagnostic
only and is not treated as a primary metric because P1 does not expose boxes.

## Results

### gRefCOCO language-guided segmentation

| Metric | P1: LISA | P2: BLIP-2 -> DINO -> SAM |
|---|---:|---:|
| gIoU | 62.66% | 20.31% |
| cIoU | 74.80% | 4.82% |
| Dice | 68.10% | 21.37% |
| Target-instance coverage >=50% | 90.00% | 6.00% |
| No-target accuracy | 0.00% | 100.00% |
| Mean component inference time | 55.57 s | 1.32 s* |
| Peak VRAM | 5.30 GB | 5.23 GB* |

P1 won 24 of 30 paired examples, P2 won five, and one was tied. P1 was strong
on multi-target expressions (80.13% gIoU and 96.67% instance coverage) and on
selecting one person in a crowd (67.79% gIoU). However, it emitted a mask for
all five no-target expressions, giving 0% no-target accuracy.

P2 correctly returned an empty result for all five no-target expressions, but
its BLIP-2 bridge also returned `no person` for most expressions that did have
a target. Consequently, P2 emitted a mask on only 6.67% of the 30 cases. Its
20.31% overall gIoU includes perfect scores for the five correctly empty cases;
on target cases its group gIoU was only 3.95% for multiple targets and 4.99%
for one target in a crowd. This isolates the main failure upstream of SAM: the
free-form VQA answer is not a reliable grounding query for referring language.

### MOTSChallenge small street pedestrians

| Metric | P1: LISA | P2: BLIP-2 -> DINO -> SAM |
|---|---:|---:|
| gIoU | 83.68% | 87.71% |
| cIoU | 81.89% | 85.00% |
| Dice | 90.80% | 93.09% |
| Target-instance coverage >=50% | 74.92% | 76.27% |
| Mean component inference time | 54.98 s | 8.41 s* |
| Peak VRAM | 5.30 GB | 5.32 GB* |

P2 won nine of 12 paired frames and improved mean IoU by 4.03 percentage
points. Both systems achieved IoU >= 0.50 on every selected frame. P2 was
especially strong when the smallest person was 33--64 pixels tall: 91.41%
gIoU and 82.26% instance coverage, compared with P1's 85.35% and 74.15%.

The conclusion changes for the five frames containing a person no taller than
32 pixels. P2 still had slightly higher gIoU (82.53% versus 81.34%), but P1
covered more individual people (76.00% versus 67.89%). A high union-mask IoU
therefore does not prove that every tiny pedestrian was found.

### Full surveillance test: 60 MOTS frames and 593 people

Date completed: 2026-08-25

The prepared MOTS pool was run in full. It contains 60 labeled frames and 593
visible people. Twenty-four frames contain a person no taller than 32 pixels;
the other 36 contain a smallest person between 33 and 64 pixels. Frames remain
at least 20 frames apart within each video sequence.

The main P1 and P2 systems were not changed. P1 received "Please segment all
people visible in this street scene." P2 received the same intent through
BLIP-2, whose short answer was passed to Grounding DINO and then SAM. A third
diagnostic system, **P2-direct**, removed BLIP-2/Q-Former and sent the fixed
query `person.` directly to Grounding DINO and SAM. P2-direct is an ablation,
not a replacement name for P2.

For every system, one labeled person counts as detected only when the predicted
union mask covers at least 50% of that person's visible ground-truth pixels.
This is the same rule for P1, P2, and P2-direct; DINO box count is not used for
the main comparison.

| Metric | P1: LISA | P2: BLIP-2 -> DINO -> SAM | P2-direct: person -> DINO -> SAM |
|---|---:|---:|---:|
| Labeled people | 593 | 593 | 593 |
| Detected people | 405 | 469 | **488** |
| Missed people | 188 | 124 | **105** |
| Person recall >=50% | 68.30% | 79.09% | **82.29%** |
| gIoU | 85.80% | **90.55%** | 88.66% |
| cIoU | 86.93% | **90.31%** | 89.14% |
| Dice | 92.08% | **94.92%** | 93.75% |
| Pixel precision | 89.77% | **95.89%** | 92.88% |
| Pixel recall | 94.87% | 94.24% | **94.99%** |
| False-positive pixels | 1,364,307 | **607,039** | 952,463 |
| Mean component inference time | 54.55 s | 8.28 s* | 7.65 s* |
| Peak VRAM | 5.30 GB | 5.32 GB* | 3.27 GB* |

P2 had the best mask quality: it achieved 90.55% gIoU, won 47 of 60 paired
frames against P1, and produced fewer false-positive pixels than either other
system. P2-direct detected the most individual people, 488 of 593, but its
extra detections came with lower gIoU and 345,424 more false-positive pixels
than unchanged P2. Removing BLIP-2 therefore increased person recall by 3.20
percentage points but reduced gIoU by 1.89 points. BLIP-2 helped suppress false
positives and improve the union mask in this fixed-intent setting; it did not
maximize the number of people found.

| Person height | Labeled people | P1 recall | P2 recall | P2-direct recall |
|---|---:|---:|---:|---:|
| <=32 px | 25 | **28.00%** | 12.00% | 16.00% |
| 33--64 px | 70 | 11.43% | 37.14% | **52.86%** |
| >64 px | 498 | 78.31% | 88.35% | **89.76%** |

All three systems still perform poorly on truly tiny people. P1 found seven of
25 people no taller than 32 pixels, P2 found three, and P2-direct found four.
This confirms that the strong whole-image IoU scores do not mean that every
distant pedestrian was detected.

`*` P2 time is the sum of BLIP-2, Grounding DINO, and SAM inference; P2-direct
time contains only Grounding DINO and SAM. Both exclude model loading and
swapping. Peak VRAM is the largest single stage because the components were run
serially on the 8 GB GPU.

### What to test next

1. Preserve the original referring expression for grounding instead of relying
   only on BLIP-2's short VQA answer. Compare expression-direct, VQA-only, and
   hybrid/fallback queries on a validation split.
2. Add multi-scale or tiled Grounding DINO inference for people <=32 pixels and
   tune its box/text thresholds on validation data. Report false positives as
   well as per-person recall.
3. Add explicit empty-mask training or refusal calibration to P1, which is the
   clearest weakness exposed by gRefCOCO.
4. Run the already prepared full pool of 150 gRefCOCO expressions. The full
   60-frame MOTS surveillance pool is now complete.

The completed pilot artifacts, the full 60-frame surveillance artifacts, and
every individual overlay are mirrored in the local website. The prepared full
gRefCOCO evaluation pool still contains 150 expressions.

## Interpretation limits

- Thirty language cases and twelve video frames are sufficient for failure
  discovery and website examples, not a final publication claim.
- MOTS frames are sampled from videos, so the temporal-gap rule reduces but does
  not eliminate correlation.
- MOTS has no language annotations; its prompt is synthetic and tests visual
  recall more than language reasoning.
- P2-direct is a fixed-class-query ablation. It does not test VQA and must not
  be reported as a third complete language-guided pipeline.
- P2 time is the sum of component inference only and excludes model load/swap
  overhead. P2-direct time contains only Grounding DINO and SAM.
- COCO imagery is common in model pretraining ecosystems, so this is a practical
  zero-shot comparison rather than proof of completely unseen visual content.
