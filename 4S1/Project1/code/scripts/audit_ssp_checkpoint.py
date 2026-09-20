import torch,json,sys
from pathlib import Path
R=Path('/home/osta/lisa-eval/released-models');torch.set_num_threads(4)
a=torch.load(R/'weights/SSP-SAM_checkpoint_best_miou.pth',map_location='cpu',weights_only=False)
print('keys',list(a));print('epoch',a.get('epoch'));print('args',a.get('args'))
b=torch.jit.load(str(R/'weights/SSP-SAM_CS-ViT-B-16.pt'),map_location='cpu').state_dict()
d=[]
for k,v in b.items():
 if 'encoder.'+k in a['model'] and not torch.equal(v.float(),a['model']['encoder.'+k].float()):d.append((k,float((v.float()-a['model']['encoder.'+k].float()).abs().max())))
print('encoder differences',len(d),d[:10])
