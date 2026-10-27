"""Register generated-only eye artwork; derive masks and neutral display exports.

No image-generation call occurs in this build. Raw PNGs and prompts are retained.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
W, H = 1024, 1536
GEN = ROOT/'generation/eyes'
OUT = ROOT/'assets/eyes'
REPORTS = ROOT/'reports'
OUT.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
COMPONENTS = {}

# Uniform scale plus translation only; bbox coordinates are in the original
# 1024x1536 source. Full sclera is deliberately larger than its display opening.
PLACEMENT = {
 'upper_lid_screen_left': {'width':60,'x':430,'y':178.6},
 'upper_lid_screen_right': {'width':62,'x':525,'y':178.6},
 'lower_lid_screen_left': {'width':43,'x':443,'y':189},
 'lower_lid_screen_right': {'width':46,'x':532,'y':189},
 'eyewhite_screen_left': {'width':57,'x':438.5,'y':178.8},
 'eyewhite_screen_right': {'width':58,'x':525,'y':178.5},
 'iris_full_screen_left': {'width':28,'x':454,'y':173},
 'iris_full_screen_right': {'width':29,'x':534.5,'y':172},
 'brow_screen_left': {'width':39,'x':437,'y':151.8},
 'brow_screen_right': {'width':41,'x':531,'y':151.8},
}


def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()


def register(name):
 raw_path=GEN/f'{name}.png'
 image=Image.open(raw_path).convert('RGBA')
 a=np.array(image)
 labels,_=ndi.label(a[:,:,3]>16,structure=np.ones((3,3)))
 counts=np.bincount(labels.ravel());counts[0]=0
 # Keep the main stroke and intentional detached lashes, discard only tiny
 # isolated generation specks. No skin/iris/hair colour thresholds are used.
 keep_ids=np.flatnonzero(counts>=max(24,counts.max()*.0005))
 core=np.isin(labels,keep_ids)
 support=ndi.binary_dilation(core,iterations=3)
 removed=int(((a[:,:,3]>0)&~support).sum())
 a[~support]=0
 if name.startswith('eyewhite'):
  # Refine alpha at native generation size; 2px is <0.2% of the image width.
  hard=ndi.binary_opening(a[:,:,3]>127,iterations=2)
  hard=ndi.binary_closing(hard,iterations=2)
  alpha=Image.fromarray((hard*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.7))
  a[:,:,3]=np.array(alpha)
 image=Image.fromarray(a)
 hard=np.array(image.getchannel('A'))>16
 yy,xx=np.nonzero(hard);bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
 config=PLACEMENT[name];scale=config['width']/(bbox[2]-bbox[0])
 # Keep padding for antialiasing; resize once from the generated mother asset.
 pad=6;crop_box=(max(0,bbox[0]-pad),max(0,bbox[1]-pad),min(image.width,bbox[2]+pad),min(image.height,bbox[3]+pad))
 crop=image.crop(crop_box)
 size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
 small=crop.resize(size,Image.Resampling.LANCZOS)
 x=round(config['x']-(bbox[0]-crop_box[0])*scale)
 y=round(config['y']-(bbox[1]-crop_box[1])*scale)
 canvas=Image.new('RGBA',(W,H));canvas.alpha_composite(small,(x,y))
 if name.startswith('brow_'):file=f'assets/hair_refined/{name}.png'
 elif name.startswith('eyewhite_'):file=f'assets/eyes/eyewhite_full_{name[9:]}.png'
 else:file=f'assets/eyes/{name}.png'
 canvas.save(ROOT/file)
 # Retain cleaned high-resolution image as a reusable full artwork source.
 clean_path=GEN/f'{name}_clean.png';image.save(clean_path)
 COMPONENTS[name]={
  'generatedSource':str(raw_path.relative_to(ROOT)),
  'sourceSha256':sha(raw_path),'cleanedSource':str(clean_path.relative_to(ROOT)),
  'registeredFile':file,'sha256':sha(ROOT/file),'bbox':list(canvas.getbbox()),
  'sourceContentBox':list(bbox),'sourceSize':list(image.size),
  'transform':{'method':'uniform scale and translation','scale':scale,'x':x,'y':y,'resizedCrop':list(size)},
  'cleanup':{'method':'remove tiny isolated specks; sclera alpha opening/closing at source size only','removedSpeckPixels':removed},
 }
 return canvas


PARTS={name:register(name) for name in PLACEMENT}
# Apertures are technical geometry, not generated art. These reviewed source
# control points retain eye placement and are intersected with the full sclera.
SPECS={
 'screen_left':{'box':[431,171,491,214],'center':[468,193],
  'top':[(444,188),(451,181),(474,180),(484,189)],
  'bottom':[(484,189),(481,213),(458,222),(444,188)]},
 'screen_right':{'box':[526,171,588,214],'center':[549,193],
  'top':[(533,189),(542,181),(568,180),(578,188)],
  'bottom':[(578,188),(575,213),(546,222),(533,189)]},
}


def cubic(points):
 p=np.array(points);out=[]
 for t in np.linspace(0,1,128):
  q=(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3];out.append(tuple(q))
 return out


layers=[];stats={};masks={}
for side,spec in SPECS.items():
 scale=8;mask=Image.new('L',(W*scale,H*scale))
 points=cubic(spec['top'])+cubic(spec['bottom'])[1:]
 ImageDraw.Draw(mask).polygon([(round(x*scale),round(y*scale)) for x,y in points],fill=255)
 mask=mask.resize((W,H),Image.Resampling.LANCZOS)
 # Match the technical opening to the generated eyelid linework. This removes
 # both a gap below the upper lash and sclera spilling below the lower contour.
 # Only clipping geometry changes; no generated ink or RGB is repainted.
 upper=np.array(PARTS[f'upper_lid_{side}'].getchannel('A'))
 lower=np.array(PARTS[f'lower_lid_{side}'].getchannel('A'))
 labels,_=ndi.label(lower>16,structure=np.ones((3,3)))
 counts=np.bincount(labels.ravel());counts[0]=0
 contour=labels==counts.argmax()
 top=np.full(W,-1.0);bottom=np.full(W,float(H))
 for x in range(W):
  rows=np.flatnonzero(upper[:,x]>32)
  if len(rows):top[x]=rows.max()-.25
  rows=np.flatnonzero(contour[:,x])
  if len(rows):
   weights=lower[rows,x].astype(float)
   bottom[x]=float(np.average(rows,weights=weights))+.1
 # Smooth only within each stroke's coverage; never smear the H sentinel.
 for boundary,valid in [(top,top>=0),(bottom,bottom<H)]:
  if valid.any():
   xs=np.flatnonzero(valid);values=np.interp(np.arange(W),xs,boundary[valid])
   boundary[valid]=ndi.gaussian_filter1d(values,.65)[valid]
 yy=np.arange(H)[:,None]
 coverage=np.clip(yy-top[None,:]+.5,0,1)*np.clip(bottom[None,:]-yy+.5,0,1)
 mask=ImageChops.multiply(mask,Image.fromarray(np.rint(coverage*255).astype('uint8')))
 white=PARTS[f'eyewhite_{side}'].copy()
 mask=ImageChops.multiply(mask,white.getchannel('A'))
 masks[side]=mask
 mask.save(OUT/f'aperture_{side}.png')
 mask_alpha=Image.new('RGBA',(W,H),(255,255,255,0));mask_alpha.putalpha(mask)
 mask_alpha.save(OUT/f'aperture_alpha_{side}.png')
 # The visible sclera is the clipped export, its complete mother stays separate.
 white.putalpha(mask);white.save(OUT/f'eyewhite_{side}.png')
 iris=PARTS[f'iris_full_{side}'].copy()
 iris.putalpha(ImageChops.multiply(iris.getchannel('A'),mask));iris.save(OUT/f'iris_{side}.png')
 for name in [f'eyewhite_{side}',f'iris_{side}',f'lower_lid_{side}',f'upper_lid_{side}']:
  layers.append({'name':name,'file':f'assets/eyes/{name}.png','visible':True})
 stats[side]={'box':spec['box'],'center':spec['center'],'rangePixels':{'x':[-4,4],'y':[-2,2]},'painterOrder':[f'eyewhite_{side}',f'iris_{side}',f'lower_lid_{side}',f'upper_lid_{side}']}

manifest={'canvas':[W,H],'layers':layers,'eyes':stats,
 'runtime':{'iris':'assets/eyes/iris_full_{side}.png','aperture':'assets/eyes/aperture_{side}.png','apertureAlpha':'assets/eyes/aperture_alpha_{side}.png','clipping':'move full iris, destination-in true-alpha aperture derived from generated eyelid boundaries; fixed generated eyelids above','cameraTracking':False},
 'artwork':{'sourcePolicy':'generated-only','tool':'official built-in image_gen','model':'not exposed','generationCalls':14,'components':COMPONENTS,'scope':'8 eye components and 2 eyebrows; all other v3 artwork preserved'}}
(ROOT/'eye_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Standalone art inspection: every full component on light/dark/checker plates.
order=['upper_lid','lower_lid','eyewhite','iris_full','brow']
sheet=Image.new('RGB',(1350,5*260),'#242b35');draw=ImageDraw.Draw(sheet)
for row,kind in enumerate(order):
 for col,side in enumerate(['screen_left','screen_right']):
  name=f'{kind}_{side}';im=PARTS[name];bounds=im.getbbox();crop=im.crop((bounds[0]-2,bounds[1]-2,bounds[2]+2,bounds[3]+2))
  factor=min(8,620/crop.width,210/crop.height);crop=crop.resize((round(crop.width*factor),round(crop.height*factor)),Image.Resampling.LANCZOS)
  panel=Image.new('RGBA',(665,220),'#a6adb6');panel.alpha_composite(crop,((665-crop.width)//2,(220-crop.height)//2))
  x=col*675;y=row*260;sheet.paste(panel.convert('RGB'),(x+5,y+30));draw.text((x+8,y+7),f'{name} | generated mother -> uniform registration',fill='white')
sheet.save(REPORTS/'eye_group_components.png')
# Three backgrounds at generous zoom, keeping the whole layer visible.
for side in SPECS:
 combined=Image.new('RGBA',(W,H));combined.alpha_composite(Image.open(OUT/f'eyewhite_{side}.png'));combined.alpha_composite(Image.open(OUT/f'iris_{side}.png'))
 for kind in ['lower_lid','upper_lid']:combined.alpha_composite(PARTS[f'{kind}_{side}'])
 combined.alpha_composite(PARTS[f'brow_{side}'])
 box=(426,143,496,218) if side=='screen_left' else (519,143,591,218)
 crop=combined.crop(box).resize((560,600),Image.Resampling.LANCZOS)
 multi=Image.new('RGB',(1680,630));d=ImageDraw.Draw(multi)
 for i,color in enumerate(['#ffffff','#171c25','#a6adb6']):
  panel=Image.new('RGBA',crop.size,color);panel.alpha_composite(crop);multi.paste(panel.convert('RGB'),(i*560,30));d.text((i*560+8,8),f'{side} | {color}',fill='white')
 multi.save(REPORTS/f'eye_group_{side}_backgrounds.png')
print(json.dumps({'registeredGeneratedComponents':len(COMPONENTS),'eyeLayers':len(layers),'sourcePolicy':'generated-only'}))
