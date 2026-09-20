"""Remote preparation only, before model evaluation."""
import json,hashlib,platform,re,zipfile,random
from pathlib import Path
import requests
from robust_download import download
assert platform.node()=='cenara70hx'
R=Path('/home/osta/lisa-eval/code/results/region_verifier_20260915');R.mkdir(exist_ok=True)
W=Path('/home/osta/lisa-eval/released-models/weights/clip-vit-base-patch32');W.mkdir(exist_ok=True)
api=requests.get('https://huggingface.co/api/models/openai/clip-vit-base-patch32?blobs=true',timeout=30);api.raise_for_status();info=api.json();rev=info['sha']
for name in ['config.json','preprocessor_config.json','tokenizer_config.json','special_tokens_map.json','vocab.json','merges.txt','pytorch_model.bin']:
 entry=next(x for x in info['siblings'] if x['rfilename']==name);sha=entry.get('lfs',{}).get('sha256')
 download(f'https://huggingface.co/openai/clip-vit-base-patch32/resolve/{rev}/{name}',str(W/name),sha256=sha,timeout=20)
(R/'clip_source.json').write_text(json.dumps(dict(repo='openai/clip-vit-base-patch32',revision=rev,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in W.iterdir() if p.is_file()}),indent=2))
from PIL import Image,ImageDraw,ImageFont
prior=Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915')
old=json.loads((prior/'selected.json').read_text());excluded={x['source']['id'] for x in old}
data=json.loads((prior/'captions.json').read_text());random.Random(20260916).shuffle(data)
chosen=[];used=set(excluded)
with zipfile.ZipFile('/home/osta/lisa-eval/code/data/RSTPReid.zip') as z:
 for group,pattern in [('hat',r'\b(?:hat|cap|beanie)\b'),('other',r'\b(?:black|white|blue|red|grey)\s+(?:coat|jacket|shirt|top)\b')]:
  for row in data:
   if row['split']!='test' or row['id'] in used:continue
   captions=row['captions']
   if not any(re.search(pattern,s,re.I) for s in captions):continue
   if group=='hat' and any(re.search(r'hood|jacket.s hat',s,re.I) for s in captions):continue
   path=R/'candidate_images'/row['img_path'];path.parent.mkdir(exist_ok=True);path.write_bytes(z.read('imgs/'+row['img_path']));used.add(row['id']);chosen.append(dict(group=group,path=str(path),source=row,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   if sum(x['group']==group for x in chosen)>=16:break
(R/'candidates.json').write_text(json.dumps(chosen,indent=2));font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
for start in range(0,len(chosen),16):
 sheet=Image.new('RGB',(1000,1200),'white');d=ImageDraw.Draw(sheet)
 for j,s in enumerate(chosen[start:start+16]):
  im=Image.open(s['path']).convert('RGB');factor=min(225/im.width,260/im.height);im=im.resize((round(im.width*factor),round(im.height*factor)));x=j%4*250;y=j//4*300;sheet.paste(im,(x+(250-im.width)//2,y));d.text((x+5,y+265),f"{start+j}: {s['source']['img_path']}",font=font,fill='black')
 sheet.save(R/f'contact_{start}.jpg')
print('candidates',len(chosen),flush=True)
