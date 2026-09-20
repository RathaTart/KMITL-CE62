"""Opt-in inference acceleration; leaves frozen research implementation unchanged."""
import types
import torch
from lisa_engine import LisaEngine
from model.llava.model.language_model.llava_llama import LlavaLlamaForCausalLM

class FastLisaEngine(LisaEngine):
    def segment(self,*args,**kwargs):
        original=self.model.generate
        def cached_generate(model,*a,**kw):
            kw['use_cache']=True
            kw['attention_mask']=torch.ones_like(kw['input_ids'])
            kw['output_hidden_states']=False
            outputs=original(*a,**kw)
            # Original evaluate consumes the full last decoding-step hidden state.
            # Replay that exact prefix without cache; cached per-token hidden states
            # must not be concatenated/substituted into the segmentation projection.
            replay=LlavaLlamaForCausalLM.forward(model,input_ids=outputs.sequences[:,:-1],images=kw['images'],use_cache=False,output_hidden_states=True,return_dict=True)
            outputs.hidden_states=(replay.hidden_states,)
            return outputs
        self.model.generate=types.MethodType(cached_generate,self.model)
        try:return super().segment(*args,**kwargs)
        finally:self.model.generate=original
