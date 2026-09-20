# CCTV appearance diagnostic: hats and black coats

Six distinct RSTPReid test identities were selected before predictions from 16 caption-matched candidates after assistant visual review. Ambiguous hood/hat and color cases were excluded. Each image received two short queries ("the main person wearing a hat", "the main person wearing a black coat") and its native caption: 18 queries per frozen method, original CoHD and Scale704+guard. No training or method tuning occurred.

Both methods returned nonempty masks for all 18 queries. For short queries, this includes 2/2 hat-positive and 4/4 black-coat-positive cases, but zero correct empty outputs among four hat-negative and two black-coat-negative cases. Returning a mask on positives alone does not demonstrate language understanding. The six native captions also all produced masks.

This measures empty/nonempty output agreement only, NOT mask IoU, retrieval Rank-1, or verified instance selection. RSTPReid supplies cropped surveillance people and captions, not native masks or our counterfactual absence annotations. Positives were checked against native captions; negative references came from assistant visual review before inference, not independent human annotation. The selected pilot is neither a representative benchmark nor a full-frame or distant-small-person evaluation. Foundation pretraining overlap is not ruled out.

Mean resident request time was 1.419013s original and 1.300940s Scale704. Another training process was using the GPU throughout; these are shared-load observations, not comparable with earlier idle-GPU timings. Includes image reading, preprocessing, language, inference, mask restoration and filtering; excludes initial loading, scoring and rendering. Methods were warmed twice and execution order alternated per query. No image features were cached.

## Dataset choices

- [RSTPReid](https://github.com/NjtechCVLab/RSTPReid-Dataset): 20,505 cropped images, 4,101 identities, 15 cameras, two descriptions per image. Official linked archive downloaded and sampled here. Useful for text/person matching, not full-frame segmentation. Zhu et al., DSSL, ACM MM 2021.
- [UPAR](https://github.com/speckean/upar_dataset): 40 unified attributes across PA100K, PETA, RAPv2 and Market1501-Attributes, useful for attribute recognition and cross-dataset checks. Original images are separate; verify individual attribute semantics and licenses. Not run here. Specker et al., WACV 2023.
- [PRW-TBPS](https://github.com/Dacun/Text-based-Person-Search): text annotations associated with PRW person boxes for full-image search. This is the closer next evaluation target for full-frame selection. Needs original PRW images; the linked original-image homepage returned HTTP502 during this check. Not downloaded or tested here. Box annotations are not segmentation masks. Zhang et al., Text-based Person Search in Full Images via Semantic-Driven Proposal Generation.

Proposed next experiment: person proposals followed by head-region hat and torso clothing verification, with matched and mismatched descriptions, uncertainty/absence calibration, and separately locked identity/camera splits. Measure selection, false acceptance, missed targets and total latency. This architecture suggestion is untested here and is not a novelty claim. Original CoHD remains default.

Evidence: `code/results/rstp_attributes_20260915/diagnostic` contains the pre-inference lock, prompts, input/code hashes, 36 masks, per-query timing, summary, audit and 18 visual comparisons. Prediction-to-prediction overlap in the audit is prompt sensitivity, not ground-truth accuracy. Local-only presentation; no publication.
