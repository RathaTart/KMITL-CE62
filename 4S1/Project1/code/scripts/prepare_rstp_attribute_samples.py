"""Inspect official RSTPReid archive and select native-caption samples remotely."""
import json,zipfile,platform,hashlib,re
from pathlib import Path
assert platform.node()=='cenara70hx'
root=Path('/home/osta/lisa-eval/code/results/rstp_attributes_20260915')
root.mkdir(exist_ok=True)
archive=Path('/home/osta/lisa-eval/code/data/RSTPReid.zip')
with zipfile.ZipFile(archive) as z:
 names=z.namelist();print(names[:8]);jn=[n for n in names if n.endswith('.json')];print(jn)
 data=json.loads(z.read(jn[0]));print('count',len(data),'first',data[0]);(root/'captions.json').write_text(json.dumps(data))
 print('splits',sorted(set(str(x.get('split')) for x in data)))
 selected=[];used=set();used_ids=set()
 for group,pattern in [('hat',r'\b(?:hat|cap|beanie)\b'),('black_clothing',r'\bblack\s+(?:shirt|t-shirt|jacket|coat|top|clothes|clothing|sweater|hoodie)\b')]:
  for row in data:
   if row.get('split')!='test':continue
   captions=row.get('captions',row.get('caption',[]));captions=[captions] if isinstance(captions,str) else captions
   matches=[s for s in captions if re.search(pattern,s,re.I)]
   if not matches or row['id'] in used_ids:continue
   if group=='hat' and any(re.search(r'hood|jacket.s hat',s,re.I) for s in captions):continue
   image=row.get('img_path',row.get('file_path',row.get('image_path')))
   if image in used:continue
   name=next(n for n in names if n.endswith('/'+image) or n==image or n.endswith('/'+Path(image).name))
   dest=root/'samples'/Path(image).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(z.read(name));used.add(image);used_ids.add(row['id'])
   selected.append(dict(group=group,path=str(dest),native_caption=matches[0],source=row,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
   if sum(x['group']==group for x in selected)>=8:break
 (root/'selected.json').write_text(json.dumps(selected,indent=2));print('selected',len(selected));print(json.dumps(selected,indent=2))
 from PIL import Image,ImageDraw,ImageFont
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
 sheet=Image.new('RGB',(1000,340*((len(selected)+4)//5)),'white');d=ImageDraw.Draw(sheet)
 for i,s in enumerate(selected):
  im=Image.open(s['path']).convert('RGB');im.thumbnail((180,280));x=(i%5)*200;y=(i//5)*340;sheet.paste(im,(x+(200-im.width)//2,y));d.text((x+5,y+285),f"{i}: {s['source']['img_path']}",font=font,fill='black');d.text((x+5,y+308),s['group'],font=font,fill='black')
 sheet.save(root/'contact.jpg')
