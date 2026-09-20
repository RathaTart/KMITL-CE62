import platform,requests,json,hashlib,zipfile,cv2
from pathlib import Path
from PIL import Image,ImageDraw
assert platform.node()=='cenara70hx'
C=Path('/home/osta/lisa-eval/code');O=C/'results/cohd_cctv_20260915';O.mkdir(exist_ok=True);D=O/'source';D.mkdir(exist_ok=True)
entries=[('uid_vid_00144','010201','56f587f18d777f753209cc33','validation'),('uid_vid_00147','010004','56f587a38d777f753209cb58','test'),('uid_vid_00149','010200','56f587ec8d777f753209cc1b','test')]
z=zipfile.ZipFile(C/'results/personpath22_metadata_20260914/anno_visible.zip');records=[]
for uid,camera,code,split in entries:
 p=D/(uid+'.mp4');url='https://data.kitware.com/api/v1/item/'+code+'/download'
 if not p.exists():
  r=requests.get(url,stream=True,timeout=90);r.raise_for_status()
  with p.open('wb') as f:
   for b in r.iter_content(2**20):f.write(b)
 anno=json.loads(z.read('anno_visible_2022/'+uid+'.mp4.json'));(D/(uid+'.json')).write_text(json.dumps(anno));cap=cv2.VideoCapture(str(p));n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);assert n>0
 tiles=[]
 for frac in [.1,.5,.9]:
  cap.set(cv2.CAP_PROP_POS_FRAMES,int(n*frac));ok,im=cap.read();assert ok;im=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB));im.thumbnail((600,340));tiles.append(im)
 panel=Image.new('RGB',(1800,380),'white');draw=ImageDraw.Draw(panel);draw.text((8,8),uid+' source camera '+camera+' '+split,fill='black')
 for j,tile in enumerate(tiles):panel.paste(tile,(j*600,35))
 panel.save(D/(uid+'_contact.jpg'));cap.release();record=dict(uid=uid,camera=camera,split=split,url=url,video=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),fps=fps,frames=n,annotation=str(D/(uid+'.json')));records.append(record);print(json.dumps(record),flush=True)
(O/'source_lock.json').write_text(json.dumps(records,indent=2))
# MOTS static source camera review contact sheets.
M=C.parent/'dataset/mots/extracted/MOTSChallenge/train'
for seq in ['0009','0002']:
 paths=sorted((M/'images'/seq).glob('*.jpg'));panel=Image.new('RGB',(1800,380),'white');dr=ImageDraw.Draw(panel);dr.text((8,8),'MOTS '+seq,fill='black')
 for j,k in enumerate([len(paths)//10,len(paths)//2,9*len(paths)//10]):
  im=Image.open(paths[k]);im.thumbnail((600,340));panel.paste(im,(600*j,35))
 panel.save(D/('mots_'+seq+'_contact.jpg'))
