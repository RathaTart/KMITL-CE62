"""Small supervised boundary gate over frozen LISA/SAM/YOLO/ZoomNeXt outputs.

Only LISA/SAM disagreement pixels may change. Train on 20 development images,
select among fixed epoch checkpoints on 10 development images, then freeze.
"""
import argparse,json,platform,hashlib
from pathlib import Path
import cv2,numpy as np,torch
from PIL import Image

def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2))
def name(i):return f'{i["item_id"]}__{i["prompt_id"]}'
def mask(p):return np.asarray(Image.open(p))>0
def features(i,a):
    n=name(i);l=mask(a.source/'p1_masks'/f'{n}.png');r=mask(a.refinement/'refined'/f'{n}.png')
    y=mask(a.yolo/'masks'/f'{n}.png');z=np.load(a.zoom/'probabilities'/f'{n}.npy').astype('float32')
    gray=cv2.imread(i['image'],cv2.IMREAD_GRAYSCALE).astype('float32')/255
    edge=np.clip(cv2.magnitude(cv2.Sobel(gray,cv2.CV_32F,1,0),cv2.Sobel(gray,cv2.CV_32F,0,1)),0,1)
    def sdf(m):return np.clip((cv2.distanceTransform(m.astype('uint8'),cv2.DIST_L2,5)-cv2.distanceTransform((~m).astype('uint8'),cv2.DIST_L2,5))/20,-1,1)
    agreement=(l&r).sum()/max(1,(l|r).sum())
    f=np.stack([l,r,y,z,sdf(l),sdf(r),edge,np.full(l.shape,agreement)],-1).astype('float32')
    if a.drop in ['yolo','both']:f[:,:,2]=0
    if a.drop in ['zoom','both']:f[:,:,3]=0
    return f,l,r

def predict(model,f,l,r):
    pred=l.copy();d=l!=r
    with torch.no_grad():
        x=torch.from_numpy(f[d]);vals=[]
        for chunk in x.split(65536):vals.append(model(chunk).squeeze(-1).numpy()>0)
        if vals:pred[d]=np.concatenate(vals)
    return pred
def iou(p,g):return (p&g).sum()/max(1,(p|g).sum()) if (p|g).any() else 1.
def net():return torch.nn.Sequential(torch.nn.Linear(8,16),torch.nn.ReLU(),torch.nn.Linear(16,1))

def train(a):
    torch.manual_seed(20260914);rng=np.random.default_rng(20260914);torch.set_num_threads(4)
    items=read(a.source/'manifest.json')['items'];ids=sorted({Path(i['image']).name for i in items});rng.shuffle(ids);trainids=set(ids[:20]);validids=set(ids[20:])
    assert not trainids&validids
    cache=[]
    for i in items:
        f,l,r=features(i,a);g=mask(i['ground_truth']);cache.append((i,f,l,r,g))
    xs=[];ys=[]
    for i,f,l,r,g in cache:
        if Path(i['image']).name not in trainids:continue
        yy,xx=np.where(l!=r)
        if len(yy):
            take=rng.choice(len(yy),size=min(4096,len(yy)),replace=False);xs.append(f[yy[take],xx[take]]);ys.append(g[yy[take],xx[take]])
    x=torch.from_numpy(np.concatenate(xs));y=torch.from_numpy(np.concatenate(ys).astype('float32'))[:,None]
    model=net();opt=torch.optim.AdamW(model.parameters(),lr=.005,weight_decay=.01);log=[];best=-1
    a.out.mkdir(parents=True,exist_ok=False)
    for epoch in range(1,41):
        for idx in torch.randperm(len(x)).split(2048):
            loss=torch.nn.functional.binary_cross_entropy_with_logits(model(x[idx]),y[idx]);opt.zero_grad();loss.backward();opt.step()
        if epoch in [5,10,20,40]:
            scores=[];baseline=[]
            for i,f,l,r,g in cache:
                if Path(i['image']).name not in validids or not g.any():continue
                scores.append(float(iou(predict(model,f,l,r),g)));baseline.append(float(iou(l,g)))
            value=float(np.mean(scores));log.append(dict(epoch=epoch,validation_positive_miou=value,lisa_positive_miou=float(np.mean(baseline))))
            if value>best:best=value;torch.save(model.state_dict(),a.out/'gate.pt')
            print(log[-1],flush=True)
    write(a.out/'training.json',dict(dropped=a.drop,train_images=sorted(trainids),validation_images=sorted(validids),epochs_checked=log,seed=20260914,parameters=sum(p.numel() for p in model.parameters()),features=['LISA','SAM','YOLO-SAM','Zoom probability','LISA signed distance','SAM signed distance','image edge','global LISA-SAM agreement'],constraint='Only LISA/SAM disagreement pixels may change',checkpoint_sha256=hashlib.sha256((a.out/'gate.pt').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))

def infer(a):
    torch.set_num_threads(4);model=net();model.load_state_dict(torch.load(a.checkpoint,map_location='cpu',weights_only=True));model.eval()
    (a.out/'masks').mkdir(parents=True,exist_ok=False)
    for i in read(a.source/'manifest.json')['items']:
        f,l,r=features(i,a);p=predict(model,f,l,r);Image.fromarray(p.astype('uint8')*255).save(a.out/'masks'/f'{name(i)}.png')
    write(a.out/'inference.json',dict(checkpoint=str(a.checkpoint),sha256=hashlib.sha256(a.checkpoint.read_bytes()).hexdigest()))

if __name__=='__main__':
    if platform.node()!='cenara70hx':raise SystemExit('Remote only')
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['train','infer']);p.add_argument('--source',type=Path,default=Path('results/grefcoco_pilot_p1_p2'));p.add_argument('--refinement',type=Path,default=Path('results/lisa_dense_refinement_20260914'));p.add_argument('--yolo',type=Path,default=Path('results/attribute_pilot_20260914/yolo/p3_expression'));p.add_argument('--zoom',type=Path,default=Path('results/lisa_refinement_20260914/zoom'));p.add_argument('--out',type=Path,default=Path('results/boundary_fusion_20260914'));p.add_argument('--checkpoint',type=Path);p.add_argument('--drop',choices=['none','zoom','yolo','both'],default='none');a=p.parse_args();(train if a.stage=='train' else infer)(a)
