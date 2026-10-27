from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1]
a=np.array(Image.open(R/'generation/front_master.png').convert('RGBA'))
labels,_=ndi.label(a[:,:,3]>=245); counts=np.bincount(labels.ravel());counts[0]=0
core=labels==counts.argmax()
keep=ndi.binary_dilation(core,iterations=2)&(a[:,:,3]>30)
b=a.copy(); b[~keep]=0
b[:,:,3]=np.where(core,255,np.where(keep,np.minimum(np.rint(a[:,:,3].astype(float)*255/254),255),0)).astype('uint8')
Image.fromarray(b).save(R/'assets/front_master_clean.png')
report={'sourceCanvas':[a.shape[1],a.shape[0]],'removedNonzeroAlphaPixels':int(((a[:,:,3]>0)&~keep).sum()),'retainedRGBChanges':int(np.any(a[:,:,:3][keep]!=b[:,:,:3][keep],axis=1).sum()),'opaqueCorePixels':int(core.sum()),'method':'Largest connected alpha >=245 region; retain two-pixel edge with alpha >30; normalize opaque interior alpha; RGB unchanged inside retained subject.'}
(R/'reports/cleanup.json').write_text(json.dumps(report,indent=2))
print(report)
Image.fromarray(b).crop((365,20,650,310)).resize((855,870)).save(R/'reports/head_detail.png')
