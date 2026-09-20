# Extended training-free experiment: a locked custom pipeline

15 September 2026. All inference and numerical evaluation ran on cenara70hx through Tailscale. This report formats saved outputs; it does not recompute predictions or scores.

## Main result

The locked primary improves the equal-weight balanced score against all three baselines, with all three adjusted intervals above zero. The large gain comes mainly from rejecting absent targets. Positive-mask IoU is numerically higher than LISA, but its interval still spans zero.

180 project-held-out testA images. Primary positive IoU difference vs LISA: +0.94 points (95% CI -0.12 to +1.92). A reliable positive-IoU improvement is not established by the multiplicity-adjusted interval. New to project evaluation does not mean absent from model pretraining; this does not establish CCTV generalization.

The primary method was selected before inference on these 180 images. The other custom variants are exploratory ablations; selecting a new winner from this table would require another untouched test.

| Method | Positive IoU (%) | No-target accuracy (%) | Balanced (%) | All-case IoU (%) |
|---|---:|---:|---:|---:|
| LISA | 73.50 | 0.00 | 36.75 | 49.00 |
| YOLO_World_SAM | 43.39 | 18.33 | 30.86 | 35.04 |
| ZoomNeXt_vision_only | 21.55 | 0.00 | 10.78 | 14.37 |
| Custom_primary | 74.44 | 56.67 | 65.56 | 68.52 |
| Custom_aggressive | 73.44 | 65.00 | 69.22 | 70.62 |
| LISA_custom_boundary | 74.44 | 0.00 | 37.22 | 49.63 |
| LISA_union | 74.22 | 0.00 | 37.11 | 49.48 |
| LISA_guided | 73.87 | 3.33 | 38.60 | 50.36 |
| LISA_verifier_only | 73.50 | 56.67 | 65.09 | 67.89 |

Balanced score is the unweighted mean of positive-target mean IoU and valid empty-mask accuracy on no-target cases. All-case IoU depends on this set’s 120:60 composition and is not a substitute for positive-target performance. Invalid responses receive zero credit.

## Paired uncertainty against all three baselines

| Baseline | Positive difference (points) | Adjusted interval | Balanced difference (points) | Adjusted interval |
|---|---:|---|---:|---|
| LISA | +0.94 | [-0.61, +2.21] | +28.80 | [+20.43, +37.11] |
| YOLO_World_SAM | +31.06 | [+22.27, +39.96] | +34.70 | [+24.05, +45.42] |
| ZoomNeXt_vision_only | +52.89 | [+44.04, +61.14] | +54.78 | [+45.16, +64.05] |

Stratified paired image bootstrap, 10,000 draws. The 99.167% Bonferroni intervals adjust for six primary comparisons: two endpoints against three baselines. A strictly positive lower bound supports an improvement under this analysis; an interval spanning zero does not. Unadjusted 95% intervals and exploratory comparisons are available in the evidence JSON.

## What the custom pipeline does

The deployed primary retains LISA for expression-conditioned selection. Grounding DINO proposes people and SAM supplies candidate masks. A candidate is accepted when at least 50% of its pixels overlap LISA. If accepted candidates cover at least 80% of LISA, the method trims LISA outside their support dilated with a 15×15 elliptical kernel, then unions the accepted masks. Otherwise it uses their union with LISA. Finally, a frozen Qwen2-VL verifier examining the full scene with the LISA bounding box suppresses the output when its yes score is below 0.4. This score is a model token likelihood, not a calibrated probability of correctness.

No model weights were updated. Thresholds and composition were selected using labeled development data, so training-free does not mean tuning-free. This is a frozen-model ensemble that requires LISA at deployment. ZoomNeXt is evaluated as a vision-only reference; YOLO-World uses SAM for masks.

## Development search and selection

Development used 90 expressions. The exported search contains 1,607 configuration evaluations; controls and compositions can repeat, so this is not a count of distinct models. The primary maximizes balanced score subject to positive IoU no lower than LISA and zero positive verifier rejection on development. Ties favor positive IoU, then fewer stages. These development constraints do not guarantee the same behavior on new images.

| Search family | Configuration evaluations |
|---|---:|
| geometry_sweep | 43 |
| custom_boundary_sweep | 48 |
| guided_sweep | 36 |
| clip_sweep | 54 |
| gate_sweep | 270 |
| candidate_sweep | 64 |
| composition_sweep | 1092 |

The search included morphology, SAM agreement, custom boundary trimming and distance blending, grayscale guided filtering, CLIP scoring, Qwen2-VL scene/bounding-box/candidate verification, BLIP-2 verification, RexSeek object selection, explicit-person clause decomposition, conservative selection correction, and verifier combinations. RexSeek ran with NF4 quantization of language-model linear layers while excluding vision/projector/head modules; its result must not be represented as full-precision upstream performance. Candidate-based corrections did not meet the development inclusion rule. Raw trials and availability failures remain downloadable.

## Protocol and limits

The method was frozen at 2026-09-14T18:42:53Z. The test contains 180 distinct testA images: 120 positive and 60 no-target. The audit verifies image hashes, exclusion of historical project images, development separation, unchanged manifest and frozen method provenance. Public pretrained models may have encountered COCO; project-held-out is not pretraining-clean. This language-selection experiment establishes no fixed-camera CCTV generalization. No drone imagery is part of this experiment.

Coverage diagnostics count whether at least 50% of each visible person’s ground-truth pixels are predicted. They are not one-to-one instance matching. The separate development candidate audit uses maximum-cardinality one-to-one IoU matching to assess proposal availability; it does not measure deployed language selection. Model-stage timings are not complete deployment latency. The arbitrary-image CLI records its own end-to-end time including model loading.

## Reproduce and inspect

Run on the remote host from /home/osta/lisa-eval/code; supply an existing image path and a new output directory. This command does not require ground truth.

```bash
/home/osta/blip2-qformer-eval/.venv/bin/python scripts/infer_extended.py \
  --image /absolute/path/image.jpg --text "the person in a blue hat" \
  --out /absolute/path/new-output
```

## Model access and proposal diagnostics

SAM 3 was not evaluated: the actual weight-access probe returned HTTP 401 / GatedRepoError. It has no measured score in this study. RexSeek access succeeded and its quantized development experiments completed. Failed access is not evidence that a model performs poorly.

| IoU | Matched development targets | Recall (%) |
|---|---:|---:|
| 0.5 | 105/108 | 97.22 |
| 0.75 | 101/108 | 93.52 |

These are oracle proposal-availability diagnostics using development annotations. They suggest selection remains a bottleneck but do not establish that the deployed selector finds those matches.

## Research foundations

The custom composition draws on frozen expression segmentation, proposal masks, visual verification and image-guided refinement. It is an empirical engineering combination; this study makes no novelty claim.

- [RexSeek official implementation](https://github.com/IDEA-Research/RexSeek)
- [RexSeek paper](https://arxiv.org/html/2503.08507v1)
- [Guided Image Filtering](https://people.csail.mit.edu/kaiming/eccv10/index.html)

An end-to-end smoke run completed in 106.9 seconds on the recorded development image, including model loading. Expression: “middle woman”. Valid response: True. This single run is a deployment check, not a throughput benchmark.

[Deployment record](../extended-assets/deployment_result.json) · [Overlay](../extended-assets/deployment_overlay.png)

- [comparison.json](../extended-assets/comparison.json)
- [paired.json](../extended-assets/paired.json)
- [per_expression.json](../extended-assets/per_expression.json)
- [audit.json](../extended-assets/audit.json)
- [method_lock.json](../extended-assets/method_lock.json)
- [selection_lock.json](../extended-assets/selection_lock.json)
- [development.json](../extended-assets/development.json)
- [availability.json](../extended-assets/availability.json)
- [environment_audit.json](../extended-assets/environment_audit.json)
- [shape_implementation_audit.json](../extended-assets/shape_implementation_audit.json)
- [candidate_matching_diagnostic.json](../extended-assets/candidate_matching_diagnostic.json)
- [locked_dev_reproduction.json](../extended-assets/locked_dev_reproduction.json)
- [rexseek_quantization_audit.json](../extended-assets/rexseek_quantization_audit.json)
- [rexseek_loading.json](../extended-assets/rexseek_loading.json)
