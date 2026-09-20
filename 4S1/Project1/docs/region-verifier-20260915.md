# Frozen appearance verifier: confirmation result

Generic Scale704 person proposals followed by frozen CLIP ViT-B/32 checking reduced false acceptance, but rejected two true hat cases. Original CoHD remains default. No model weights were trained; crop mode and thresholds were selected only on the six previously explored development images, then locked before 24 new identity-disjoint RSTPReid images / 40 unambiguous attribute queries.

| Endpoint | Original | Scale704 | Verified |
|---|---:|---:|---:|
| Hat positives returning masks |9/9|9/9|7/9|
| Hat negatives correctly empty |0/13|0/13|9/13|
| Black-coat positives returning masks |6/6|6/6|6/6|
| Black-coat negatives correctly empty |0/12|0/12|12/12|
| All positive retention |15/15|15/15|13/15|
| All correct negative rejections |0/25|0/25|21/25|
| Resident mean, shared GPU |1.417641s|1.298559s|1.359517s|

False acceptance fell 25→4; missed positives increased 0→2. The intent of improving rejection without losing positives was NOT fully achieved. Overall empty/nonempty agreement was 34/40, versus15/40 for baselines, but this is not native mask accuracy or instance selection. Generic unfiltered proposals returned masks on every query, so generic prompting alone did not resolve rejection.

Mean verifier/extra processing cost was0.060759s; total was approximately4.7% above Scale704 and below the original model in the same shared-load run. Another training process occupied the GPU throughout. Do not compare these absolute values to previous idle-GPU0.593/0.654s runs or claim clean performance certification. Resident requests include image read/preprocessing, CoHD, components, crops, CLIP and mask selection; exclude startup, scoring and figures. Fixed attribute text embeddings are cached at startup; image embeddings are recomputed per request. The proposal-control timing is the CoHD portion inside a verified request.

Full-frame smoke timing (two frames × two attributes, multiple candidate regions): original1.446694s, Scale7041.298248s, verified1.519111s. This is17.0% above Scale704 and5.0% above original under shared load. Do not transfer the cropped single-candidate4.7% overhead claim to full frames. No full-frame appearance accuracy is available.

## What was selected

CoHD uses `all people`; connected components are approximate proposals. Cropped-main-person tests keep the largest; a separate qualitative full-frame smoke check uses up to eight. CLIP compares fixed positive/alternative texts. Hat: whole-person crop, margin>0 (hat/cap/beanie versus hair/hood). Black upper clothing: torso20–75% of proposed height, margin>−0.01 versus ten alternative colors. No open-ended prompt parser or multi-attribute reasoning is claimed.

Whole versus regional crops and thresholds−0.02,−0.01,0,0.01,0.02 were tested on development only. Head-only(top42%) was worse than whole-person for hats. Whole and torso tied for black at the selected threshold; the declared tie-break preferred torso. Thus torso superiority is not demonstrated. Cosine margins are not calibrated correctness probabilities.

## Evidence limits

The24 images are selected from32 unseen-by-this-study candidate identities, excluding all16 previous reviewed identities; eight uncertain attribute labels are omitted, leaving40 queries. Reference presence came from captions and assistant visual inspection before inference, not native absence/mask labels or independent human annotation. These are cropped surveillance people, not a representative full-frame benchmark. Identity separation does not ensure new-camera or pretraining independence.

Two predetermined, previously explored full CCTV frames exercise both attributes in multi-proposal mode, qualitative only: no native appearance GT. A connected component can merge people, geometric head/torso crops can be misplaced, and a verifier cannot recover people missing from proposals. Keep the original default; any deployment decision needs independent labels and larger tests. No architecture novelty or general superiority is claimed.

Visual inspection of `08_hat` shows a concrete failure: the generic mask-derived candidate starts below the visible hat, so even whole-candidate verification loses that evidence. Top padding or independent detector boxes should be tested in a subsequent revision on newly locked data, not retuned here and described as untouched confirmation.

References: [CLIP](https://github.com/openai/CLIP), [released checkpoint](https://huggingface.co/openai/clip-vit-base-patch32), [RSTPReid](https://github.com/NjtechCVLab/RSTPReid-Dataset). Full method predeclaration is in `region-verifier-protocol-20260915.md`; evidence at `code/results/region_verifier_20260915`, with source hashes, pre-inference locks, all outputs/timings and audit. Local-only website. CLI `infer_region_verifier.py` is opt-in, remote only.
