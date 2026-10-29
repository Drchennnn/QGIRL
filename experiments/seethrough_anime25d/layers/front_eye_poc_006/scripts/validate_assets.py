from pathlib import Path
from PIL import Image
from psd_tools import PSDImage
import numpy as np,json,hashlib
p=Path(__file__).resolve().parents[1];src=p.parent/'front_hair_poc_003_3/exports'
def arr(f):return np.array(Image.open(f).convert('RGBA'))
def diff(a,b):return np.any(a!=b,2)&((a[:,:,3]>0)|(b[:,:,3]>0))
a=arr(src/'neutral.png');b=arr(p/'exports/neutral.png');r=np.zeros((1024,1024),bool);r[490:645,280:500]=1;r[485:645,565:800]=1
changed=diff(a,b);assert not(changed&~r).any();assert np.array_equal(b,arr(p/'exports/neutral_restored.png'))
psd=PSDImage.open(p/'exports/anime25d_adapter.psd');assert len(psd)==20
layerchecks=[]
for i,node in enumerate(reversed(list(psd))):
 f=p/'exports/adapter_layers'/f'rig_{i:04d}_{node.name}.png';d=arr(f);im=np.array(node.topil().convert('RGBA'));raw=np.zeros_like(d);x0,y0,x1,y1=node.bbox;raw[y0:y1,x0:x1]=im;assert not diff(raw,d).any(),node.name;assert node.visible
 cyan=lambda c:int(((c[:,:,0].astype('int16')<150)&(c[:,:,1].astype('int16')>c[:,:,0].astype('int16')+10)&(c[:,:,2].astype('int16')>c[:,:,0].astype('int16')+15)&(c[:,:,3]>0)).sum())
 q={'name':node.name,'visible':True,'rawVisibleRGBAMatchesPNG':True}
 if node.name.startswith('eyewhite'):
  dark=int(((np.max(d[:,:,:3],2)<110)&(d[:,:,3]>127)).sum());assert dark==0,(node.name,dark);assert cyan(d)==0;q.update(darkPixels=dark,cyanPixels=0)
 if node.name.startswith('face'):
  c=d[495:635,290:790];assert cyan(c)==0,(node.name,cyan(c));q['eyeRegionCyanPixels']=0
 layerchecks.append(q)
closed={}
for f in(p/'exports').glob('closed_*.png'):
 d=arr(f);delta=diff(b,d);assert not(delta&~r).any();checks={}
 for side,(x0,x1)in {'left':(320,480),'right':(590,760)}.items():
  if 'both'in f.stem or side in f.stem:checks[side]=cyan(d[540:618,x0:x1]);assert checks[side]==0
 closed[f.name]={'outsideEyeROIChangedPixels':int((delta&~r).sum()),'closedEyeCyanPixels':checks}
files={str(f.relative_to(p/'exports')):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in(p/'exports').rglob('*')if f.is_file()}
report={'status':'technical_pass_pending_art_and_upstream','adapterLayers':20,'workingLayers':27,'neutralChangedVisiblePixelsVs003_3':int(changed.sum()),'neutralOutsideEyeROIChangedPixels':0,'neutralRestoredExactRGBA':True,'eyeROIs':[[280,490,500,645],[565,485,800,645]],'adapterReadback':layerchecks,'nativeClosed':closed,'files':files,'newImageGenerations':0,'modalRuns':0,'limits':['adapter closed-lash layers deliberately visible for import;not intended as flattened neutral','runtime material appearance and clipping require separate real-upstream visual review']}
(p/'reports/asset_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS20-layer PSD raw visibleRGBA readback;pure whites no dark/cyan;face eye-region cyan0;nativeclosed3states;neutraloutside0;neutralchanged',int(changed.sum()))
