# Runtime optimization — 15 September 2026

An opt-in accelerated CLI is implemented at `code/scripts/infer_extended_fast.py`. Model weights, prompts, SAM refinement and Qwen rejection rules are unchanged. The original frozen accuracy pipeline remains available.

## Measured results

| Measurement | Original | Accelerated |
|---|---:|---:|
| Complete pipeline, including model loading | 109.92 s | 75.20 s |
| LISA only, loaded model, three paired cases | 44.78–46.78 s | 13.47–14.14 s |

The complete pipeline comparison used one identical development image and expression in two sequential process runs on cenara70hx. Final masks were identical pixel-for-pixel. The three paired LISA cases (single, multiple and absent target) also produced identical masks and text. These are small runtime/equivalence checks, not a full accuracy re-evaluation or a real-time throughput benchmark. The 13–14 seconds figure is only the LISA stage.

## Implementation

The old LISA configuration disables KV caching, repeating full-prefix work during text generation. The new wrapper enables KV caching, then replays the final full prefix without cache to supply the hidden states expected by the original segmentation decoder. A full attention mask is explicitly provided for the older LLaVA implementation. No model-weight updates are involved.

The initial attempt exposed an older LLaVA attention-mask requirement; its failure log remains on the remote host. Comparisons to older archived masks showed small boundary differences even with a fresh original run, so the reported equivalence is based on newly paired runs rather than claiming exact reproduction across all historical runs.

## Run remotely

From `/home/osta/lisa-eval/code`:

```bash
/home/osta/blip2-qformer-eval/.venv/bin/python scripts/infer_extended_fast.py \
  --image /absolute/path/image.jpg --text "the person in a blue hat" \
  --out /absolute/path/new-output
```

The output includes mask, overlay, runtime and the original method-lock hash. All inference must run on the remote host. This reduces latency but does not make the full pipeline real-time.

## Evidence

- [Full pipeline timing and equivalence](../code/results/runtime_optimization_20260915/full_comparison.json)
- [Three paired LISA cases](../code/results/runtime_optimization_20260915/lisa_paired.json)
- [Hugging Face explanation of KV caching](https://github.com/huggingface/transformers/blob/main/docs/source/en/cache_explanation.md)
