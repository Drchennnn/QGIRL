"""Extract reference views without repainting or resampling source pixels."""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'inputs/original_head_design.png'
VIEWS = {
    'front': (40, 80, 706, 850),
    'three_quarter': (708, 74, 1125, 535),
    'profile': (1128, 68, 1536, 551),
    'back': (730, 548, 1112, 947),
    'eye_detail': (1142, 606, 1518, 877),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = Image.open(SOURCE).convert('RGB')
    assert source.size == (1536, 1024), source.size
    records = {}
    for name, box in VIEWS.items():
        cropped = source.crop(box)
        path = ROOT / f'inputs/reference_{name}.png'
        cropped.save(path)
        readback = Image.open(path).convert('RGB')
        assert readback.tobytes() == source.crop(box).tobytes()
        records[name] = {
            'file': str(path.relative_to(ROOT)), 'sourceBox': list(box),
            'size': list(cropped.size), 'sha256': sha(path),
            'sourcePixelDifferences': 0, 'resampled': False,
        }
    # Preview only. The model input remains the exact original-resolution crop.
    sheet = Image.new('RGB', (1400, 850), '#d5d7db')
    draw = ImageDraw.Draw(sheet)
    placements = {'front': (20, 35), 'three_quarter': (710, 35),
                  'profile': (1095, 35), 'back': (710, 510),
                  'eye_detail': (1060, 570)}
    for name, (x, y) in placements.items():
        im = Image.open(ROOT / records[name]['file'])
        if name != 'front':
            im.thumbnail((290, 330))
        draw.text((x, y - 18), name.replace('_', ' '), fill='#22252e')
        sheet.paste(im, (x, y))
    sheet.save(ROOT / 'reports/reference_views.jpg', quality=95)
    report = {
        'source': 'inputs/original_head_design.png', 'sourceSha256': sha(SOURCE),
        'views': records, 'inferenceInput': records['front']['file'],
        'physicalViewAnglesCalibrated': False,
        'frontLandmarksSourcePixels': {
            'crown': [392, 113], 'chin': [391, 694],
            'iris_screen_left': [298, 514], 'iris_screen_right': [477, 507],
            'mouth_center': [389, 608],
        },
        'landmarkPrecision': 'manual reference anchors; not calibrated geometry',
        'features': ['screen-left lightning clip', 'two signature hair highlights',
                     'white inner dye', 'tapered brows and pointed outer lashes',
                     'cyan U-shaped irises', 'unequal angled fringe tips'],
        'note': 'Native front crop is 666x770; enlargement is not new detail.',
    }
    (ROOT / 'inputs/reference_registration.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    config_path = ROOT / 'experiment.json'
    config = json.loads(config_path.read_text())
    config['reference']['singleFrontInputPrepared'] = True
    config['reference']['frontInput'] = records['front']['file']
    config['reference']['registration'] = 'inputs/reference_registration.json'
    config['status'] = 'reference_prepared_decomposition_route_pending'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'views': len(records), 'frontSize': records['front']['size'],
                      'sourcePixelDifferences': 0}))


if __name__ == '__main__':
    main()
