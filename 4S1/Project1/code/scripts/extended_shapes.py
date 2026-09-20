"""Pure frozen-mask transformations shared by final rendering and audits."""
import cv2,numpy as np
from scipy.ndimage import binary_fill_holes,distance_transform_edt
from PIL import Image

def shape_mask(lisa,ms,cfg,image=None):
    family=cfg['family']
    if family in ['baseline','lisa']:return lisa.copy()
    if family=='fill_holes':return binary_fill_holes(lisa)
    if family=='guided':
        guide=np.asarray(Image.fromarray(image).convert('L')).astype('float32')/255;size=(2*cfg['radius']+1,)*2
        mean=lambda v:cv2.boxFilter(v,-1,size,normalize=True,borderType=cv2.BORDER_REFLECT)
        mi=mean(guide);mp=mean(lisa.astype('float32'));var=mean(guide*guide)-mi*mi;cov=mean(guide*lisa)-mi*mp;a=cov/(var+cfg['eps']);b=mp-a*mi
        return mean(a)*guide+mean(b)>=cfg['threshold']
    if family=='remove_small':
        n,labels,stats,_=cv2.connectedComponentsWithStats(lisa.astype('uint8'),8);keep=np.flatnonzero(stats[:,cv2.CC_STAT_AREA]>=cfg['fraction']*lisa.size);return np.isin(labels,keep[keep!=0])
    if family in ['open','close','dilate','erode','median']:
        u=lisa.astype('uint8');size=cfg['size'];kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size))
        if family=='median':return cv2.medianBlur(u,size)>0
        if family=='dilate':return cv2.dilate(u,kernel)>0
        if family=='erode':return cv2.erode(u,kernel)>0
        return cv2.morphologyEx(u,cv2.MORPH_OPEN if family=='open' else cv2.MORPH_CLOSE,kernel)>0
    coverage=(ms&lisa).sum((1,2))/np.maximum(ms.sum((1,2)),1);accepted=ms[coverage>=cfg['coverage']];sam=accepted.any(0) if len(accepted) else np.zeros_like(lisa)
    if family=='agreement':
        op=cfg['op'];return sam if op=='sam' else lisa&sam if op=='intersect' else lisa|sam if op=='union' else lisa.astype('int32')+accepted.sum(0)>=2 if len(ms) else lisa
    if family=='union_clean':
        p=lisa|sam;n,labels,stats,_=cv2.connectedComponentsWithStats(p.astype('uint8'),8);keep=np.flatnonzero(stats[:,cv2.CC_STAT_AREA]>=cfg['fraction']*p.size);return np.isin(labels,keep[keep!=0])
    if family=='trim_union':
        allowed=(lisa&sam).sum()/max(lisa.sum(),1)>=cfg['mincover'];size=cfg['margin'];support=cv2.dilate(sam.astype('uint8'),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size)))>0
        return (lisa&support)|sam if allowed else lisa|sam
    if family=='distance_blend':
        overlap=(sam&lisa).sum()/max((sam|lisa).sum(),1)
        if not sam.any() or not lisa.any() or overlap<cfg['minagreement']:return lisa.copy()
        ld=distance_transform_edt(lisa)-distance_transform_edt(~lisa);sd=distance_transform_edt(sam)-distance_transform_edt(~sam)
        return (1-cfg['weight'])*ld+cfg['weight']*sd>0
    raise ValueError(cfg)

