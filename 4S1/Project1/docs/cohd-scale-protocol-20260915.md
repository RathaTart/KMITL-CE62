# CoHD scale and runtime study — protocol before predictions

User authorized continued small-person detection experiments with approximately unchanged runtime and, if useful, descriptive-person prompts. All inference, training, scoring and numerical diagnostics run on cenara70hx. Website changes remain local only.

## Bounded first experiment

Keep released CoHD-Tiny weights fixed. Compare the original FP32 480-square input with mixed-precision inference, increased resolution, and overlapping crop inference. First verify that each variant runs with finite outputs. Mixed precision is a computational control, not a novel architecture. Tiling is inspired by established sliced inference, not claimed as new: https://arxiv.org/abs/2202.06934. AMP reference: https://docs.pytorch.org/docs/stable/notes/amp_examples.html.

Use 24 evenly sampled historical CCTV frames (12 MOTS / 12 VIRAT) as explicitly reused development data. All 120 prior CCTV frames and viewpoints are already explored. Select candidates using development only. Original defaults remain unchanged.

Primary runtime criterion: mean full-image resident request <=1.05 times paired original; <=1.10 is an exploratory near-budget band, not a primary pass. Include image loading, preprocessing, every crop, model execution, coordinate restoration and fusion; exclude scoring, plot export and one-time loading. Rotate method order and warm up each configuration. Record memory and per-image times.

Candidates: FP32 480 baseline, FP32 640 resolution control, AMP 480/640/768, four overlapping tiles at AMP 256 or 320, and full AMP 256 plus four AMP 256 tiles. Crops are deterministic quadrants each covering 55% of image width and height (10% overlap); no GT-dependent region selection. Original no-target decision applies to each pass. Restore masks to original coordinates and union predictions. Cropping can remove relational context and increase false positives; measure these, not only recall. A failed/unsupported precision mode must be recorded, not silently substituted under the same label.

## Selection and confirmation

Development implementation amendment, before confirmation: the original decoder hard-codes spatial projection lengths 900/3600/14400, so non-480 resolutions fail with matrix-shape errors. Preserve these failed controls. Test explicitly named `adapt_*` variants which bilinearly resample only the spatial projection input back to its trained grid while retaining high-resolution attention maps elsewhere. No weights change. Also test full 480 AMP plus one fixed upper-55%-height crop, or one central-60%-width/height crop, in the same batch. This is deterministic and uses no GT. The amendment is development work, not a post-confirmation change. AMP 480 is retained as a speed-only control.

Second development amendment, still before confirmation predictions: additional foreground from scale/crops increased VIRAT false positives. Sweep four native-component rules on development (minimum height 12/20 pixels and maximum width/height 0.8/1.2, exempt components with >=4096 pixels). These are standing-person shape heuristics with explicit crouching/fragmentation/domain risks, not learned person recognition. Evaluate actual merged masks, not just delete boxes after scoring. Re-run the best guarded 768 and center-crop candidates with timing/segmentation metrics; also inspect 704 as an intermediate resolution. The final primary and one secondary must be frozen before confirmation. No numeric selection rule uses confirmation results.

Prefer a method that improves small-person recall at the primary time budget, with no more than 1 point loss of positive mask IoU and no more than 10% increase in false-positive pixels/box components within each relevant domain. If none qualify, report the best measured trade-offs without claiming the joint goal was achieved. Limit confirmation to baseline and up to two development-selected variants, frozen before confirmation scoring.

Prepare previously unscored, image-disjoint frames from the existing fixed cameras before any new predictions. These are temporally related to explored footage, so call this within-camera confirmation, not unseen-camera generalization. Save source-frame and hash exclusions. Person observations are correlated; no broad population significance claim from two viewpoints.

MOTS: native masks and ignore regions; mean IoU, pixel FP/FN, per-person coverage>=50%, and small-person (<64 original pixels tall) coverage. VIRAT: existing mask-to-box adapter with native human boxes, one-to-one IoU>=0.5 matches, TP/FP/FN and size strata. Neither is official detector/tracking AP. Inspect fixed-position examples including failures.

## Descriptive-language check

Use native human referring expressions and native person masks from gRefCOCO, explicitly distinguishing this from CCTV validation. Include hat/cap and clothing descriptions, multiple-person distractors and absent targets if eligible annotations exist. Freeze selection before predictions, audit training/project overlap, and never invent hat labels for tiny CCTV people. If no verified CCTV attribute labels exist, report that limitation. Compare original and selected candidate on the exact same expressions; report target-mask IoU, instance coverage, incorrect-person coverage and time. A crop's geometric scale alone does not establish correct attribute binding.
