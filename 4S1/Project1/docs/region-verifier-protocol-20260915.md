# Frozen appearance verification protocol

User authorized continuing person proposals → head/torso appearance checking → acceptance/rejection, with measured extra latency. All scientific execution is on cenara70hx. No deployment and no foundation weights trained.

## Method and development

CoHD Scale704+guard with the generic query `all people` produces connected components. For the cropped-person diagnostic the largest component is selected; this is an approximate candidate, not a trained instance detector. For the separate full-frame smoke check, inspect up to eight largest components. A merged component can contain multiple people; missing proposals cannot be recovered by verification.

Frozen [CLIP ViT-B/32](https://huggingface.co/openai/clip-vit-base-patch32) compares candidate crops with fixed English attribute descriptions. Tested views: whole candidate; top 42% of proposed height for hats; 20–75% of height for black upper clothing. These are geometric regions, not estimated anatomical keypoints. Horizontal padding is 5%.

Hat margin: maximum cosine similarity for hat/cap/beanie minus maximum for uncovered hair/hood. Black clothing margin: black minus the strongest of ten alternative colors, averaging coat/jacket/top text templates before normalization. Margins are not calibrated probabilities. Support is restricted to these two attributes; it is not arbitrary natural-language reasoning.

The six previously explored RSTPReid images are development only. For each attribute test whole/region and thresholds −0.02, −0.01, 0, 0.01, 0.02. Prefer candidates retaining every development positive, maximize balanced presence agreement, break ties toward region and threshold closest to zero. This calibrates two decisions but updates no model weights.

Selected before confirmation: hat whole-person crop at margin >0; black torso crop at margin >−0.01. Each was 6/6 on development. For black clothing, whole and torso tied at the selected threshold; torso superiority is NOT established. Head-only checking did worse than the selected whole-person hat method on development. Machine-readable hashes and timestamps are in `method_lock.json`.

## Confirmation

From the official RSTPReid archive, seed 20260916 shuffles caption records. Candidate images are test identities excluding all 16 earlier reviewed identities. Up to 16 hat-caption and 16 other-clothing-caption identities are selected. Assistant visual review of originals, before predictions, retains 24 images and labels hats/black coats where clear. Uncertain attributes are null and omitted; no negative label is inferred solely from an unmentioned word in the caption. These are exploratory assistant-reviewed references, not native absence/mask annotations or independent human validation. Different identities do not establish unseen-camera or pretraining independence.

Compare original CoHD with attribute text; Scale704 with attribute text; the selected frozen verifier using generic proposals. Save generic unfiltered proposals as a control. Rotate method order per query; warm up all methods. Do not retune on confirmation. Report positive retention, correct rejection, false positives/negatives separately; empty/nonempty mask agreement is not instance-selection accuracy or mask IoU.

## Timing and artifacts

Measure complete resident requests: read/preprocess, CoHD, component selection, crop creation, CLIP image embedding, decision, and mask restoration/filtering. Initial loading, scoring and rendering are excluded. Fixed vocabulary text embeddings are prepared at startup; image features are not cached between requests. The unfiltered proposal-control timing is the CoHD portion inside a verified request, not a separate full-pipeline run. The GPU is shared with another user's training process; log process state, do not interrupt it, and do not compare these absolute times to earlier idle-GPU values.

Two predetermined reused full CCTV frames (first per source in the scale confirmation manifest) exercise the multi-component path with both attributes. They have no native appearance references; show qualitative outputs only, with no claimed appearance score.

Evidence directory: `code/results/region_verifier_20260915`. Retain original CoHD as default unless broader, independently annotated evaluation establishes the desired tradeoff. Primary research intent is better rejection without additional missed positives; if new positives are rejected, state that this intent is not fully achieved even if balanced agreement improves.
