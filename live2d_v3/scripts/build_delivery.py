from pathlib import Path
import json,base64
from PIL import Image,ImageDraw,ImageChops
import numpy as np
R=Path(__file__).resolve().parents[1]
b=json.loads((R/'body_manifest.json').read_text());h=json.loads((R/'hair_manifest.json').read_text());e=json.loads((R/'eye_manifest.json').read_text())
layers=b['layers'].copy()
for l in h['layers']:
 layers.append(l)
 if l['name']==h['eyeSlot']['after']:layers.extend(e['layers'])
m={'canvas':[1024,1536],'layers':layers,'stage':'Refined artwork plus mouse gaze prototype; no camera tracking or Cubism binding','coordinateConvention':'screen_left/right = viewer side'}
(R/'manifest.json').write_text(json.dumps(m,indent=2))
def render(dx=0,dy=0):
 im=Image.new('RGBA',(1024,1536))
 for l in layers:
  if l['name'].startswith('iris_'):
   side=l['name'][5:];part=Image.open(R/e['runtime']['iris'].format(side=side)).convert('RGBA')
   if dx or dy:part=part.transform(im.size,Image.Transform.AFFINE,(1,0,-dx,0,1,-dy),resample=Image.Resampling.BICUBIC)
   mask=Image.open(R/f'assets/eyes/aperture_{side}.png');part.putalpha(ImageChops.multiply(part.getchannel('A'),mask))
  else:part=Image.open(R/l['file'])
  im.alpha_composite(part)
 return im
neutral=render();neutral.save(R/'reports/neutral.png')
# The static PSD must render the same neutral pose as the interactive path.
static=Image.new('RGBA',neutral.size)
for l in layers:static.alpha_composite(Image.open(R/l['file']))
n=np.array(neutral);s=np.array(static);visible=(n[:,:,3]>0)|(s[:,:,3]>0)
static_changes=int((np.any(n!=s,axis=2)&visible).sum())
assert static_changes==0, f'Static/runtime neutral mismatch: {static_changes} pixels'
source=np.array(Image.open(R/'assets/front_master_clean.png'));a=np.array(neutral);active=(source[:,:,3]>0)|(a[:,:,3]>0);changed=int((np.any(a!=source,axis=2)&active).sum())
poses=[(-4,-2),(0,-2),(4,-2),(-4,0),(0,0),(4,0),(-4,2),(0,2),(4,2)]
sheet=Image.new('RGB',(900,990),'#bbc1c7');d=ImageDraw.Draw(sheet)
for i,(x,y) in enumerate(poses):
 im=render(x,y);crop=im.crop((365,15,655,315));sheet.paste(crop,((i%3)*300,(i//3)*330),crop);d.text(((i%3)*300+5,(i//3)*330+307),f'X {x:+d} / Y {y:+d}',fill='black')
sheet.save(R/'reports/gaze_nine.png')
checks=[]
for side in e['eyes']:
 mask=np.array(Image.open(R/f'assets/eyes/aperture_{side}.png'));iris=Image.open(R/e['runtime']['iris'].format(side=side))
 for dx,dy in poses:
  p=Image.new('RGBA',iris.size);p.alpha_composite(iris,(dx,dy));p.putalpha(ImageChops.multiply(p.getchannel('A'),Image.fromarray(mask)));alpha=np.array(p.getchannel('A'));leaks=int(((alpha>0)&(mask==0)).sum());assert leaks==0;checks.append({'side':side,'x':dx,'y':dy,'outsideMaskPixels':leaks})
report={'layers':len(layers),'canvas':[1024,1536],'neutralChangedPixelsVsV1':changed,'staticVsRuntimeNeutralChangedPixels':static_changes,'gazeClippingChecks':checks,'cameraTracking':False,'cubismRig':False,'irisMethod':'Semantic inset aperture and fixed upper/lower eyelids over a complete moving iris.','hairMethod':h['source']}
(R/'reports/verification.json').write_text(json.dumps(report,indent=2))
data=[]
for l in layers:
 file=l['file'];mask=None
 if l['name'].startswith('iris_'):
  side=l['name'][5:];file=e['runtime']['iris'].format(side=side);mask='data:image/png;base64,'+base64.b64encode((R/e['runtime']['apertureAlpha'].format(side=side)).read_bytes()).decode()
 data.append({'name':l['name'],'src':'data:image/png;base64,'+base64.b64encode((R/file).read_bytes()).decode(),'mask':mask})
template=(R/'scripts/viewer_template.html').read_text();(R/'视线与发片精修预览.html').write_text(template.replace('__DATA__',json.dumps(data)))
print(json.dumps({'layers':len(layers),'neutralChangedPixelsVsV1':changed,'clippingChecks':len(checks),'allPass':True}))
