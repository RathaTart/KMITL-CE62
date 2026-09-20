import requests,json
base='https://huggingface.co/IDEA-Research/RexSeek-3B/resolve/10b3661c71bae890315f471d97a055e22fad4bb9/'
x=requests.get(base+'model.safetensors.index.json',timeout=30).json();keys=list(x['weight_map']);print('vision weights',len([k for k in keys if k.startswith('vision_tower.')]),[k for k in keys if k.startswith('vision_tower.')][:4])
