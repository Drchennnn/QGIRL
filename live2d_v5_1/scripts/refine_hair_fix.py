"""Register the official ear/cheek hair repair, without any old ear-hole mask."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SIZE = (1024, 1536)
source_path = ROOT/'generation/hair_fix/hair_ear_cheek_repair.png'
image = Image.open(source_path).convert('RGBA')
pixels = np.array(image)
labels, _ = ndi.label(pixels[:, :, 3] > 8)
counts = np.bincount(labels.ravel()); counts[0] = 0
support = ndi.binary_dilation(labels == counts.argmax(), iterations=3)
pixels[~support] = 0
# Make the near-opaque generated interiors opaque; retain soft edge alpha.
pixels[:, :, 3][pixels[:, :, 3] >= 250] = 255
Image.fromarray(pixels).save(ROOT/'generation/hair_fix/hair_clean.png')
registered = Image.new('RGBA', SIZE)
registered.alpha_composite(Image.fromarray(pixels).resize((290, 300), Image.Resampling.LANCZOS), (365, 15))
hair = np.array(registered)
y, x = np.indices(hair.shape[:2])

# The center fringe remains its own movable layer, with an overlap at the pinned
# root only. The generated transparent gaps define the lower strand boundary.
semantic_path = ROOT.parent/'live2d_v5/assets/hair_refined/hair_fringe_center.png'
semantic = np.array(Image.open(semantic_path).getchannel('A')) > 8
# Generation may connect the fringe to a side lock at the forehead. Constrain
# component selection to the approved center-fringe region, never to ear shapes.
allowed = ndi.binary_dilation(semantic, iterations=2) & (x >= 468) & (x <= 537) & (y < 194)
labels, _ = ndi.label((hair[:, :, 3] > 8) & (y >= 132) & allowed)
seed = labels[145, 500]
assert seed != 0, 'Missing center fringe seed'
center = ndi.binary_dilation(labels == seed, iterations=2) & (y >= 132) & allowed
root = (y >= 82) & (y < 132) & (x >= 471) & (x <= 525)
selected = center | root
fringe = np.zeros_like(hair); fringe[selected] = hair[selected]
fixed = hair.copy(); fixed[selected] = 0
overlap = (y >= 82) & (y < 126) & selected
fixed[overlap] = hair[overlap]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

outputs = {}
for name, part in [('hair_front_fixed', fixed), ('hair_fringe_center', fringe)]:
    file = f'assets/hair_refined/{name}.png'
    im = Image.fromarray(part); im.save(ROOT/file)
    outputs[name] = {'file': file, 'sha256': sha(ROOT/file), 'bbox': list(im.getbbox())}

manifest = {'canvas': list(SIZE), 'source': {
    'file': str(source_path.relative_to(ROOT)), 'sha256': sha(source_path),
    'method': 'Official built-in image generation; ear openings and cheek tips repaired in full-resolution alpha artwork',
    'model': 'not exposed by built-in tool', 'legacyEarHoleMaskApplied': False,
    'buildScript': 'scripts/refine_hair_fix.py',
    'registration': {'fullSourceSize': list(image.size), 'targetSize': [290, 300], 'position': [365, 15]},
}, 'layers': outputs, 'fringeSemanticSelection': {
    'file': str(semantic_path.relative_to(ROOT.parent)), 'sha256': sha(semantic_path),
    'method': 'approved v5 center fringe support only; no source RGB reused; never used as ear opening'},
    'scope': 'Two front hair layers only; all other 31 layers byte-identical to v5',
    'generationLog': 'generation/hair_fix/generation_log.json'}
(ROOT/'hair_fix_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
h = json.loads((ROOT/'hair_manifest.json').read_text())
h['source'] = manifest['source']
h['repairSource'] = 'hair_fix_manifest.json'
(ROOT/'hair_manifest.json').write_text(json.dumps(h, indent=2)+'\n')
registered.save(ROOT/'generation/hair_fix/hair_registered.png')
print(json.dumps({'layers': list(outputs), 'legacyEarHoleMaskApplied': False}))
