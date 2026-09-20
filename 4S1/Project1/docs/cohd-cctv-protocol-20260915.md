# CoHD CCTV adaptation protocol — 2026-09-15

Authorized by the user's approval of the drafted plan. All scientific execution is remote on cenara70hx. Original CoHD-Tiny remains unchanged. No drone imagery.

## Data and split decisions, before model evaluation

- Train: 53 frames from stationary MOTS20-09, stride 10, with native human instance masks and prompt "all people"; replay 270 historical gRefCOCO expressions with original masks.
- Validate: 40 annotated PersonPath22/VIRAT keyframes from uid_vid_00144 and uid_vid_00149. Contact sheets show the same camera view, so both belong to the same source group. Add the existing 90 gRefCOCO validation expressions.
- Test: 60 MOTS20-02 frames with native masks, plus 60 annotated PersonPath22/VIRAT uid_vid_00147 frames with visible boxes. Test viewpoints differ from training and validation. Source 010200 and 010201 are not treated as independent cameras.
- CCTV prompts are deliberately limited to "all people": the datasets do not provide human-authored referring expressions. Do not claim clothing-description or absent-description CCTV validation. Native human masks/boxes are used; no generated segmentation ground truth.
- PersonPath22 frames are sampled only at annotation frame_idx values, checked against annotation timestamps and video dimensions. Crowd/background/in-vehicle labels are ignore boxes. Never treat unannotated frames as empty.
- A new balanced gRefCOCO sample could not be filled after historical-image exclusion (testA remaining negatives 14, multiple targets 5; val lacks eligible single cases in this available annotation pool). Use the previous 300-image set only as a reused regression diagnostic, excluded from this round's fitting/selection. It is not an untouched test.
- Contact-sheet checks at 10%, 50%, 90% verify stationary viewpoints. Two test viewpoints support a pilot, not population-level CCTV significance claims. No night imagery is established in this sample.

## Prespecified methods

Original: released CoHD-Tiny with default inference, no extra modules.
Custom A: fine-tune existing mask_embed, class_embed and dha; freeze all other weights including image/language encoders and original no-target head. Cache their unmodified upstream inputs during training only; deployment always encodes the full image. Loss: foreground-weighted cross entropy (background 1, foreground 2) plus Tversky (FP 0.3, FN 0.7), and KL preservation weight 0.1 on gRefCOCO replay. AdamW lr 1e-5, weight decay .01, 4 epochs, gradient accumulation 4, clipping 1, seed 20260915. Checkpoints at epochs 1, 2, 4. Select highest validation box F2 subject to gRef positive IoU no more than 1pp lower, absent accuracy no lower, and box precision no more than 2pp lower. If none qualifies, retain best F2 only as a failed-constraint experimental candidate.
Custom B: add a false-negative-aware linear verifier to Custom A. Fit on training outputs with positive examples weighted four times absent examples. Compare C=0.01 and 0.1 and thresholds .50 through .99, choosing validation absence rejection subject to no additional positive empty predictions in gRef/CCTV and no positive-IoU loss. Include a no-additional-rejection endpoint. Freeze before test. This is an adaptation, not an established novelty claim.

## Evaluation

MOTS: union IoU, cumulative IoU, foreground FP/FN pixels, and target-mask coverage recall >=50%, including small targets (visible mask height <64 pixels). Coverage recall is not one-to-one instance detection AP; a union can merge people.
PersonPath22: identical connected-component conversion (8-connected, minimum 4 pixels) on every mask; one-to-one Hungarian matching of component bounding boxes to native visible-person boxes at IoU >=0.5. Report TP/FP/FN, recall, precision, F2. Suppress unmatched predictions with >50% box area inside an ignore box. This is a declared mask-to-box adapter, not official tracking AP or native CoHD instance output.
Language regression: positive/negative IoU and rejection separately, labeled reused data.
Runtime: paired batch-one full-image resident requests with alternating method order after warmup, excluding initial load and file export. Include feature/verifier overhead. Target <5% overhead. Report mean/median/p95 and GPU memory. Do not infer inference speed from cached-head training/evaluation.

Report each CCTV source separately. Repeated frames are correlated; do not treat 120 frames as 120 independent cameras or use frame-bootstrap intervals to claim broad CCTV superiority. Primary desired outcome: lower missed-person rate, <=2pp precision loss and <5% runtime overhead on the test, while disclosing all mask and language regressions. Save failures and unchanged cases, not just gains.
