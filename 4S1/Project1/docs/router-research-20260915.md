# Router experiment — 15 September 2026

Status: frozen confirmation and paired cold-request checks complete.

The user authorized testing a training-free hard-case detector first, then training a meaningful small decision layer if needed. All inference, fitting, and statistical scoring run on cenara70hx. Foundation model weights remain frozen.

## Question and methods

Can a pre-LISA decision save computation while preserving or improving text-conditioned person segmentation? Candidate actions are cached LISA, YOLO-World plus SAM, ZoomNeXt, the intersection or union of the two cheap masks, and an empty mask. The gate reads no LISA output and no ground truth at inference.

The training-free geometry gate uses ZoomNeXt ambiguity and components, or agreement between its mask and YOLO box rectangles. Zoom probabilities are normalized per image, so ambiguity is a heuristic, not calibrated confidence. The language-only training-free control rejects when Qwen presence probability is below 0.5, otherwise runs cached LISA.

The trained primary is an ExtraTrees regressor (120 trees, depth 5, minimum leaf 15) predicting each alternative's IoU gain relative to LISA. Inputs include box geometry and confidence, Zoom geometry, query flags, and frozen Qwen presence scores. This is a trained routing layer, not a new segmentation network. A matched no-Zoom ablation and a separately locked exploratory accuracy candidate test whether the added components are useful.

## Separation of development and confirmation

All 270 previously explored images are explicitly development data, including the former 180-image held-out experiment. The split is 180 fitting images and 90 internal validation images. No refitting on internal validation occurs. The confirmation sample contains 90 new images (30 single target, 30 multiple targets, 30 absent target), excludes historical image IDs, and verifies image hashes. Selection, feature code, and model hashes are locked before confirmation scoring. Confirmation results must not be used for retuning.

These are gRefCOCO testA examples. They assess language-based selection and cannot establish CCTV generalization or absence of foundation-model pretraining overlap.

## Development findings

The geometry-only search covered 408 rules and 21 trained models. No configuration met the joint validation target: positive IoU within one percentage point of cached LISA, balanced quality at least LISA, and a 20% estimated stage-cost reduction. Adding frozen language presence scores improved absent-target rejection, but still did not meet that joint speed target. The locked primary was therefore selected for balanced quality under the positive-IoU constraint, without a speed claim.

On internal validation, cached LISA positive IoU was 71.20%. The primary achieved 70.70% positive IoU and 82.14% absent-target accuracy, calling LISA on 71.11% of cases. These are development numbers only. Most savings arise from early empty-mask decisions, not successfully replacing LISA on positive images.

## Timing and statistical interpretation

Confirmation reports the sum of saved measured model-stage times for the selected route. This excludes model loading, feature extraction, subprocess overhead, and scheduling; it is not measured end-to-end cascade latency. Separate fresh-process requests exercise an early-exit case and a LISA-fallback case, each paired with cached LISA. Those two purposefully selected development cases illustrate branches, not average workload latency.

Primary comparisons against cached LISA use paired bootstrap intervals for positive IoU, balanced score, and stage time, with Bonferroni 98.333% intervals across the three claims. Other candidates and ablations are exploratory. Balanced score is the average of positive mean IoU and absent-target accuracy; it is not positive segmentation accuracy.

## Reproduction

Remote scripts under `/home/osta/lisa-eval/code/scripts`: `prepare_router_dev.py`, `router_development.py`, `train_router.py`, `prepare_router_confirmation.py`, `lock_router_controls.py`, `train_router_ablation.py`, `run_router_confirmation.sh`, `apply_router.py`, `score_router.py`, and `benchmark_router_runtime.py`.

Frozen decisions and models are under `results/router_dev_20260915`. Confirmation masks, audit, and scores are under `results/router_confirm_20260915`. Cold request evidence is under `results/router_runtime_20260915`.

For a new remote image, use `infer_router.py --image ABSOLUTE_PATH --text DESCRIPTION --out NEW_DIRECTORY --method Learned_primary` with `/home/osta/blip2-qformer-eval/.venv/bin/python`. The CLI runs only stages needed by its selected action. GPU must be idle.


## Frozen confirmation results

| Method | Positive mean IoU | Absent-target accuracy | Balanced score | Model-stage seconds/image | LISA calls / 90 |
|---|---:|---:|---:|---:|---:|
| Cached LISA | 73.07% | 0.00% | 36.53% | 13.753 | 90 |
| Training-free Zoom gate | 70.72% | 0.00% | 35.36% | 13.746 | 87 |
| Training-free language gate | 71.55% | 56.67% | 64.11% | 14.150 | 71 |
| Trained primary | 66.94% | 66.67% | 66.80% | 13.496 | 65 |
| Trained accuracy candidate (exploratory) | 67.13% | 70.00% | 68.56% | 12.933 | 60 |
| Trained no-Zoom ablation (exploratory) | 66.94% | 73.33% | 70.14% | 12.991 | 63 |
| YOLO-World + SAM | 39.72% | 6.67% | 23.19% | 4.497 | 0 |
| ZoomNeXt alone | 24.32% | 0.00% | 12.16% | 0.207 | 0 |

The primary failed the intended positive-quality constraint: positive IoU fell by 6.13 percentage points. Its adjusted interval for that difference is [-13.93, 0.00] pp. It improved balanced score by 30.27 pp, adjusted interval [19.27, 40.90] pp, through absent-target rejection. It incorrectly rejected 5 of the 60 positive images. The model-stage time saving was only 0.256 seconds (1.86%); adjusted interval [-1.287, 1.901] seconds includes both slowdown and speedup. This is not evidence of a runtime improvement.

The no-Zoom ablation has identical positive IoU, higher absent-target accuracy, and lower stage cost than the primary on this sample. There is no demonstrated added value from ZoomNeXt in this gate. This comparison is exploratory and does not establish that ZoomNeXt can never help another design.

The training-free language gate preserves positive quality better than the learned gate but still loses 1.52 pp against cached LISA and costs more model time. The training-free geometry gate almost never bypasses LISA and loses 2.35 pp. The small learned layer therefore does not satisfy the proposed joint improvement either.

## Decision

Keep cached LISA as the positive-segmentation baseline. Do not promote this router as an accuracy-and-runtime improvement or a novel invention. This experiment is evidence against the tested Zoom difficulty proxy and small gate, not proof that all training-based approaches are impossible. A next training experiment would need to improve a cheap expert's text-conditioned segmentation itself, or distill a stronger model into a smaller one, rather than only predict which existing weak mask to use. That is a separate experiment requiring new training data and another untouched test set; it was not performed here.

The existing cache optimization remains the demonstrated runtime result: three paired development cases reduced the LISA stage from roughly 45–47 seconds to 13–14 seconds with identical paired outputs. That is an engineering optimization, not a new segmentation method, and does not by itself establish a broad benchmark result.

## Audit and limitations

The confirmation audit passed: 90 unique images, disjoint from the 270 development images, verified image hashes, frozen feature and model hashes, and 720 rendered predictions across eight methods. No confirmation-guided retuning was performed. A Windows line-ending error stopped the shell queue before language inference; the missing stage was resumed without changing the selected methods or data.

Raw local scores: `code/results/router_confirm_20260915/scores/{comparison,paired,per_expression,audit}.json`. Method locks and execution provenance are saved in `code/results/router_dev_20260915`.


## Actual cold-request checks

| Purposefully selected development branch | Cached LISA | Trained primary | Outcome |
|---|---:|---:|---|
| Must fall back to LISA | 41.69 s | 66.66 s | Added filtering slows this request |
| Empty-mask early exit | 40.38 s | 25.45 s | Skipping LISA saves time on this request |

These include subprocess/model loading and mask rendering, measured from the CLI timer after initial Python imports and small-router loading. They are two selected examples, not a representative mean or steady-state throughput result. They verify that both branches execute, but do not overturn the confirmation result: no demonstrated joint positive-accuracy and runtime improvement.
