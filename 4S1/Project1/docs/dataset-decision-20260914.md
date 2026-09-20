# Dataset decision for the training-free study

Decision: use **gRefCOCO, a documented person-focused subset, as the primary segmentation benchmark**. Use HumanRef attribute/position/interaction/rejection subsets as a secondary person-selection benchmark. Do not change the primary dataset in response to which method wins.

The unit of evaluation is one image plus one supplied referring expression, producing a mask of all matching people (or an empty mask). This is not image retrieval over a gallery.

## Why gRefCOCO is primary

The [official GRES project](https://henghuiding.com/GRES/) supports single-target, multi-target, and no-target segmentation with existing target annotations. The [official dataset/API](https://github.com/henghuiding/gRefCOCO) supplies references linked to COCO images and instance annotations. This matches our output and permits pixel-level mask evaluation without generating new ground truth using our own segmentation model. The [2026 GREx project](https://henghuiding.com/GREx/) retains gRefCOCO as its generalized referring dataset; pin and record the downloaded annotation version rather than silently mixing revisions.

The person-only subset is our project subset, not a new official benchmark. Positive references must target only person-category annotations, and their masks must preserve the original instance annotations. Negative expressions must actually refer to a person who is absent; do not admit unrelated food/furniture expressions merely because they have an empty target. Document any annotation-only eligibility review before inspecting model performance. Retain exact original expressions rather than rewriting them to help a particular model.

## Why HumanRef is secondary

[HumanRef](https://github.com/IDEA-Research/RexSeek) directly targets person attributes, positions, interactions, reasoning, multiple matches, and rejection, making it a strong check on language-based person selection. However, its [paper, section 3.5](https://arxiv.org/html/2503.08507v1#S3.SS5) states that benchmark masks are generated with SAM2 from ground-truth boxes. These are useful supplementary masks but should not be treated as independently hand-drawn pixel boundaries when judging SAM-based refiners. Report its official instance-matching metrics and rejection separately from gRefCOCO mask IoU. Celebrity recognition is outside this clothing-description study.

RefCOCOg is useful for longer single-object descriptions, but does not by itself cover the multiple/no-match behavior required here. Its [official API](https://github.com/lichengunc/refer) recommends the UMD split for image-disjoint train/validation/test data. It is not necessary to add it to the first primary experiment.

## Fixed evaluation policy

1. Treat all 150 images already used in this project as explored development/diagnostic data. The previous 120-image reservation is no longer an untouched test.
2. Select new person-focused development and evaluation examples from official splits, exclude every previously inspected image ID and image hash from the new final evaluation, and save the complete manifest and annotation hashes before new model comparisons.
3. Keep official split identities visible and score them separately. Do not silently merge val/testA/testB into an official benchmark score. The final subset size and eligible no-target pool must be audited before claiming a locked new manifest; this decision document does not claim that selection has already happened.
4. Use development examples to choose training-free rules and thresholds. No optimizer or model-weight updates. Freeze the rule before the new final evaluation and compare all systems on exactly the same image/expression pairs.
5. Report positive-target mean IoU, cumulative IoU, one-to-one instance selection quality, and no-target rejection separately; stratify single versus multiple targets and clothing-attribute cases. Use image-grouped uncertainty intervals.
6. State possible foundation-model training overlap with COCO. Excluding our own development images does not prove absence from foundation-model pretraining.
7. Unmodified ZoomNeXt has no text input and is only a vision-only control on this task. A general claim about outperforming it in camouflage segmentation requires a separate common camouflage task with scene-disjoint data. Our own unannotated video cannot supply quantitative mask accuracy.

## Completed training-free diagnostic before this decision

Seven fixed rules were checked on the old 30-image development set: unchanged LISA, small-hole filling, all enclosed-hole filling, 3/5-pixel morphological closing, 3-pixel median filtering, and fixed weighted mask voting. No parameters were trained. Development selection chose enclosed-hole filling, which changes the mask only by filling background components disconnected from the image border.

On the already inspected 120-expression set, positive mean IoU changed from 70.654% to 71.026% (+0.372 percentage points); the descriptive paired-bootstrap interval was +0.198 to +0.566 points. No-target rejection remained 0/20. Because the images and mask defects had already been inspected, this is encouraging exploratory evidence, not independent confirmation. It also does not show better understanding of clothing descriptions.

Artifacts: `code/results/training_free_20260914` and `code/scripts/training_free_probe.py`. All computation ran remotely on cenara70hx. The next meaningful comparison should use the newly locked dataset protocol above.
