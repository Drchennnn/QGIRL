"""Register six saved official generated face components; no generation at build time."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'generation/face'
SIZE = (1024, 1536)
# Original eye anchors and chin are retained. Each mother is scaled uniformly.
PLACEMENT = {
    'face': {'width': 187, 'centerX': 509.5, 'bottom': 270.5},
    'ear_screen_left': {'height': 46, 'x': 408.5, 'y': 179.5},
    'ear_screen_right': {'height': 47, 'x': 586.5, 'y': 179},
    'nose': {'height': 7, 'centerX': 509, 'y': 214},
    'mouth': {'width': 28, 'centerX': 510, 'y': 234.5},
    'neck_bridge': {'width': 78, 'centerX': 510, 'y': 245},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register(name, placement):
    raw = GEN / f'{name}.png'
    image = Image.open(raw).convert('RGBA')
    arr = np.array(image)
    labels, _ = ndi.label(arr[:, :, 3] > 8, structure=np.ones((3, 3)))
    counts = np.bincount(labels.ravel()); counts[0] = 0
    # The mouth intentionally has two separated strokes. All other art is one piece.
    ids = np.flatnonzero(counts >= max(32, counts.max() * .01)) if name == 'mouth' else [counts.argmax()]
    core = np.isin(labels, ids)
    support = ndi.binary_dilation(core, iterations=4)
    removed = int(((arr[:, :, 3] > 0) & ~support).sum())
    arr[~support] = 0
    if name in ('face', 'ear_screen_left', 'ear_screen_right', 'neck_bridge'):
        # Remove tiny generated root-edge burrs at mother size, retaining soft alpha.
        mask = ndi.binary_opening(arr[:, :, 3] > 127, iterations=3)
        mask = ndi.binary_closing(mask, iterations=2)
        arr[:, :, 3] = np.array(Image.fromarray(np.uint8(mask) * 255).filter(ImageFilter.GaussianBlur(.7)))
    image = Image.fromarray(arr)
    clean = GEN / f'{name}_clean.png'; image.save(clean)
    box = Image.fromarray(np.uint8(arr[:, :, 3] > 8) * 255).getbbox()
    scale = placement['width'] / (box[2] - box[0]) if 'width' in placement else placement['height'] / (box[3] - box[1])
    width, height = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
    left = placement.get('x', placement.get('centerX', 0) - width / 2)
    top = placement.get('y', placement.get('bottom', 0) - height)
    pad = 6
    crop_box = (max(0, box[0]-pad), max(0, box[1]-pad), min(image.width, box[2]+pad), min(image.height, box[3]+pad))
    crop = image.crop(crop_box)
    small_size = (max(1, round(crop.width*scale)), max(1, round(crop.height*scale)))
    small = crop.resize(small_size, Image.Resampling.LANCZOS)
    x = round(left - (box[0] - crop_box[0]) * scale)
    y = round(top - (box[1] - crop_box[1]) * scale)
    canvas = Image.new('RGBA', SIZE); canvas.alpha_composite(small, (x, y))
    seam = None
    if name == 'neck_bridge':
        # Derived overlap blend: hide the closed mother asset's bottom outline
        # inside the existing white neck. This changes alpha only, not RGB artwork.
        alpha = np.array(canvas.getchannel('A')).astype(float)
        fade = np.clip((303 - np.arange(SIZE[1])) / 9, 0, 1)
        canvas.putalpha(Image.fromarray(np.uint8(np.rint(alpha * fade[:, None]))))
        seam = {'method': 'vertical alpha overlap blend into inherited white neck', 'opaqueUntilY': 294, 'transparentFromY': 303}
    file = f'assets/hair_refined/{name}.png'; canvas.save(ROOT / file)
    return {
        'generatedSource': str(raw.relative_to(ROOT)), 'sourceSha256': sha(raw),
        'cleanedSource': str(clean.relative_to(ROOT)), 'registeredFile': file,
        'sha256': sha(ROOT/file), 'bbox': list(canvas.getbbox()),
        'sourceContentBox': list(box), 'sourceSize': list(image.size),
        'transform': {'method': 'uniform scale and translation', 'scale': scale, 'x': x, 'y': y, 'resizedCrop': list(small_size)},
        'cleanup': {'method': 'isolated specks; source-size 3px opening/2px closing for filled parts; no RGB repaint', 'removedSpeckPixels': removed},
        'overlapBlend': seam,
    }


components = {name: register(name, p) for name, p in PLACEMENT.items()}
log = json.loads((GEN/'generation_log.json').read_text())
manifest = {'canvas': list(SIZE), 'coordinateConvention': 'screen_left/right = viewer side',
    'artwork': {'sourcePolicy': 'generated-only', 'generationCalls': len(log['calls']), 'successfulOutputs': len(components), 'components': components},
    'stage': 'front face components; hidden-area artwork prepared; no angle keyforms or Cubism binding',
    'symmetryPolicy': 'For future symmetric structures generate one source, mirror and register; retain existing two generated ears in this group.'}
(ROOT/'face_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
# Ear attachments are beneath the face, not drawn over the cheek skin.
h = json.loads((ROOT/'hair_manifest.json').read_text())
by_name = {entry['name']: entry for entry in h['layers']}
order = ['hair_back', 'neck_bridge', 'ear_screen_left', 'ear_screen_right', 'face', 'brow_screen_left', 'brow_screen_right', 'nose', 'mouth', 'hair_front_fixed', 'hair_fringe_center']
h['layers'] = [by_name[name] for name in order]
h['eyeSlot']['after'] = 'face'
h['faceSource'] = 'face_manifest.json'
(ROOT/'hair_manifest.json').write_text(json.dumps(h, indent=2)+'\n')
print(json.dumps({name: value['bbox'] for name, value in components.items()}))
