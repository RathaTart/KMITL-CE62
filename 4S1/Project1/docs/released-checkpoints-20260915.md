# Released SSP-SAM and CoHD-Tiny evaluation — 15 September 2026

Status: both released checkpoints completed on all 90 images; final masks, scores, and precision diagnostics saved.

## Purpose

Test the authors' released gRefCOCO checkpoints as alternatives to cached LISA, before committing to additional training. No model fitting or threshold selection is performed in this experiment.

## Models and reproducibility

- SSP-SAM-224: [official code](https://github.com/WayneTomas/SSP-SAM), [released weights](https://huggingface.co/wayneicloud/SSP-SAM). Uses the 224-pixel CLIP Surgery model and the gRefCOCO 224 checkpoint. The repository identifies the paper as TCSVT 2025; the arXiv release appeared in March 2026.
- CoHD-Tiny: [official code](https://github.com/RobertLuo1/CoHD), [released Swin-Tiny checkpoint](https://huggingface.co/RobertLuo1/CoHD/blob/main/CoHD_grefcoco_swin_tiny.pth), ICCV 2025.
- LISA: saved cached-LISA outputs from exactly the same 90 images, evaluated on the same remote GPU. These times are from the preceding run, not an interleaved benchmark.

All inference and scoring run on cenara70hx, NVIDIA CMP 70HX with 8 GB VRAM. New repositories and dependencies are isolated under `/home/osta/lisa-eval/released-models`. Existing model repositories and checkpoints are preserved. Downloaded model files are checked against their Hugging Face SHA256 records. Repository commits, checkpoint revisions, input manifest hash, precision, and scripts are recorded with the results.

## Evaluation protocol

The 90-image router confirmation set is reused as an exploratory checkpoint comparison: 30 single-target, 30 multiple-target, and 30 absent-target examples. It is no longer a new untouched confirmation set. Predictions use only image and expression; ground truth is read separately by the scorer.

Metrics separate positive mean IoU from absent-target accuracy. Balanced score is their arithmetic mean and must not be interpreted as positive segmentation accuracy. Paired bootstrap intervals are exploratory. The model predictions are mapped to original image resolution for the common mask metric; this differs from paper-native evaluation spaces.

Both new checkpoints were trained for gRefCOCO, while the current LISA checkpoint was not comparably fine-tuned. Therefore differences assess these deployed checkpoints, not architecture alone. Training overlap from foundation pretraining and auxiliary datasets is not ruled out. No CCTV generalization claim is made.

## Implementation details affecting interpretation

SSP-SAM's released dataset implementation computes or loads cached SAM image embeddings outside the prompt-model forward call. Our timed model stages include a fresh SAM image-encoder pass for each image plus the prompt/decoder forward. Input and output transformations follow the source: 224-pixel letterboxed CLIP image, 1024-pixel longest-side SAM preprocessing, native 512-pixel padded prediction, threshold at sigmoid 0.5, and the paper's under-50-native-pixel no-target rule. The mask is unpadded and restored to original coordinates. All stored weights remain float32. CUDA automatic mixed precision is enabled only during SAM image encoding; the prompt model runs in float32. This setting was checked against full float32 on three images (0, 0, and 1 differing output pixels). The frozen image encoder is checked for equality with the original SAM weights before conversion. As in upstream test.py, released CLIP Surgery weights are loaded separately and encoder.* entries from the task checkpoint are excluded; all remaining missing or unexpected keys are checked.

CoHD-Tiny uses the official 480-pixel square input, BERT tokenization, mask-class argmax and no-target-class argmax. A no-target prediction produces an empty output mask. The full model checkpoint loads strictly, including BERT. Because the server lacks a CUDA compiler toolkit, the model uses the authors' provided PyTorch deformable-attention fallback on the GPU. Its runtime is specific to that backend. Model computation is float32.

Model-stage times synchronize the GPU. Per-request timings additionally include image loading, preprocessing and output-mask saving; one-time model loading is reported separately. Neither metric includes checkpoint downloads or environment installation. No published millisecond figure is treated as a prediction for this machine.

## Reproduction

Project scripts under `code/scripts`: `download_released_models.py`, `download_released_sam.py`, `lock_released_eval.py`, `run_released_cohd.py`, `run_released_ssp.py`, `score_released_models.py`, `render_released_examples.py`.

Run inference with `/home/osta/lisa-eval/released-models/.venv/bin/python` on the remote host, one model at a time. Results live in `/home/osta/lisa-eval/code/results/released_checkpoints_20260915`. Preserve the original result directory; use a new `--out` directory for a rerun.


## Results

| Checkpoint | Positive mean IoU (60) | No-target accuracy (30) | Single-target IoU | Multiple-target IoU | Mean model time / image | Mean request time / image |
|---|---:|---:|---:|---:|---:|---:|
| Cached LISA | 73.07% | 0.00% | 73.24% | 72.89% | 13.753 s | Not measured in this run |
| SSP-SAM-224, corrected AMP | 75.51% | 33.33% | 78.79% | 72.24% | 5.378 s | 5.417 s |
| CoHD-Tiny | 78.01% | 20.00% | 79.05% | 76.98% | 0.637 s | 0.646 s |

All three methods produced nonempty masks on all 60 positive examples. SSP-SAM correctly rejected 10/30 absent examples; CoHD rejected 6/30. Neither checkpoint solves absent-person rejection reliably.

CoHD has the strongest observed positive-segmentation result and is about 21.6 times faster than the saved cached-LISA model-stage baseline. SSP-SAM is about 2.6 times faster, with higher overall balanced quality (54.42%, compared with CoHD 49.01% and LISA 36.53%) because its absent-target accuracy is higher.

The positive-IoU differences versus LISA are +4.95 percentage points for CoHD and +2.45 pp for SSP-SAM. Their exploratory paired 95% bootstrap intervals are [-0.58, +10.83] pp and [-4.38, +9.42] pp respectively. Both include zero, so this small reused set does not establish a statistically clear positive-accuracy gain. The observed speed difference is large, but the baseline timings were saved from the previous run on the same GPU rather than interleaved with these runs.

## Precision correction and validation

The initial whole-SAM half conversion produced an anomalously low 12.69% positive IoU. It is archived under `initial_half_precision` and `SSP_SAM_224`, and is excluded from the final released-checkpoint comparison. Same-model diagnostics found a mean absolute image-feature difference of 0.09277 and mean mask-logit difference of 2.402 against full float32. Keeping weights float32 and using autocast only inside image encoding reduced those differences to 0.00006348 and 0.001509 on the diagnostic image. Full-float32 versus AMP checks on three inputs differed by 0, 0, and 1 output pixel. This validates the correction on those inputs, not universal bitwise equivalence.

The precision addendum was recorded before scoring the corrected full run. Checkpoints, expressions, images, architecture, and mask thresholds were unchanged. The corrected method is named `SSP_SAM_224_AMP` in machine-readable results. An unrelated GPU job caused a temporary memory conflict; it was allowed to finish before the corrected run resumed. No other user's job was interrupted.

The final audit verified 90 predictions per method, unique keys, output hashes, and original-resolution mask shapes. Checkpoint loads were checked for missing/unexpected keys. Example overlays use the first manifest example from each case type, selected without considering scores; visual inspection confirms masks are aligned in original coordinates.

## Decision

**Prioritize CoHD-Tiny as the next practical baseline.** It offers the best observed positive IoU with the lowest measured runtime here. Keep SSP-SAM as an additional comparison, particularly for no-target behavior. Evaluate on a larger independently reserved set before claiming general superiority; use a separately grouped fixed-camera dataset for any CCTV claim. Running these published checkpoints is a baseline improvement, not a new research invention.

Raw final results are in `code/results/released_checkpoints_20260915`: `comparison.json`, `paired.json`, `per_expression.json`, `audit.json`, `protocol_lock.json`, and `precision_addendum.json`. Per-model folders contain every mask, per-image timing row, and provenance. `examples.png` shows saved evidence; initial failed precision results remain separately archived.
