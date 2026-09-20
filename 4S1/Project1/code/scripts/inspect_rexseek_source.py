import requests
for fn in ['modeling_rexseek.py','preprocessing_rexseek.py']:
    r=requests.get('https://huggingface.co/IDEA-Research/RexSeek-3B/resolve/10b3661c71bae890315f471d97a055e22fad4bb9/'+fn,timeout=30);r.raise_for_status()
    print('\nFILE',fn,'\n',r.text[:16000])
