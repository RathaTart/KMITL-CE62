"""Batch-friendly wrapper around the official LISA inference path.

Upstream only ships `chat.py`, an interactive REPL that hard-codes a full-GPU
fp16/bf16 layout. This module exposes the same computation as a reusable class so
it can be driven over a dataset, and adds the placement control needed to fit
LISA-7B on a 6 GB card:

    LLM (LLaVA-7B)      -> GPU, NF4 4-bit          ~3.6 GB
    CLIP ViT-L/14       -> GPU, fp16               ~0.6 GB
    SAM ViT-H encoder   -> GPU fp16 or CPU fp32    ~1.3 GB   <- the swing factor
    SAM prompt enc/dec  -> GPU fp16                negligible

`sam_encoder_device="cpu"` keeps the SAM image encoder off the GPU and moves only
the resulting [1, 256, 64, 64] feature map back, which is what makes the model
run at all on 6 GB. It costs wall-clock time but does not change the output:
the encoder is frozen in LISA and its result is deterministic either way.
Measured cosine similarity against the GPU fp16 encoder is 0.99999.

One deliberate departure from upstream: the SAM **prompt encoder and mask
decoder run in fp32**, not fp16. The [SEG] prompt embedding is large enough
(norm 150-250) that a 256-dim dot product overflows fp16 and the decoder returns
NaN, which thresholds to an empty mask and imitates a model failure. See
`_make_sam_head_fp32`.
"""

import os
import sys
import time
import types
from typing import List, Optional

import cv2
import numpy as np
import torch
import torch.nn.functional as F

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISA_DIR = os.path.join(REPO_ROOT, "LISA")
if LISA_DIR not in sys.path:
    sys.path.insert(0, LISA_DIR)

from accelerate.hooks import remove_hook_from_module  # noqa: E402
from transformers import AutoTokenizer, BitsAndBytesConfig, CLIPImageProcessor  # noqa: E402

from model.LISA import LISAForCausalLM  # noqa: E402
from model.llava import conversation as conversation_lib  # noqa: E402
from model.llava.mm_utils import tokenizer_image_token  # noqa: E402
from model.segment_anything.utils.transforms import ResizeLongestSide  # noqa: E402
from utils.utils import (  # noqa: E402
    DEFAULT_IM_END_TOKEN,
    DEFAULT_IM_START_TOKEN,
    DEFAULT_IMAGE_TOKEN,
    IMAGE_TOKEN_INDEX,
)

SAM_PIXEL_MEAN = torch.Tensor([123.675, 116.28, 103.53]).view(-1, 1, 1)
SAM_PIXEL_STD = torch.Tensor([58.395, 57.12, 57.375]).view(-1, 1, 1)


def enable_mmap_checkpoint_loading():
    """Make transformers memory-map the .bin shards instead of reading them whole.

    LISA-7B-v1 ships as two pickle shards, the first of which is 9.98 GB.
    transformers 4.31 calls torch.load() without mmap, so that entire shard is
    materialised in RAM before any tensor reaches the GPU. On a 16 GB laptop
    that pages catastrophically. torch>=2.1 can mmap zipfile-format checkpoints,
    which drops the resident cost to roughly the size of one tensor at a time.
    """
    import transformers.modeling_utils as modeling_utils

    if getattr(modeling_utils.load_state_dict, "_mmap_patched", False):
        return
    original = modeling_utils.load_state_dict

    def load_state_dict(checkpoint_file, *args, **kwargs):
        if str(checkpoint_file).endswith(".bin"):
            try:
                return torch.load(checkpoint_file, map_location="cpu", mmap=True)
            except Exception:  # noqa: BLE001 - older torch / legacy tar format
                pass
        return original(checkpoint_file, *args, **kwargs)

    load_state_dict._mmap_patched = True
    modeling_utils.load_state_dict = load_state_dict


def sam_preprocess(x: torch.Tensor, img_size: int = 1024) -> torch.Tensor:
    """Normalise and zero-pad to a square SAM input (copied from chat.py)."""
    x = (x - SAM_PIXEL_MEAN) / SAM_PIXEL_STD
    h, w = x.shape[-2:]
    return F.pad(x, (0, img_size - w, 0, img_size - h))


class LisaEngine:
    def __init__(
        self,
        model_path: str,
        clip_path: str,
        precision: str = "fp16",
        quantization: str = "4bit",
        sam_encoder_device: str = "cpu",
        sam_cpu_dtype: str = "fp32",
        quantize_seg_projection: bool = False,
        image_size: int = 1024,
        model_max_length: int = 512,
        conv_type: str = "llava_v1",
    ):
        assert precision in ("fp32", "fp16", "bf16")
        assert quantization in ("none", "8bit", "4bit")
        assert sam_encoder_device in ("cuda", "cpu")
        assert sam_cpu_dtype in ("fp32", "bf16")
        self.quantize_seg_projection = quantize_seg_projection
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. torch was probably installed as a CPU-only "
                "build - reinstall from requirements-inference.txt."
            )

        enable_mmap_checkpoint_loading()

        self.image_size = image_size
        self.conv_type = conv_type
        self.sam_encoder_device = sam_encoder_device
        self.sam_cpu_dtype = torch.float32 if sam_cpu_dtype == "fp32" else torch.bfloat16
        self.torch_dtype = {
            "fp32": torch.float32,
            "fp16": torch.half,
            "bf16": torch.bfloat16,
        }[precision]

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            model_max_length=model_max_length,
            padding_side="right",
            use_fast=False,
        )
        self.tokenizer.pad_token = self.tokenizer.unk_token
        seg_token_idx = self.tokenizer("[SEG]", add_special_tokens=False).input_ids[0]

        kwargs = {"torch_dtype": self.torch_dtype}
        if quantization in ("4bit", "8bit"):
            # SAM must stay unquantised: a frozen ViT-H that never saw
            # quantisation during training loses mask-edge quality.
            skip = ["visual_model"]
            if not quantize_seg_projection:
                # text_hidden_fcs is the whole [SEG]-to-mask bridge:
                # Linear(4096,4096) -> ReLU -> Linear(4096,256), and every mask
                # rides on its output. Upstream's skip list omits it, so the
                # 4-bit path quantises it. Keeping it in fp16 costs 25.5 MB of
                # the 17.83 M parameters' worth of VRAM - nothing against a
                # 4-bit 7B - and removes NF4 rounding from the one projection
                # the mask quality is most sensitive to.
                skip.append("text_hidden_fcs")
            common = dict(llm_int8_skip_modules=skip)
            if quantization == "4bit":
                qconfig = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    **common,
                )
            else:
                qconfig = BitsAndBytesConfig(load_in_8bit=True, **common)

            kwargs.update(torch_dtype=torch.half, quantization_config=qconfig)

            # Everything lands on the GPU here, including the SAM encoder, and
            # _place_sam_encoder() moves the encoder down afterwards if asked.
            #
            # Do NOT try to place the encoder on the CPU *via* device_map, e.g.
            # {"model.visual_model.image_encoder": "cpu", "": 0}. accelerate's
            # dispatch_model reads a "cpu" entry as *offload* whenever the main
            # device is a GPU: the module keeps meta-tensor parameters and an
            # AlignDevicesHook streams the real weights in per forward. That
            # breaks .to("cpu") with "Cannot copy out of meta tensor", and if it
            # had worked the hook would have copied ViT-H onto the GPU on every
            # forward pass - precisely what the CPU placement exists to avoid.
            #
            # Loading GPU-first is affordable. Measured on a 6 GB RTX 3060:
            # 4.68 GB after from_pretrained, 5.27 GB peak once the CLIP tower is
            # built, then 4.08 GB after the encoder moves to the CPU.
            kwargs["device_map"] = {"": 0}

        self.model = LISAForCausalLM.from_pretrained(
            model_path,
            low_cpu_mem_usage=True,
            vision_tower=clip_path,
            seg_token_idx=seg_token_idx,
            **kwargs,
        )
        self.model.config.eos_token_id = self.tokenizer.eos_token_id
        self.model.config.bos_token_id = self.tokenizer.bos_token_id
        self.model.config.pad_token_id = self.tokenizer.pad_token_id

        # The released checkpoint already carries `train_mask_decoder`, so
        # LISAForCausalLM.__init__ ignores the `vision_tower` kwarg and falls back
        # to config.vision_tower ("openai/clip-vit-large-patch14"). Repoint it at
        # the local snapshot before the tower is actually built.
        inner_cfg = self.model.get_model().config
        inner_cfg.vision_tower = clip_path
        inner_cfg.mm_vision_tower = clip_path
        self.model.get_model().initialize_vision_modules(inner_cfg)

        vision_tower = self.model.get_model().get_vision_tower()
        vision_tower.to(device="cuda", dtype=self.torch_dtype)

        if quantization == "none":
            self.model = self.model.to("cuda", dtype=self.torch_dtype)

        self._place_sam_encoder()

        self.clip_image_processor = CLIPImageProcessor.from_pretrained(clip_path)
        self.transform = ResizeLongestSide(image_size)
        self.model.eval()

    def _place_sam_encoder(self):
        """Optionally push the SAM ViT-H image encoder onto the CPU.

        `get_visual_embs` is patched rather than relying on accelerate hooks, so
        the encoder runs in fp32 on CPU (fp16 CPU matmul is unsupported for some
        ops) and the feature map is cast back to the LLM's device/dtype.
        """
        encoder = self.model.model.visual_model.image_encoder

        # If this ever trips, something reintroduced accelerate offload for the
        # encoder (a "cpu"/"disk" entry in device_map). See the note in
        # __init__: offloaded modules hold meta tensors, and .to() cannot copy
        # out of them.
        meta = [n for n, prm in encoder.named_parameters() if prm.device.type == "meta"]
        if meta:
            raise RuntimeError(
                f"SAM image encoder has {len(meta)} meta-tensor parameters "
                f"(e.g. {meta[0]}), so its weights were never materialised. "
                "This happens when device_map offloads it; load with "
                'device_map={"": 0} and move it afterwards instead.'
            )
        self._make_sam_head_fp32()

        if self.sam_encoder_device == "cuda":
            # Keep the encoder itself in fp16 - it is the memory-hungry part and
            # it is numerically well behaved (its outputs sit in ~[-0.8, 0.7]).
            # Only its output dtype has to match the fp32 decoder.
            encoder.to(device="cuda", dtype=torch.half)
            enc_device, enc_dtype = "cuda", torch.half
        else:
            # Loading with device_map={"": 0} leaves an accelerate
            # AlignDevicesHook on every submodule, with execution_device cuda:0.
            # Those hooks move incoming tensors back onto the GPU before the real
            # forward runs, which once the weights are on the CPU raises
            #   "Input type (torch.cuda.FloatTensor) and weight type
            #    (torch.FloatTensor) should be the same".
            # We place this module by hand, so the hooks have to come off first.
            remove_hook_from_module(encoder, recurse=True)
            encoder.to(device="cpu", dtype=self.sam_cpu_dtype)
            torch.cuda.empty_cache()
            enc_device, enc_dtype = "cpu", self.sam_cpu_dtype

        def get_visual_embs(model_self, pixel_values: torch.FloatTensor):
            """Same computation as upstream, with placement and dtype pinned.

            Returns fp32 because the mask decoder is fp32; see
            _make_sam_head_fp32 for why it has to be.
            """
            with torch.no_grad():
                embs = []
                for i in range(pixel_values.shape[0]):
                    x = pixel_values[i].unsqueeze(0).to(enc_device, enc_dtype)
                    emb = model_self.model.visual_model.image_encoder(x)
                    embs.append(emb.to("cuda", torch.float32))
                torch.cuda.empty_cache()
                return torch.cat(embs, 0)

        self.model.get_visual_embs = types.MethodType(get_visual_embs, self.model)

    def _make_sam_head_fp32(self):
        """Force the [SEG]->mask path to fp32, because fp16 overflows there.

        text_hidden_fcs projects the [SEG] hidden state to the 256-d SAM prompt.
        Measured embedding norms are ~150-250 with individual values to +/-47. A
        256-dim dot product at that scale reaches ~4e5, past the fp16 ceiling of
        65504, so the mask decoder's attention produced inf and then NaN - and a
        NaN mask thresholds to nothing, which reads as "the model emitted [SEG]
        but no mask". On a 5-image check this silently voided 3 of 5 results.

        The checkpoint declares torch_dtype "bfloat16", whose exponent range
        matches fp32; fp16 is what upstream's 4-bit path happens to select, and
        it is not wide enough here.

        Cost is trivial: the prompt encoder and mask decoder are a few million
        parameters, against a 4-bit 7B LLM. The image encoder stays fp16.
        """
        visual = self.model.model.visual_model
        visual.prompt_encoder.float()
        visual.mask_decoder.float()

        # evaluate() derives the sparse-embedding dtype from pred_embeddings
        # (`sparse_embeddings.to(pred_embeddings[i].dtype)`), so promoting this
        # output to fp32 is what keeps the whole decoder path in fp32. A hook
        # avoids touching the quantised module itself, leaving the LLM's
        # quantisation exactly as configured.
        fc = self.model.model.text_hidden_fcs[0]
        if not getattr(fc, "_fp32_out_hooked", False):
            fc.register_forward_hook(lambda _m, _args, out: out.float())
            fc._fp32_out_hooked = True

    def build_prompt(self, instruction: str) -> str:
        conv = conversation_lib.conv_templates[self.conv_type].copy()
        conv.messages = []
        text = DEFAULT_IMAGE_TOKEN + "\n" + instruction
        text = text.replace(
            DEFAULT_IMAGE_TOKEN,
            DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN,
        )
        conv.append_message(conv.roles[0], text)
        conv.append_message(conv.roles[1], "")
        return conv.get_prompt()

    @torch.no_grad()
    def segment(self, image_rgb: np.ndarray, instruction: str, max_new_tokens: int = 64):
        """Run one image/instruction pair. Returns masks, decoded text and timings."""
        original_size_list = [image_rgb.shape[:2]]

        image_clip = (
            self.clip_image_processor.preprocess(image_rgb, return_tensors="pt")[
                "pixel_values"
            ][0]
            .unsqueeze(0)
            .to("cuda", self.torch_dtype)
        )

        image_sam = self.transform.apply_image(image_rgb)
        resize_list = [image_sam.shape[:2]]
        image_sam = (
            sam_preprocess(
                torch.from_numpy(image_sam).permute(2, 0, 1).contiguous().float(),
                img_size=self.image_size,
            )
            .unsqueeze(0)
            .to("cuda", self.torch_dtype)
        )

        input_ids = tokenizer_image_token(
            self.build_prompt(instruction), self.tokenizer, return_tensors="pt"
        ).unsqueeze(0).cuda()

        torch.cuda.synchronize()
        t0 = time.perf_counter()
        output_ids, pred_masks = self.model.evaluate(
            image_clip,
            image_sam,
            input_ids,
            resize_list,
            original_size_list,
            max_new_tokens=max_new_tokens,
            tokenizer=self.tokenizer,
        )
        torch.cuda.synchronize()
        latency = time.perf_counter() - t0

        output_ids = output_ids[0][output_ids[0] != IMAGE_TOKEN_INDEX]
        text = self.tokenizer.decode(output_ids, skip_special_tokens=False)
        text = text.replace("\n", "").replace("  ", " ").strip()

        masks: List[np.ndarray] = []
        for pred_mask in pred_masks:
            if pred_mask.shape[0] == 0:
                continue
            masks.append((pred_mask.detach().cpu().numpy()[0] > 0))

        return {
            "masks": masks,
            "text": text,
            "latency_s": latency,
            "emitted_seg": len(masks) > 0,
        }

    @staticmethod
    def peak_vram_gb() -> float:
        return torch.cuda.max_memory_allocated() / (1024**3)


def read_image_rgb(path: str) -> Optional[np.ndarray]:
    img = cv2.imread(path)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def overlay(image_rgb: np.ndarray, mask: np.ndarray, colour=(255, 0, 0)) -> np.ndarray:
    """Half-blend `colour` into the masked pixels (same style as chat.py)."""
    out = image_rgb.copy()
    if mask is not None and mask.any():
        out[mask] = (
            image_rgb * 0.5 + mask[:, :, None].astype(np.uint8) * np.array(colour) * 0.5
        )[mask]
    return out
