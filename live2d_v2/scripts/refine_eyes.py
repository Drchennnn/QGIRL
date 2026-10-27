from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1]; A=np.array(Image.open(R/'assets/front_master_clean.png').convert('RGBA'));H,W=A.shape[:2]
OUT=R/'assets/eyes';OUT.mkdir(exist_ok=True)
def polygon(points):
 im=Image.new('L',(W,H));ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)
# Source-image coordinates; screen names never infer character-side names.
specs={
'screen_left':{'box':[431,171,490,212],'aperture':[(444,187),(449,184),(457,183),(470,183),(478,185),(483,190),(482,199),(478,205),(472,210),(460,211),(450,205),(446,199)],'iris':[(457,179),(474,179),(480,183),(480,194),(478,201),(474,205),(470,207),(464,207),(460,204),(457,199),(455,190)],'center':[468,193]},
'screen_right':{'box':[526,170,586,212],'aperture':[(533,190),(537,186),(544,182),(555,181),(565,183),(574,185),(577,188),(575,198),(570,204),(561,210),(546,211),(537,205),(533,199)],'iris':[(539,179),(553,177),(560,179),(562,186),(561,195),(558,201),(554,206),(545,207),(541,205),(537,199),(535,190)],'center':[549,193]}}
layers=[];stats={}
for side,s in specs.items():
 aperture=polygon(s['aperture']);iris_mask=polygon(s['iris']);inside=iris_mask>0
 x0,y0,x1,y1=s['box']
 yy,xx=np.indices((H,W));rgb=A[:,:,:3].astype(float)
 roi=(xx>=x0+7)&(xx<x1-5)&(yy>=181)&(yy<=210)
 chroma=(rgb[:,:,2]-rgb[:,:,0]>13)|((np.abs(rgb[:,:,0]-rgb[:,:,1])<12)&(rgb.min(axis=2)>145))
 raw=roi&chroma
 lab,n=ndi.label(raw);counts=np.bincount(lab.ravel());counts[0]=0;raw=lab==counts.argmax()
 raw=ndi.binary_fill_holes(raw)
 raw=ndi.binary_closing(raw,iterations=1)
 aperture=np.array(Image.fromarray((raw*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.65)))
 # Blue-black outer lashes can pass the blue-chroma eye test. Keep these
 # stationary source pixels outside the reviewed iris contour as occluders.
 aperture[(rgb.max(axis=2)<130)&~inside]=0
 surface=np.zeros_like(A);surface[y0:y1,x0:x1]=A[y0:y1,x0:x1]
 # Continuous sclera replaces the entire aperture, including all old iris pixels.
 for y in range(y0,y1):
  xx=np.flatnonzero(aperture[y]>0)
  if not len(xx):continue
  grey=int(np.interp(y,[181,185,191,211],[187,212,245,246]))
  surface[y,xx,:3]=[grey, min(grey+1,255),min(grey+3,255)];surface[y,xx,3]=255
 # Isolate the iris against white using its source blue chroma, retaining highlights.
 iris=np.zeros_like(A)
 cx,cy=s['center'];rx=13 if side=='screen_left' else 14
 for y in range(170,212):
  for x in range(cx-rx-3,cx+rx+4):
   if y<181:
    if abs(x-cx)<rx-1:iris[y,x]=[27,43,61,255]
    continue
   rgb=A[y,x,:3].astype(float)
   # Restrict to the curved iris contour; reject sclera and skin.
   bottom=208; half=rx if y<195 else rx*np.sqrt(max(0,1-((y-195)/14)**2))
   if abs(x-cx)>half+1:continue
   blue=rgb[2]-rgb[0]
   is_highlight=(y<190 and x<cx-2 and rgb.min()>170)
   if blue>12 or rgb.max()<110 or is_highlight:
    iris[y,x]=A[y,x]
 # Smooth complete iris contour; source blue texture is extended only at its rim.
 scale=4;mask_hi=Image.new('L',(W*scale,H*scale));draw=ImageDraw.Draw(mask_hi)
 draw.ellipse(((cx-rx)*scale,169*scale,(cx+rx)*scale,208*scale),fill=255)
 alpha=np.array(mask_hi.resize((W,H),Image.Resampling.LANCZOS))
 valid=(iris[:,:,3]>0)&(np.max(iris[:,:,:3],axis=2)>0)&ndi.binary_erosion(inside,iterations=2)
 nearest=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
 iris[:,:,:3]=iris[nearest[0],nearest[1],:3];iris[:,:,3]=alpha
 # Repaint only the movable iris at 4x, keeping the established U motif.
 sprite=Image.new('RGBA',(W*scale,H*scale));dr=ImageDraw.Draw(sprite)
 dr.ellipse(((cx-rx)*scale,167*scale,(cx+rx)*scale,208*scale),fill=(27,43,61,255))
 def curve(p):
  pts=[]
  for t in np.linspace(0,1,24):
   v=(1-t)**3*np.array(p[0])+3*(1-t)**2*t*np.array(p[1])+3*(1-t)*t*t*np.array(p[2])+t**3*np.array(p[3]);pts.append(tuple(v))
  return pts
 pts=curve([(cx-rx+2,195),(cx-rx+5,190),(cx-6,190),(cx-5,196)])
 pts+=curve([(cx-5,196),(cx-2,201),(cx+2,201),(cx+5,195)])
 pts+=curve([(cx+5,195),(cx+7,190),(cx+rx-4,191),(cx+rx-2,195)])
 pts+=curve([(cx+rx-2,195),(cx+rx-3,210),(cx-rx+3,211),(cx-rx+2,195)])
 dr.polygon([(int(x*scale),int(y*scale)) for x,y in pts],fill=(79,181,210,255))
 dr.ellipse(((cx-rx+1)*scale,183*scale,(cx-rx+8)*scale,188*scale),fill=(241,251,249,255))
 iris=np.array(sprite.resize((W,H),Image.Resampling.LANCZOS))
 # Preserve source lashes outside the aperture on a foreground occluder.
 occ=A.copy();occ[:y0]=0;occ[y1:]=0;occ[:,:x0]=0;occ[:,x1:]=0;occ[:,:,3]=np.minimum(occ[:,:,3],255-aperture)
 white=surface.copy();white[:,:,3]=aperture
 for name,img in [('eye_socket_'+side,occ),('eyewhite_'+side,white),('iris_'+side,iris)]:
  Image.fromarray(img).save(OUT/(name+'.png'))
 Image.fromarray(aperture).save(OUT/('aperture_'+side+'.png'))
 # The PSD contains a clipped neutral iris; the full movable iris is a separate PNG.
 neutral=Image.fromarray(iris)
 neutral.putalpha(ImageChops.multiply(neutral.getchannel('A'),Image.fromarray(aperture)))
 neutral.save(OUT/('iris_neutral_'+side+'.png'))
 layers.extend([{'name':'eyewhite_'+side,'file':'assets/eyes/eyewhite_'+side+'.png','visible':True},{'name':'iris_'+side,'file':'assets/eyes/iris_neutral_'+side+'.png','visible':True},{'name':'eye_socket_'+side,'file':'assets/eyes/eye_socket_'+side+'.png','visible':True}])
 stats[side]={'box':s['box'],'center':s['center'],'rangePixels':{'x':[-4,4],'y':[-2,2]},'irisPixels':int(inside.sum())}
(R/'eye_manifest.json').write_text(json.dumps({'canvas':[W,H],'layers':layers,'eyes':stats,'runtime':{'iris':'assets/eyes/iris_{side}.png','aperture':'assets/eyes/aperture_{side}.png','clipping':'translate iris then destination-in stationary aperture','cameraTracking':False}},indent=2))
print(json.dumps(stats))
