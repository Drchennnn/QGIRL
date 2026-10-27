from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1]
A=np.array(Image.open(R/'assets/front_master_clean.png').convert('RGBA')); H,W=A.shape[:2]
Y,X=np.indices((H,W)); active=A[:,:,3]>0
body=(Y>=300)|((Y>=270)&(X>=482)&(X<=537))
head=active&~body
out=R/'assets/head';out.mkdir(exist_ok=True)
def poly(points):
    im=Image.new('1',(W,H));ImageDraw.Draw(im).polygon(points,fill=1);return np.array(im,dtype=bool)
def ellipse(box):
    im=Image.new('1',(W,H));ImageDraw.Draw(im).ellipse(box,fill=1);return np.array(im,dtype=bool)
def box(x0,y0,x1,y1):return (X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1)
labels=np.full((H,W),'',dtype=object)
face_outline=poly([(471,112),(524,112),(548,164),(575,175),(582,199),(569,227),(560,243),(544,254),(510,272),(481,259),(458,244),(449,225),(438,203),(438,179)])
face=face_outline&head
# The forehead strands remain hair; skin beneath them is completed separately.
dark=np.max(A[:,:,:3],axis=2)<150
skin=(A[:,:,0].astype(int)>A[:,:,1].astype(int)+6)&(A[:,:,1].astype(int)>A[:,:,2].astype(int)+2)&(np.min(A[:,:,:3],axis=2)>125)
face &= skin | (ndi.binary_dilation(skin,iterations=2)&(Y>=237)&(Y<=273))
face |= skin&ellipse((430,82,590,273))&head&(Y<237)
labels[head]='hair_back'
labels[head&(Y<228)&(X>=409)&(X<=607)]='hair_crown'
labels[head&poly([(470,81),(520,71),(542,116),(553,164),(561,184),(532,187),(500,190),(476,180),(466,151)])]='hair_fringe_center'
labels[head&poly([(432,98),(469,74),(476,95),(462,131),(451,169),(447,200),(456,231),(469,263),(484,293),(461,302),(437,278),(424,232),(417,185)])]='hair_side_screen_left'
labels[head&poly([(547,84),(578,106),(600,159),(603,218),(588,269),(557,301),(539,298),(559,267),(572,229),(582,190),(572,145)])]='hair_side_screen_right'
labels[face]='face'
earL=poly([(420,181),(430,185),(437,208),(447,231),(437,230),(420,218),(411,202)])&head
earR=poly([(597,180),(606,190),(610,205),(600,220),(587,231),(584,213)])&head
labels[earL]='ear_screen_left';labels[earR]='ear_screen_right'
# White inner hair streaks are independent of the surrounding dark hair.
light=(np.min(A[:,:,:3],axis=2)>125)&(np.max(A[:,:,:3],axis=2)-np.min(A[:,:,:3],axis=2)<34)
for side,region in [('screen_left',box(399,216,466,296)),('screen_right',box(548,219,623,295))]:
    m=light&region&head&np.char.startswith(labels.astype(str),'hair')
    labels[m]='hair_streak_'+side
clip=box(413,122,444,168)&head&((A[:,:,0].astype(int)>A[:,:,2].astype(int)+35)|((A[:,:,1]>130)&(A[:,:,0]<185)))
clip=ndi.binary_dilation(clip,iterations=1)&head
labels[clip]='clip_screen_left'
for side,region in [('screen_left',box(442,151,474,158)),('screen_right',box(531,150,569,160))]:
    m=region&head&(np.min(A[:,:,:3],axis=2)<165)&ndi.binary_dilation(skin,iterations=2)
    labels[ndi.binary_dilation(m,iterations=1)&head]='brow_'+side
eye_polys={
 'screen_left':([(433,178),(447,173),(466,173),(480,177),(490,185),(483,183),(480,197),(476,205),(468,210),(454,208),(445,201),(440,190)],(456,178,483,210)),
 'screen_right':([(526,185),(532,177),(548,173),(565,172),(584,177),(580,187),(572,200),(560,210),(544,209),(535,201),(533,188)],(535,176,562,210))}
eye_apertures={}
for side,(points,irisbox) in eye_polys.items():
    eye=poly(points)&head
    # Partition exact source pixels, including upper lashes and lower outlines.
    upper=eye&(Y<=np.where(side=='screen_left',180,179))
    upper|=eye&dark&(Y<187)&~box(*irisbox)
    iris=eye&ellipse(irisbox)&~upper
    white=eye&~upper&~iris
    lower=white&dark&(Y>196)
    labels[white]='eyewhite_'+side;labels[iris]='iris_'+side
    labels[upper]='upper_lid_'+side;labels[lower]='lower_lid_'+side
    eye_apertures[side]=eye&~upper
for name,region in [('nose',box(504,213,513,224)),('mouth',box(493,231,525,242))]:
    m=region&head&(np.min(A[:,:,:3],axis=2)<210)
    labels[ndi.binary_dilation(m,iterations=1)&head]=name
# Move fringe/eye antialias edge pixels off the face backing. They remain
# exact source pixels on the corresponding movable foreground component.
residual=(labels=='face')&(np.min(A[:,:,:3],axis=2)<215)&(Y<233)
labels[residual&(Y<170)&(X<480)]='hair_side_screen_left'
labels[residual&(Y<170)&(X>=530)]='hair_side_screen_right'
labels[residual&(Y<188)&(X>=480)&(X<530)]='hair_fringe_center'
for side,region in [('screen_left',box(435,170,490,212)),('screen_right',box(526,169,587,212))]:
    labels[residual&region]='upper_lid_'+side
labels[residual&(Y>=212)&(X<460)]='hair_side_screen_left'
labels[residual&(Y>=212)&(X>561)]='hair_side_screen_right'
stray=(labels=='hair_back')&face_outline&head
labels[stray&(X<480)]='hair_side_screen_left'
labels[stray&(X>535)]='hair_side_screen_right'
labels[stray&(X>=480)&(X<=535)&(Y<237)]='hair_fringe_center'
order=['hair_back','ear_screen_left','ear_screen_right','face','hair_crown',
       'hair_side_screen_left','hair_side_screen_right','hair_streak_screen_left','hair_streak_screen_right',
       'brow_screen_left','brow_screen_right','eyewhite_screen_left','eyewhite_screen_right',
       'iris_screen_left','iris_screen_right','upper_lid_screen_left','upper_lid_screen_right',
       'lower_lid_screen_left','lower_lid_screen_right','nose','mouth','hair_fringe_center','clip_screen_left']
masks={n:(labels==n)&head for n in order};layers=[];stats={}
def backing(name, mask, color):
    b=np.zeros_like(A);b[mask,:3]=color;b[mask,3]=255;return b
for i,name in enumerate(order):
    visible=masks[name]
    if not visible.any():continue
    b=np.zeros_like(A)
    # Concealed additions only occupy fully opaque pixels owned by a later layer.
    later=np.zeros((H,W),dtype=bool)
    for n in order[i+1:]:later|=masks[n]
    eligible=later&(A[:,:,3]==255)
    extra=np.zeros((H,W),dtype=bool)
    if name=='face':
        extra=ellipse((424,84,593,273))&eligible
        b=backing(name,extra,[252,228,218])
    elif name=='hair_back':
        extra=ellipse((399,40,620,289))&eligible
        b=backing(name,extra,[49,54,69])
    elif name.startswith('eyewhite_'):
        side=name[len('eyewhite_'):];extra=eye_apertures[side]&eligible
        b=backing(name,extra,[246,247,248])
    elif name.startswith('iris_'):
        side=name[len('iris_'):];extra=ellipse(eye_polys[side][1])&eligible
        near=ndi.distance_transform_edt(~visible,return_distances=False,return_indices=True)
        b[extra]=A[near[0][extra],near[1][extra]];b[extra,3]=255
    elif name.startswith('hair_') or name.startswith('ear_'):
        extra=ndi.binary_dilation(visible,iterations=7)&eligible
        if name.startswith('hair_'):
            extra &= ~((masks['hair_fringe_center'])&(Y>137))
        near=ndi.distance_transform_edt(~visible,return_distances=False,return_indices=True)
        b[extra]=A[near[0][extra],near[1][extra]];b[extra,3]=255
    b[visible]=A[visible]
    Image.fromarray(b).save(out/(name+'.png'))
    layers.append({'name':name,'file':'assets/head/'+name+'.png','visible':True})
    stats[name]={'visiblePixels':int(visible.sum()),'concealedPaintPixels':int(extra.sum())}
combined=Image.new('RGBA',(W,H))
for item in layers:combined.alpha_composite(Image.open(R/item['file']))
expected=A.copy();expected[~head]=0
got=np.array(combined);active2=(got[:,:,3]>0)|(expected[:,:,3]>0)
changed=int((np.any(got!=expected,axis=2)&active2).sum())
assert changed==0,changed
combined.save(R/'reports/head_reassembled.png')
(R/'head_manifest.json').write_text(json.dumps({'canvas':[W,H],'coordinateConvention':'screen left/right','layers':layers,'boundary':'body y>=300 OR (y>=270 AND 482<=x<=537)','validation':{'neutralChangedPixels':changed},'paintMethod':'Local flat-colour and nearest-source extension in concealed pixels only; no AI regeneration.','layerStats':stats},indent=2))
print(json.dumps({'layers':len(layers),'neutralChangedPixels':changed,'concealedPaintPixels':sum(v['concealedPaintPixels'] for v in stats.values())}))
