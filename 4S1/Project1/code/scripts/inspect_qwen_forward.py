import inspect
from transformers import Qwen2VLForConditionalGeneration
print(inspect.signature(Qwen2VLForConditionalGeneration.forward))
print(inspect.getsource(Qwen2VLForConditionalGeneration.forward)[-5500:])
