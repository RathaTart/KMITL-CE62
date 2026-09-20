# Training-free pipeline study

Research date: 14 September 2026. This continues the user's instruction to test improvements without training or updating model weights. All inference, calibration, and scoring run on cenara70hx. No optimizer, learned adapter, LoRA, or gradient update is used in this study.

## Current research and design choices

| Source | Relevant idea | Use in this study |
|---|---|---|
| [HybridGL, CVPR 2025](https://arxiv.org/abs/2504.00356), [official code](https://github.com/fhgyuanshen/HybridGL) | Combine local candidate detail with global context and spatial guidance | A simplified frozen-CLIP candidate selector compares masked person crops with the full image retaining a sharp candidate and blurred background. It also uses explicit horizontal position scores. |
| [RESAnything, NeurIPS 2025](https://suikei-wang.github.io/RESAnything/) | Attribute-oriented descriptions and proposal selection | Keep clothing attributes in the expression. Split conjunctions only when they clearly introduce another person; do not turn “black jacket and blue hat” into unrelated target clauses. We do not reproduce the full MLLM captioning method. |
| [GeoSelect, July 2026 preprint](https://arxiv.org/abs/2607.03869) | Execute inspectable geometric operations instead of relying entirely on embedding similarity | Use simple left/right/center coordinate bonuses and log each operation. This is a small adaptation to person images, not GeoSelect's typed spatial program executor or a replication of its aerial-image results. |
| [SAMRefiner, ICLR 2025](https://arxiv.org/abs/2502.06756) | Coarse-mask refinement with reliable prompting and multiple-object handling | Keep a semantic reference mask and permit a proposal union to replace it only when agreement is high. The actual implementation is a project heuristic, not SAMRefiner. |

[Tarot-SAM3](https://arxiv.org/abs/2604.07916) appeared in the recent search but was withdrawn on 4 August 2026, with its authors stating that substantial revision was needed. Its reported performance is not used as supporting evidence or as the basis of a claimed reproduction.

The feature extractor is the existing frozen CLIP ViT-L/14 checkpoint. HybridGL itself uses modified feature extraction and additional components; simply averaging standard CLIP image similarities is not equivalent to that published method. This study tests the underlying design idea under our existing environment, and must be labeled accordingly.

## New evaluation data

The locked project subset contains 60 unique gRefCOCO images, all from official **testA**: 20 single-person references, 20 multi-person references, and 20 no-target references. Every image contains at least two annotated non-crowd people. Positive targets must all be person annotations. Negative expressions must begin with an explicit person subject; original expressions and annotations remain unchanged.

Historical manifests from the LISA and YOLO project result trees excluded 300 image IDs. Selected image hashes were also checked against available historical images. The manifest records original image IDs, annotation IDs, expressions, per-image hashes, and official split. This is new to our project experiments; foundation-model training overlap with COCO remains possible. It is a project subset score, not an official full-testA benchmark score.

The initial attempt to sample all categories from official val found no eligible person-single references in the installed annotation file. Before any prediction or dataset lock, selection was changed to testA for all three groups. No split mixing or score-based selection was used.

The old 30-expression pilot is used only to select scalar rules. All previously explored 150 images remain development/diagnostic data and are excluded from the new evaluation. The sampling seed is 2026091402. Details are saved in `results/training_free_fresh_20260914/selection_lock.json`.

## Methods and controls

1. **LISA baseline:** image and complete original expression, followed by “Please output segmentation mask.” LISA-7B-v1 uses NF4 4-bit language weights, with its segmentation projection preserved and SAM mask head in fp32. The new run uses the SAM image encoder on GPU in fp16; every LISA-derived method uses these same saved baseline masks.
2. **Enclosed-hole filling:** fill background connected components that do not reach an image border. This has no model weights or optimized thresholds. It can repair segmentation holes but cannot understand a description or reliably reject an absent person.
3. **Proposal-agreement refinement:** Grounding DINO detects generic person candidates at box/text thresholds 0.25, followed by NMS at 0.5 and a maximum of 12 boxes. Frozen SAM ViT-H supplies each candidate's mask. Select candidates having at least 60% of their area inside the LISA mask. Replace the LISA mask with their union only if union/LISA IoU exceeds a development-selected threshold; otherwise retain LISA. Fill enclosed holes in either case.
4. **Global/local CLIP selector:** score each candidate's isolated crop and full-image context using frozen CLIP. Average the two similarities. For explicit left/right/center descriptions, apply a coordinate bonus of maximum order 0.04. Relative constructions such as “left of” are left unexecuted and logged. Explicit person conjunctions select a union of clause matches; simple plural phrases allow candidates within 0.015 of the best score. No target count or GT metadata enters inference.
5. **YOLO-World + SAM control:** existing YOLO-World checkpoint, original expression as its vocabulary, confidence 0.05, same SAM checkpoint. Fresh predictions on the same 60 expressions.
6. **ZoomNeXt control:** existing person-finetuned EffB1 checkpoint with its native multi-scale image input, min/max probability normalization and 0.5 threshold. Vision-only: it cannot follow the expression and is not a fair test of native camouflage superiority.

CLIP's selection considers local/hybrid/spatial modes and similarity floors 0, 0.20, 0.25, and 0.30 on the historical development set. It chooses by overall request mean IoU. The selected mode is spatial, with floor 0.0; therefore it does not acquire an effective confidence-based no-match mechanism. Its development overall mean IoU is 41.24%, which does not surpass LISA. The method is retained as a controlled test of language/context selection.

Proposal agreement checks thresholds 0.75, 0.85, 0.95 and a fill-only fallback. Development selects 0.75, with positive mean IoU 75.50%, versus LISA 75.19% and hole filling 75.32%. These are small development differences, not evidence of a final-test win. Both method locks are written before scoring the new evaluation data.

## Evaluation and reproducibility

Score positive mean IoU, overall mean IoU, cumulative IoU, no-target rejection, invalid-response rate, and single/multiple groups. A missing LISA segmentation token without a clear rejection phrase is treated as invalid rather than rewarded as a correct empty mask. Paired bootstrap intervals use 5,000 samples over unique positive-image pairs.

Also report visible target-person coverage and distractor-person coverage using all non-crowd person annotations. Coverage means at least 50% of that person's visible GT mask is predicted. This is an explanatory metric, **not** strict one-to-one instance matching or a replacement for mask IoU.

The GPU is shared. An initial smoke attempt collided with another task's SAM process and ran out of memory during loading; that failed run produced no scored prediction. After the other process finished, the identical smoke run completed successfully. Subsequent foundation model stages run serially and wait for GPU availability.

Reproduction entry: `code/scripts/run_training_free_study.sh`. Supporting scripts: `prepare_training_free_eval.py`, `global_local_selector.py`, `proposal_agreement.py`, and `score_training_free_fresh.py`. Final metrics must be read from the completed `results/training_free_fresh_20260914/scores` artifacts; do not substitute development scores.

## Completed fresh evaluation

All 60 expressions completed on the remote host. The scorer's audit passed: 60 unique image hashes, official testA throughout, exclusion of 300 historical image IDs, matching development method locks, correct mask dimensions, and no newly trained weights. All LISA responses were valid under the recorded rule. Values below are percentages.

| System | Positive mean IoU (40) | Single (20) | Multiple (20) | Overall mean IoU (60) | No-target rejection (20) |
|---|---:|---:|---:|---:|---:|
| LISA | 76.47 | 80.26 | 72.68 | 50.98 | 0.00 |
| LISA + enclosed-hole filling | 76.56 | 80.28 | 72.83 | 51.04 | 0.00 |
| LISA + proposal agreement + filling | **77.09** | **81.00** | **73.18** | **51.39** | 0.00 |
| Frozen CLIP global/local + spatial | 53.05 | 61.89 | 44.21 | 35.37 | 0.00 |
| YOLO-World expression + SAM | 49.67 | 35.01 | 64.34 | 36.45 | 10.00 |
| ZoomNeXt EffB1, vision only | 21.67 | 15.35 | 27.99 | 14.44 | 0.00 |

The prespecified proposal-agreement method improves positive mean IoU by **0.623 percentage points**, with a paired 95% bootstrap interval of **−0.101 to +1.385 points**. It improves 23 positive images and worsens 17. This is a small numerical gain, **not conclusive evidence of a reliable improvement over LISA**. Enclosed-hole filling alone gains 0.089 points, with interval −0.186 to +0.332, also inconclusive.

Positive cumulative IoU rises from 78.35% to 78.68%, but cumulative IoU across all requests decreases slightly, from 61.68% to 61.63%. Therefore the proposed method does not win every aggregate metric. It retains LISA at inference and does not demonstrate an end-to-end speed improvement.

All LISA-derived variants have the same visible target-person coverage (56/68, 82.35%) and the same distractor-person coverage on positive requests (8.28%). The gain is boundary/region refinement, not evidence of improved identity selection. Both LISA and the proposed refinement falsely produce nonempty masks on all 20 no-target expressions. YOLO/SAM rejects 2/20; its higher rejection rate here does not offset its lower positive IoU.

ZoomNeXt is a vision-only control in this language test. These numbers cannot establish broad superiority over its native camouflage task, or performance on fixed-camera CCTV. The 60-image sample is small and specific; larger separately locked evaluation is needed before a strong superiority claim.

## Candidate diagnostic and next research priority

An additional **offline GT-only diagnostic** examined the frozen generic-person proposal pool. Of 68 annotated targets, 67 have an individual SAM candidate with mask IoU at least 0.5. All 68 have a candidate box with at least 0.5 IoU against the visible GT bounding box. The mean best candidate-mask IoU is 87.70%. These independent best matches may reuse a candidate and are not one-to-one detection AP/recall or a deployable oracle system.

For 29 targets, a good SAM candidate exists but the CLIP-selected union covers less than half of that person's mask. This supports prioritizing **candidate selection and explicit rejection** for the next language experiment. It does not establish that candidate recall is sufficient on difficult CCTV scenes; small-person tiling remains a separate surveillance hypothesis.

`diagnose_training_free_candidates.py` writes this diagnostic without changing predictions or method locks. Its first attempt hit a NumPy scalar JSON-serialization error; converting the diagnostic box-IoU scalar to a Python float fixed serialization. The completed inference and primary scorer were unaffected. The original and corrected diagnostic source are retained in protocol artifacts.

Do not adjust the method on these 60 images and call them untouched again. The next CCTV work follows the user's fixed-camera scope, with no drone imagery in present or future experiments. Dataset and architecture choices are recorded in `docs/surveillance-research-roadmap-20260914.md`.
