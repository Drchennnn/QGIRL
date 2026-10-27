from pathlib import Path
import json
from PIL import Image,ImageChops,ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[1];spec=json.loads((R/'eye_manifest.json').read_text());src=Image.open(R/'assets/front_master_clean.png').convert('RGBA')
def eye_image(side,dx=0,dy=0):
 white=Image.open(R/f'assets/eyes/eyewhite_{side}.png').convert('RGBA');iris=Image.open(R/f'assets/eyes/iris_{side}.png').convert('RGBA');mask=Image.open(R/f'assets/eyes/aperture_{side}.png').convert('L');socket=Image.open(R/f'assets/eyes/eye_socket_{side}.png').convert('RGBA')
 moved=Image.new('RGBA',src.size);moved.alpha_composite(iris,(dx,dy));moved.putalpha(ImageChops.multiply(moved.getchannel('A'),mask));white.alpha_composite(moved);white.alpha_composite(socket)
 assert not np.any((np.array(moved.getchannel('A'))>0)&(np.array(mask)==0))
 return white
poses=[('original',None),('neutral',(0,0)),('left',(-4,0)),('right',(4,0)),('up',(0,-2)),('down',(0,2))]
sheet=Image.new('RGB',(990,6*260),'#d4d6d8');d=ImageDraw.Draw(sheet)
for i,(name,xy) in enumerate(poses):
 im=src.copy()
 if xy:
  for side in spec['eyes']:im.alpha_composite(eye_image(side,*xy))
 crop=im.crop((425,165,590,215)).resize((990,300));sheet.paste(crop.crop((0,0,990,235)),(0,i*260),crop.crop((0,0,990,235)));d.text((5,i*260+240),name,fill='black')
sheet.save(R/'reports/eye_motion.jpg')
