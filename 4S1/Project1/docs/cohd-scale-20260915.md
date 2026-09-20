# CoHD small-person scale study — 15 September 2026

## What we tested

Continued the original CoHD baseline with no new weight training. The primary **Scale 704 + guard** uses AMP float16, 704-square input, a bilinear adapter to the decoder's learned spatial-projection grid, and a small-component shape guard. A locked 768-resolution variant is secondary. These are experimental inference adaptations, not a newly established architecture or a replacement silently installed as default.

The original model has fixed spatial projection lengths 900/3600/14400. Simply changing image size failed. The adapter resamples the input to those projection MLPs while retaining higher-resolution attention maps elsewhere. Original model/checkpoint files were not edited.

The guard keeps components with >=4096 pixels, or height >=20 original-image pixels and width/height <=1.2. It can remove valid crouching, wide or fragmented people, and these absolute-size rules may not transfer to other cameras. It is not a learned semantic person classifier.

## Development and locked confirmation

Development used 24 explicitly reused CCTV frames (12 MOTS / 12 VIRAT). We tested AMP, several sizes, four overlapping tiles, full image plus top/central crops, and four shape-filter configurations. AMP480 alone reduced runtime but did not recover people; tiles and crops had quality/false-positive trade-offs. Full details remain in the development summaries.

The primary and secondary were locked before confirmation. Confirmation contains 120 previously unscored frames: 60 MOTS20-02 native human-mask frames and 60 PersonPath22/VIRAT courtyard native-box frames. Their cameras are already explored; new frame hashes do not make this an unseen-camera test. Nearby frames and repeated people are correlated.

## CCTV confirmation results

| Method | MOTS mean IoU | MOTS coverage >=50% | MOTS small coverage | VIRAT matched / GT | VIRAT FP | VIRAT <64px matched / GT | Mean seconds/image |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original CoHD | 65.16% | 62.39% | 37.50% (16 observations) | 10 / 635 | 150 | 1 / 548 | 0.6541 |
| Scale 704 + guard | 70.71% | 77.32% | 43.75% (16 observations) | 48 / 635 | 120 | 24 / 548 | 0.5934 |
| Scale 768 + guard | 69.73% | 81.41% | 31.25% (16 observations) | 70 / 635 | 150 | 42 / 548 | 0.6862 |


MOTS coverage counts a person when >=50% of their native mask is covered; it is not one-to-one detector AP. VIRAT uses the pre-existing connected-component mask-to-box adapter and Hungarian IoU>=0.5 matching with ignore handling; it is not official tracking/native detection AP. Small means original-image height <64 pixels. Per-size results under32/32to63/64plus are in analysis.json. Improved recall must still be read alongside its absolute level and false positives.

## Runtime and primary criteria

The mean full-image request includes loading the image, preprocessing, text, all inference passes, coordinate restoration and shape filtering. It excludes one-time model initialization, scoring and visualization. Paired ordering rotates after per-variant warm-up. Every variant uses the same CMP70HX GPU and PyTorch environment; no cached image features.

Primary acceptance checks (true/false): `{"runtime_pass": true, "mots_iou_preserved": true, "mots_fp_controlled": true, "virat_fp_controlled": true, "mots_small_improved": true, "virat_small_improved": true, "all_primary_cctv_criteria_pass": true}`.

These are pilot acceptance criteria, not statistical proof of generalization. Timing bootstrap intervals describe within-run request variation only. See analysis.json for per-domain metrics and uncertainty. Do not use a faster GPU-only substage as full request latency.

## Hat, clothing and absent-target prompts

| Method | Hat mask IoU (12 images) | Clothing mask IoU (12 images) | Correct absence (8 images) | Mean seconds/image |
|---|---:|---:|---:|---:|
| Original CoHD | 71.52% | 85.49% | 3 / 8 | 0.6404 |
| Scale 704 + guard | 70.74% | 83.77% | 2 / 8 | 0.5774 |
| Scale 768 + guard | 69.44% | 79.45% | 2 / 8 | 0.6702 |


**Descriptive-language accuracy did not improve.** The primary hat IoU is 70.74% versus original 71.52%; it covers 7/51 distractor people versus 3/51, while correctly returning empty on 2/8 absent cases versus 3/8. More target coverage came with more incorrect-person coverage. The CCTV acceptance result must not be described as a general language-segmentation upgrade.

This is a 32-image **reused gRefCOCO diagnostic**, selected before predictions: 12 native hat/cap descriptions, 12 clothing descriptions and 8 absent-target descriptions, each on a distinct image with multiple annotated people. Native human expressions and COCO person masks are used. Zero current fine-tuning was performed. This is not fresh held-out language evidence and not a claim about reading a tiny hat in CCTV. Target and distractor coverage are saved separately in analysis.json; a better person mask is not automatically correct attribute binding.

## Evidence, reproducibility and limitations

The 24 original development masks reproduced the historical masks: 24/24 exact. New confirmation/development hash overlap: 0. Language images overlapping official gRefCOCO train: 0; foundation pretraining overlap is not ruled out.

Saved outputs include every mask and per-image score, all per-image request timings, failed direct-resize controls, shape-rule sweeps, locked manifests, source snapshots, and fixed-position comparisons. CCTV examples use 25/50/75% positions per source; language examples use first/middle per group. The cyan zoom uses GT only to show small targets after evaluation; GT never chooses inference crops.

Preserve Original as the default until broader camera and language validation. No additional CCTV attribute labels were invented. Daytime fixed-camera evidence does not establish night, arbitrary-camera or long descriptive-relation performance.

## Run on cenara70hx

```bash
/home/osta/lisa-eval/released-models/.venv/bin/python scripts/infer_cohd_scale.py --image /absolute/image.jpg --text "the person wearing a hat" --method scale704_guard --out /absolute/new_output
```

This command accepts any text but that alone does not guarantee it selects the right person. Use `--method original` for the preserved baseline. Existing output folders are never overwritten.

## Sources

- [CoHD official code](https://github.com/RobertLuo1/CoHD)
- [Slicing Aided Hyper Inference](https://arxiv.org/abs/2202.06934): established motivation for crop inference, not a novelty claim for this work.
- [PyTorch mixed precision](https://docs.pytorch.org/docs/stable/notes/amp_examples.html)
