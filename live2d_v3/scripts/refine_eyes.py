"""Build semantic gaze layers with eyelids above the moving irises."""
from pathlib import Path
import json

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = np.array(Image.open(ROOT / 'assets/front_master_clean.png').convert('RGBA'))
H, W = SOURCE.shape[:2]
OUT = ROOT / 'assets/eyes'
OUT.mkdir(exist_ok=True)
SCALE = 8

# The opening is intentionally inset from the painted lash edge. Curves are
# listed left-to-right in source-image coordinates (screen side, never inferred
# character side). The full iris remains larger and moves behind this opening.
SPECS = {
    'screen_left': {
        'box': [431, 171, 490, 213], 'center': [468, 193], 'radius': 13,
        'top': [(444, 188), (451, 181), (474, 180), (484, 189)],
        'bottom': [(484, 189), (481, 213), (458, 222), (444, 188)],
        'lash': [(434, 185), (449, 178), (478, 179), (488, 184)],
    },
    'screen_right': {
        'box': [526, 171, 586, 213], 'center': [549, 193], 'radius': 14,
        'top': [(533, 189), (542, 181), (568, 180), (578, 188)],
        'bottom': [(578, 188), (575, 213), (546, 222), (533, 189)],
        'lash': [(527, 184), (542, 178), (571, 178), (584, 183)],
    },
}


def cubic(control, samples=96):
    p = np.asarray(control, dtype=float)
    result = []
    for t in np.linspace(0, 1, samples):
        point = ((1-t)**3*p[0] + 3*(1-t)**2*t*p[1] +
                 3*(1-t)*t*t*p[2] + t**3*p[3])
        result.append(tuple(point))
    return result


def supersampled_polygon(points):
    mask = Image.new('L', (W*SCALE, H*SCALE))
    ImageDraw.Draw(mask).polygon([(round(x*SCALE), round(y*SCALE)) for x, y in points], fill=255)
    return mask.resize((W, H), Image.Resampling.LANCZOS)


def curve_strip(spec, which):
    curve = cubic(spec['top'] if which == 'upper' else spec['bottom'])
    if which == 'upper':
        outer = [(x, y-5) for x, y in curve]
        inner = [(x, y+1) for x, y in reversed(curve)]
    else:
        outer = [(x, y-1) for x, y in curve]
        inner = [(x, y+3) for x, y in reversed(curve)]
    return supersampled_polygon(outer + inner)


def upper_lash_mask(spec):
    curve = cubic(spec['lash'])
    outer = [(x, y-3) for x, y in curve]
    inner = [(x, y+2) for x, y in reversed(curve)]
    return supersampled_polygon(outer + inner)


def recolor_chromatic_lid(image):
    """Remove any fixed blue iris cap accidentally sampled into a lid band."""
    rgb = image[:, :, :3].astype(int)
    chromatic = ((image[:, :, 3] > 0) &
                 (rgb[:, :, 2] - rgb[:, :, 0] > 20) &
                 (rgb[:, :, 1] - rgb[:, :, 0] > 10))
    image[chromatic, :3] = [24, 31, 47]
    return image


def build_iris(cx, radius):
    canvas = Image.new('RGBA', (W*SCALE, H*SCALE))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse(((cx-radius)*SCALE, 167*SCALE,
                  (cx+radius)*SCALE, 210*SCALE), fill=(27, 43, 61, 255))
    points = []
    segments = [
        [(cx-radius+2, 195), (cx-radius+5, 190), (cx-6, 190), (cx-5, 196)],
        [(cx-5, 196), (cx-2, 201), (cx+2, 201), (cx+5, 195)],
        [(cx+5, 195), (cx+7, 190), (cx+radius-4, 191), (cx+radius-2, 195)],
        [(cx+radius-2, 195), (cx+radius-3, 210), (cx-radius+3, 211), (cx-radius+2, 195)],
    ]
    for segment in segments:
        points.extend(cubic(segment, 32))
    draw.polygon([(round(x*SCALE), round(y*SCALE)) for x, y in points], fill=(79, 181, 210, 255))
    draw.ellipse(((cx-radius+1)*SCALE, 183*SCALE,
                  (cx-radius+8)*SCALE, 188*SCALE), fill=(241, 251, 249, 255))
    return canvas.resize((W, H), Image.Resampling.LANCZOS)


def render_eye(parts, dx=0, dy=0):
    result = parts['white'].copy()
    moved = parts['iris'].transform(parts['iris'].size, Image.Transform.AFFINE,
                                    (1, 0, -dx, 0, 1, -dy),
                                    resample=Image.Resampling.BICUBIC)
    moved.putalpha(ImageChops.multiply(moved.getchannel('A'), parts['aperture']))
    result.alpha_composite(moved)
    result.alpha_composite(parts['lower'])
    result.alpha_composite(parts['upper'])
    return result


layers = []
stats = {}
built = {}
for side, spec in SPECS.items():
    opening = cubic(spec['top']) + cubic(spec['bottom'])[1:]
    aperture = supersampled_polygon(opening)
    aperture_array = np.array(aperture)
    x0, y0, x1, y1 = spec['box']

    white = np.zeros_like(SOURCE)
    for y in range(y0, y1):
        grey = int(np.interp(y, [180, 187, 198, 213], [215, 240, 248, 242]))
        active = aperture_array[y] > 0
        white[y, active, :3] = [grey, min(grey+1, 255), min(grey+3, 255)]
    white[:, :, 3] = aperture_array

    bottom_mask = np.array(curve_strip(spec, 'lower'))
    luminance = SOURCE[:, :, :3].max(axis=2)
    crop = np.zeros((H, W), dtype=bool)
    crop[y0:y1, x0:x1] = True
    # Only painted linework belongs to fixed lids. Skin and old iris colour are
    # absent, preventing a second stationary iris from remaining.
    lower_alpha = np.where(crop & (bottom_mask > 0) & (luminance < 210), bottom_mask, 0).astype(np.uint8)
    # Rebuild the upper lash from a narrow semantic curve. Sampling the source
    # rectangle here also samples neighbouring dark hair and creates a large
    # downward triangle at the outer corner.
    upper_alpha = np.array(upper_lash_mask(spec))
    upper = np.zeros_like(SOURCE)
    upper[:, :, :3] = [18, 22, 34]
    upper[:, :, 3] = upper_alpha
    lower = SOURCE.copy(); lower[:, :, 3] = np.minimum(SOURCE[:, :, 3], lower_alpha)
    lower = recolor_chromatic_lid(lower)

    iris = build_iris(spec['center'][0], spec['radius'])
    neutral = iris.copy()
    neutral.putalpha(ImageChops.multiply(neutral.getchannel('A'), aperture))

    files = {
        f'eyewhite_{side}': Image.fromarray(white),
        f'iris_{side}': neutral,
        f'lower_lid_{side}': Image.fromarray(lower),
        f'upper_lid_{side}': Image.fromarray(upper),
    }
    for name, image in files.items():
        image.save(OUT / f'{name}.png')
        layers.append({'name': name, 'file': f'assets/eyes/{name}.png', 'visible': True})
    iris.save(OUT / f'iris_full_{side}.png')
    aperture.save(OUT / f'aperture_{side}.png')
    # Canvas destination-in reads transparency, not grayscale luminance. Keep
    # the L mask for CPU geometry, and export real alpha for the browser path.
    aperture_alpha = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    aperture_alpha.putalpha(aperture)
    aperture_alpha.save(OUT / f'aperture_alpha_{side}.png')

    stats[side] = {
        'box': spec['box'], 'center': spec['center'],
        'rangePixels': {'x': [-4, 4], 'y': [-2, 2]},
        'aperturePixels': int((aperture_array > 0).sum()),
        'painterOrder': [f'eyewhite_{side}', f'iris_{side}',
                         f'lower_lid_{side}', f'upper_lid_{side}'],
    }
    built[side] = {
        'white': files[f'eyewhite_{side}'], 'iris': iris,
        'lower': files[f'lower_lid_{side}'], 'upper': files[f'upper_lid_{side}'],
        'aperture': aperture,
    }

manifest = {
    'canvas': [W, H], 'layers': layers, 'eyes': stats,
    'runtime': {
        'iris': 'assets/eyes/iris_full_{side}.png',
        'aperture': 'assets/eyes/aperture_{side}.png',
        'apertureAlpha': 'assets/eyes/aperture_alpha_{side}.png',
        'clipping': 'translate complete iris, destination-in inset aperture, then composite fixed lids',
        'cameraTracking': False,
    },
}
(ROOT / 'eye_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

poses = [(-4, -2), (0, -2), (4, -2), (-4, 0), (0, 0), (4, 0),
         (-4, 2), (0, 2), (4, 2), (-1.5, .75), (2.25, -1.25)]
tile_w, tile_h = 300, 230
sheet = Image.new('RGB', (tile_w*len(poses), tile_h*2), '#b9c0c8')
draw = ImageDraw.Draw(sheet)
for row, side in enumerate(SPECS):
    for col, (dx, dy) in enumerate(poses):
        eye = render_eye(built[side], dx, dy)
        crop = eye.crop((SPECS[side]['box'][0]-4, SPECS[side]['box'][1]-4,
                         SPECS[side]['box'][2]+4, SPECS[side]['box'][3]+4))
        crop = crop.resize((tile_w, 200), Image.Resampling.NEAREST)
        sheet.paste(crop, (col*tile_w, row*tile_h), crop)
        draw.text((col*tile_w+5, row*tile_h+205), f'{side} X {dx:+g} Y {dy:+g}', fill='black')
sheet.save(ROOT / 'reports/eye_occlusion_extremes.png')
print(json.dumps({'layers': len(layers), 'eyes': stats}))
