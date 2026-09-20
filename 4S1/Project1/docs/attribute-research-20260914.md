# Detailed person descriptions: experiment record

## Question and scope

Can an image and a description such as "person wearing a blue hat and a black
jacket" select the correct visible person and produce a mask? This requires
category detection, attribute binding to one instance, selection, and segmentation.
Successful all-person segmentation does not establish this capability.

The progress report #2 records useful results on 60 camouflage images and 60
MOTS frames. Its P2 CamouflageData mean IoU is 72.21%, versus LISA's 59.51%,
but cumulative IoU is lower (53.51% versus 60.56%). These are reported historical
results, not new measurements. ZoomNeXt's separate fine-tuning experiment uses
different data splits, metrics and hardware, preventing a direct ranking here.

## Verified existing failure

The saved 30-expression gRefCOCO pilot produces nonempty P2 masks on just two
requests. Its prompt tells BLIP-2 to answer "no person" when nobody matches;
the raw answers show that it also does this for annotated positive targets.
The empty output happens before detection. The resulting perfect no-target
accuracy is not evidence of calibrated rejection. A colleague's existing
September 9 handoff at `/home/osta/Yolo_World/NOTE_FOR_P2_OWNER.md` independently
documents this issue on the larger 150-expression run and suggests a prompt fix.
This is an existing project finding, not a new invention.

## Experiments

1. Saved LISA-7B-v1 and BLIP-2/DINO/SAM masks: reused as historical controls.
2. Direct expression -> Grounding DINO -> SAM: bypass phrase rewriting.
3. Grounding DINO("person") -> per-candidate BLIP-2 yes/no verification -> SAM:
   NMS 0.5, at most 12 candidates ranked by detector confidence, retain exact "yes".
4. Prompt-fixed BLIP-2 -> DINO -> SAM: remove only the refusal instruction.
5. YOLO-World with the expression as vocabulary -> identical SAM: adapted
   segmentation baseline, not native YOLO-World segmentation.
6. The same category-generated candidates -> Qwen2-VL-2B full-scene numbered-box
   selection -> SAM. The model is already cached remotely. This changes both the
   language model and its context, so it does not isolate scene context as a cause.
7. Highest-confidence category detection -> SAM, without language selection.
   This control checks whether numbered-box prompting merely chooses candidate 0.
   Existing SAM masks are reused only when image and selected boxes match exactly.

Q-Former is the internal learned bridge in the existing BLIP-2 checkpoint. This
project currently passes generated text to Grounding DINO; it does not train a new
Q-Former or pass its latent vectors into DINO. Do not describe the pipeline as a
new feature-fusion architecture without actually implementing and training one.

The first two new detector runs use box/text thresholds 0.25. No thresholds are
tuned against this pilot. Crop verification intentionally tests a simple hypothesis;
it loses scene relationships, can contain overlapping people, and has uncalibrated
yes/no outputs. No match yields an empty mask. Several accepted boxes yield their
union, which is appropriate for plural expressions but does not resolve ambiguity
in a singular expression. The application should expose that ambiguity rather than
silently claim a unique person.

All experiment execution is on cenara70hx. Preserve stage JSONL outputs and
configuration files. New model timings exclude loading and some preprocessing;
they are not complete end-to-end latency. Historical LISA/P2 timings must not be
compared as if measured simultaneously. Memory is peak allocated PyTorch memory
per stage, not full device usage or summed concurrent requirements.

## Evaluation limitations

The reused 30-expression pilot includes original val and testA examples and is
development data. It is not an untouched final test. Report mean IoU, cumulative
IoU, success at IoU >= 0.5, and empty prediction rates by case type. Empty-empty
IoU is 1; therefore report no-target results separately. These masks alone do not
support strict one-to-one instance identification accuracy. COCO-based pretrained
models may have seen the images; dataset and checkpoint overlap needs an audit.
Invalid context-selector responses receive zero request IoU, even if the empty
fallback mask coincides with an empty target. `mask_iou` retains the purely geometric
value, while `response_valid` records the failure. Such failures receive no credit
for no-match accuracy. Four of 30 context-selector responses were invalid.

## Measured findings

The completed pilot has 25 positive targets (10 single-target, 15 multi-target) and
5 no-target expressions. Values below are percentages; none establish performance
on unseen images.

| System | All request IoU | Positive mean IoU | Single-target mean IoU | Valid no-match accuracy |
| --- | ---: | ---: | ---: | ---: |
| LISA-7B-v1, saved masks | 62.66 | 75.19 | 67.79 | 0 |
| Original BLIP-2 prompt, saved masks | 20.31 | 4.37 | 4.99 | 100 |
| Direct expression -> DINO -> SAM | 45.03 | 54.03 | 51.13 | 0 |
| BLIP-2 crop verification | 27.51 | 25.01 | 21.47 | 40 |
| Corrected BLIP-2 prompt -> DINO -> SAM | 43.51 | 52.21 | 48.90 | 0 |
| Expression -> YOLO-World -> SAM | 40.91 | 45.09 | 33.84 | 20 |
| Qwen2-VL full-scene selection | 27.28 | 32.73 | 26.38 | 0 |
| Highest-confidence person, no language selection | 33.38 | 40.06 | 34.67 | 0 |

Removing the refusal clause repairs much of the original P2 prompt failure, but
does not surpass the saved LISA masks. Direct expressions are slightly stronger
than corrected phrase rewriting on this pilot. Neither tested verification method
improves on direct grounding. The context selector selects exactly the same boxes
as the query-independent top-1 control on 18/30 requests, and performs worse overall.
This does not support promoting either verifier as an improved research method.

On the inspected clothing image, direct grounding achieves 56.56% IoU for the
blue-hat/light-shirt person and 88.63% for the brown-shirt person. It produces
72,650 false-positive pixels for the nonexistent blue-hat/black-jacket combination.
The full-scene selector picks the same box for all three prompts, exactly matching
the top-1 control; it does not establish attribute binding. No positive example of
the exact blue-hat/black-jacket combination was validated.

Recorded component times and largest serial-stage allocated memory:

| New system | Mean sum of recorded component seconds | Largest stage GiB |
| --- | ---: | ---: |
| Direct expression | 7.34 | 3.264 |
| Crop verification | 8.73 | 5.314 |
| Corrected BLIP-2 prompt | 8.27 | 5.330 |
| Context selection | 10.37 | 4.412 |
| YOLO-World + SAM | 4.16 | 3.268 |

These are not a fair end-to-end latency ranking: timer boundaries differ and
exclude loading and some preprocessing. Failed/empty predictions remain in the
averages. The raw timers and definitions are in `resources.json`; process RSS is
available only for stages that recorded it. No complete cross-model RAM comparison
is claimed.

The remote artifact audit passed key completeness, metric bounds, reproduction of
the saved LISA/P2 aggregate values, and input/artifact SHA-256 recording. The
arbitrary-image CLI was also executed successfully on the same no-match example;
it reproduced the direct pipeline's 72,650-pixel false-positive mask. Successful
execution is distinct from a correct prediction.

The three custom prompts share one visually inspected COCO image. The blue/white
hat and light-shirt person is annotated instance 2; brown-shirt person is instance
1. The black-jacket query is a visible no-match counterfactual. These are diagnostic
examples, not three independent evaluation images and not evidence about an actual
positive blue-hat/black-jacket example.

## Research contribution assessment

No novelty or universal superiority is established. Candidate generation followed
by language-conditioned selection is already an established direction. A more
specific research hypothesis is to preserve the full expression, verify each
clothing attribute on the same instance, retain scene context for relationships,
and calibrate rejection on separate negative examples. An ablation must compare
full-expression verification, individual-attribute conjunction, scene context,
and rejection calibration. Improvements must survive held-out evaluation with
shared images and masks before being claimed as a contribution.

Relevant primary sources:

- [LISA](https://github.com/JIA-Lab-research/LISA): native image-language segmentation;
  the original training includes referring-expression datasets.
- [ZoomNeXt](https://github.com/lartpang/ZoomNeXt): camouflaged object detection;
  the baseline has no text interface. A language extension is a new adapted system.
- [YOLO-World](https://github.com/AILab-CVC/YOLO-World): open-vocabulary detection;
  the segmentation component must be stated explicitly.
- [RexSeek / HumanRef](https://github.com/IDEA-Research/RexSeek): human-centric
  referring and an existing Grounding DINO + SAM demo. This limits broad novelty claims.
- [Set-of-Mark prompting](https://github.com/microsoft/SoM): numbered visual marks
  are established prior work; the context selector uses a related prompting pattern.
- [Text Augmented Spatial-aware zero-shot referring segmentation](https://arxiv.org/abs/2310.18049):
  related training-free fine-grained image/text matching and spatial reasoning.
- [Referring Expression Counting](https://openaccess.thecvf.com/content/CVPR2024/papers/Dai_Referring_Expression_Counting_CVPR_2024_paper.pdf):
  discusses detection of extra nouns in referring expressions by Grounding DINO.

## Reproduction

Copy `code/scripts/attribute_pilot.py` to `/home/osta/lisa-eval/code/scripts/`.
From `/home/osta/lisa-eval/code` on cenara70hx:

```bash
export HF_HOME=/home/osta/blip2-qformer-eval/hf-cache
export HF_HUB_OFFLINE=1
PY=/home/osta/blip2-qformer-eval/.venv/bin/python
for stage in prepare direct candidates verify masks prompt_fixed score; do
  "$PY" scripts/attribute_pilot.py "$stage" || exit 1
done
```

Do not rerun `prepare` into an existing run with changed inputs or code. Use a fresh
`--out` directory for a new configuration. Add `--custom` and a distinct `--out`
directory for the three diagnostic prompts. Existing artifacts are not final-test
evidence. The script and source-manifest hashes are recorded in protocol.json.

For an arbitrary image, the remote inference entry point is:

```bash
"$PY" scripts/infer_referring.py \
  --image /absolute/path/to/image.jpg \
  --text 'person wearing a blue hat and a black jacket' \
  --method direct --out results/new_query
```

Methods are `direct`, `crop`, and `context`. Use a fresh output directory. This
entry point does not assign accuracy scores without ground truth. Read the saved
mask and decisions together; a nonempty mask does not prove the description matched.
`run_attribute_followups.sh` records the additional benchmark commands, including
the existing YOLO-World backend and the same SAM segmentation stage.
