import json,platform,requests,subprocess,sys
from pathlib import Path
from robust_download import download
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code/research_vendors/rexseek-runtime');root.mkdir(exist_ok=True)
for pkg,version in [('timm','1.0.15'),('open_clip_torch','2.31.0'),('ftfy','6.3.1'),('wcwidth','0.2.13')]:
    meta=requests.get(f'https://pypi.org/pypi/{pkg}/{version}/json',timeout=30).json();f=next(f for f in meta['urls'] if f['filename'].endswith('py3-none-any.whl'));p=root/'wheels'/f['filename'];download(f['url'],str(p),sha256=f['digests']['sha256'],max_stalls=8)
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--target',str(root/'packages'),str(p)],check=True)
