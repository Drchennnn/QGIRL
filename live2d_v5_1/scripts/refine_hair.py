"""Register official hair isolation and split the fringe; no generation at build time."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Image.open(ROOT / 'assets/front_master_clean.png').convert('RGBA')
W, H = SOURCE.size
Y, X = np.indices((H, W))
A = np.array(SOURCE)
OUT = ROOT / 'assets/hair_refined'
OUT.mkdir(exist_ok=True)
SOURCE_V1 = ROOT.parent / 'live2d_v1/assets/head'


def save(name, array):
    image = array if isinstance(array, Image.Image) else Image.fromarray(array)
    image.save(OUT / f'{name}.png')
    return {'name': name, 'file': f'assets/hair_refined/{name}.png', 'visible': True}


def ellipse(box):
    mask = Image.new('L', (W, H))
    ImageDraw.Draw(mask).ellipse(box, fill=255)
    return np.array(mask)


def ear(side):
    # The legacy ear rectangle also contains hair. Keep the actual warm ear
    # component and its one-pixel outline, using only the reviewed source.
    rgb = A[:, :, :3].astype(int)
    warm = (rgb[:, :, 0] > rgb[:, :, 1]+5) & (rgb[:, :, 1] > rgb[:, :, 2]+2)
    if side == 'screen_left':
        roi = (X >= 410) & (X < 438) & (Y >= 182) & (Y < 229)
    else:
        roi = (X >= 587) & (X < 612) & (Y >= 180) & (Y < 228)
    labels, _ = ndi.label(warm & roi & (rgb[:, :, 0] > 155))
    counts = np.bincount(labels.ravel()); counts[0] = 0
    selected = ndi.binary_fill_holes(labels == counts.argmax())
    selected = ndi.binary_dilation(selected, iterations=1) & roi
    coverage = np.array(Image.fromarray((selected*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45)))
    image = A.copy(); image[:, :, 3] = np.minimum(A[:, :, 3], coverage)
    return image, coverage


generated_path = ROOT / 'generation/hair_official_cutout.png'
generated = Image.open(generated_path).convert('RGBA')
g = np.array(generated)
components, _ = ndi.label(g[:, :, 3] > 8)
counts = np.bincount(components.ravel()); counts[0] = 0
main = ndi.binary_dilation(components == counts.argmax(), iterations=2)
g[~main] = 0  # discard isolated nearly transparent generation specks
registered = Image.new('RGBA', (W, H))
registered.alpha_composite(Image.fromarray(g).resize((290, 300), Image.Resampling.LANCZOS), (365, 15))
hair = np.array(registered)
ears = {}
for side in ('screen_left', 'screen_right'):
    image, mask = ear(side)
    ears[side] = image
    # The generated isolation covered the original ear opening with hair.
    hair[:, :, 3] = ((hair[:, :, 3].astype(np.uint16)*(255-mask))//255).astype('uint8')

# Select the detached central fringe below its pinned root, following the
# transparent face gaps rather than thresholding colours along the hairline.
solid = (hair[:, :, 3] > 8) & (Y >= 132)
components, _ = ndi.label(solid)
seed = components[145, 500]
assert seed != 0, 'Missing central fringe in registered cutout'
component = ndi.binary_dilation(components == seed, iterations=2) & (Y >= 132)
root = (Y >= 82) & (Y < 132) & (X >= 471) & (X <= 525)
central = component | root
fringe = np.zeros_like(hair); fringe[central] = hair[central]
fixed = hair.copy(); fixed[central] = 0
# Hidden root overlap ends before the onset of motion, preventing a root seam.
root_back = (Y >= 82) & (Y < 126) & central
fixed[root_back] = hair[root_back]

face = np.array(Image.open(SOURCE_V1 / 'face.png').convert('RGBA'))
upper_mask = ((ellipse((423, 79, 596, 274)) > 0) | (face[:, :, 3] > 0)) & (Y < 215)
face[upper_mask] = [252, 228, 218, 255]
back = np.zeros_like(A)
back[ellipse((410, 27, 613, 235)) > 0] = [45, 51, 67, 255]
rgb = A[:, :, :3].astype(int)
neck_skin = (Y >= 245) & (Y < 302) & (X >= 475) & (X < 551) & (rgb[:, :, 0] > rgb[:, :, 1]+5) & (rgb[:, :, 1] > rgb[:, :, 2]+2)
neck_skin = ndi.binary_dilation(neck_skin, iterations=2) & (Y >= 245) & (Y < 302) & (X >= 475) & (X < 551)
neck_bridge = np.zeros_like(A); neck_bridge[neck_skin] = A[neck_skin]
layers = [save('hair_back', back), save('neck_bridge', neck_bridge), save('face', face)]
layers.extend(save(f'ear_{side}', image) for side, image in ears.items())
for side, box in [('screen_left', (435, 148, 477, 159)), ('screen_right', (529, 148, 574, 161))]:
    x0, y0, x1, y1 = box
    brow = np.zeros_like(A); brow[y0:y1, x0:x1] = A[y0:y1, x0:x1]
    rgb = brow[:, :, :3].astype(int)
    keep = (brow[:, :, 3] > 0) & (rgb.max(axis=2) < 160)
    brow[~keep] = 0
    layers.append(save(f'brow_{side}', brow))
for name in ('nose', 'mouth'):
    layers.append(save(name, Image.open(SOURCE_V1 / f'{name}.png').convert('RGBA')))
layers.extend([save('hair_front_fixed', fixed), save('hair_fringe_center', fringe)])
manifest = {
    'canvas': [W, H], 'layers': layers,
    'eyeSlot': {'after': 'ear_screen_right', 'before': 'brow_screen_left'},
    'motion': {'rootFixedUntilY': 132, 'fullMovementFromY': 176, 'rangePixels': [-3, 3]},
    'source': {
        'file': 'generation/hair_official_cutout.png',
        'sha256': hashlib.sha256(generated_path.read_bytes()).hexdigest(),
        'method': 'Official built-in image generation; semantic transparent hair isolation',
        'model': 'not exposed by built-in tool',
        'registration': {'sourceCrop': [365, 15, 655, 315], 'size': [290, 300]},
    },
}
(ROOT / 'hair_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
Image.fromarray(hair).save(ROOT / 'generation/hair_registered.png')
print(json.dumps({'layers': len(layers), 'movingFringePixels': int((fringe[:, :, 3]>0).sum()), 'officialCutout': str(generated_path)}))
