"""Regression checks for the v5.1 ear opening and cheek-tip hair repair.

The tests deliberately avoid declaring a visual pass from edge metrics alone.
They lock provenance/scope and emit enlarged ROI evidence for human review.
"""
from pathlib import Path
import hashlib
import json
import unittest

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT.parent / 'live2d_v5'
EXPECTED = {'hair_front_fixed', 'hair_fringe_center'}
ROIS = {
    'screen_left_ear': (400, 168, 443, 238),
    'screen_left_cheek_tip': (420, 215, 477, 278),
    'screen_right_ear': (580, 168, 620, 238),
    'screen_right_cheek_tip': (550, 215, 598, 278),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(root, relative):
    return Image.open(root / relative).convert('RGBA')


class HairSeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT/'hair_fix_manifest.json').read_text())
        cls.current = {
            name: rgba(ROOT, f'assets/hair_refined/{name}.png') for name in EXPECTED
        }
        cls.baseline = {
            name: rgba(BASELINE, f'assets/hair_refined/{name}.png') for name in EXPECTED
        }

    def test_official_high_resolution_source_and_registered_hashes_are_locked(self):
        source = self.manifest['source']
        source_path = ROOT / source['file']
        self.assertTrue(source_path.is_file())
        self.assertEqual(digest(source_path), source['sha256'])
        self.assertIn('Official built-in image generation', source['method'])
        self.assertFalse(source['legacyEarHoleMaskApplied'])
        with Image.open(source_path) as image:
            self.assertGreater(image.width, 600)
            self.assertGreater(image.height, 600)

        self.assertEqual(set(self.manifest['layers']), EXPECTED)
        for name, entry in self.manifest['layers'].items():
            path = ROOT / entry['file']
            with self.subTest(layer=name):
                self.assertEqual(path, ROOT/f'assets/hair_refined/{name}.png')
                self.assertEqual(digest(path), entry['sha256'])
                with Image.open(path) as image:
                    self.assertEqual(image.size, tuple(self.manifest['canvas']))

    def test_rebuild_does_not_reapply_the_legacy_low_resolution_ear_mask(self):
        script = ROOT / self.manifest['source']['buildScript']
        text = script.read_text()
        self.assertNotIn('front_master_clean.png', text)
        self.assertNotIn('def ear(', text)
        self.assertNotIn('legacy ear', text.lower())
        self.assertNotIn('warm =', text)

    def test_both_ear_and_cheek_tip_regions_are_materially_repaired(self):
        current = np.array(self.current['hair_front_fixed'])
        baseline = np.array(self.baseline['hair_front_fixed'])
        counts = {}
        for name, (x0, y0, x1, y1) in ROIS.items():
            changed = np.any(current[y0:y1, x0:x1] != baseline[y0:y1, x0:x1], axis=2)
            counts[name] = int(changed.sum())
            with self.subTest(region=name):
                self.assertGreater(counts[name], 20)
        self.assertTrue(all(value > 20 for value in counts.values()))

    def test_repair_does_not_materially_cover_more_of_the_eyelids(self):
        for side in ('screen_left', 'screen_right'):
            upper = np.array(Image.open(ROOT/f'assets/eyes/upper_lid_{side}.png').convert('RGBA'))[:, :, 3] > 16
            lower = np.array(Image.open(ROOT/f'assets/eyes/lower_lid_{side}.png').convert('RGBA'))[:, :, 3] > 16
            eyelids = upper | lower
            for name in EXPECTED:
                current = np.array(self.current[name])[:, :, 3]
                baseline = np.array(self.baseline[name])[:, :, 3]
                current_overlap = int(((current > 16) & eyelids).sum())
                baseline_overlap = int(((baseline > 16) & eyelids).sum())
                with self.subTest(side=side, layer=name):
                    self.assertLessEqual(current_overlap, baseline_overlap + 10)

    def test_movable_center_fringe_does_not_capture_side_hair(self):
        alpha = np.array(self.current['hair_fringe_center'])[:, :, 3]
        box = Image.fromarray(alpha).getbbox()
        self.assertIsNotNone(box)
        x0, y0, x1, y1 = box
        self.assertGreaterEqual(x0, 460)
        self.assertLessEqual(x1, 545)
        self.assertLessEqual(x1-x0, 85)
        self.assertLessEqual(y1-y0, 135)
        self.assertLessEqual(y1, 220)
        for name, (rx0, ry0, rx1, ry1) in ROIS.items():
            with self.subTest(region=name):
                self.assertEqual(int((alpha[ry0:ry1, rx0:rx1] > 8).sum()), 0)

    @classmethod
    def tearDownClass(cls):
        reports = ROOT/'reports'; reports.mkdir(exist_ok=True)
        sheet = Image.new('RGB', (900, 1120), '#303a47')
        draw = ImageDraw.Draw(sheet)
        evidence = {}
        base_neutral = rgba(BASELINE, 'reports/neutral.png')
        current_neutral_path = ROOT/'reports/neutral.png'
        current_neutral = Image.open(current_neutral_path).convert('RGBA') if current_neutral_path.is_file() else None
        for i, (name, box) in enumerate(ROIS.items()):
            x = (i % 2) * 450; y = (i // 2) * 560
            draw.text((x+10, y+8), name, fill='white')
            old = base_neutral.crop(box).resize((400, 230), Image.Resampling.NEAREST)
            sheet.paste(old, (x+25, y+34), old)
            draw.text((x+25, y+269), 'v5 baseline  nearest 4x+', fill='#c7d1dc')
            if current_neutral is not None:
                new = current_neutral.crop(box).resize((400, 230), Image.Resampling.NEAREST)
                sheet.paste(new, (x+25, y+295), new)
                draw.text((x+25, y+530), 'v5.1 repair  nearest 4x+', fill='#c7d1dc')
            x0, y0, x1, y1 = box
            current = np.array(cls.current['hair_front_fixed'])[y0:y1, x0:x1]
            baseline = np.array(cls.baseline['hair_front_fixed'])[y0:y1, x0:x1]
            evidence[name] = {
                'box': list(box),
                'changedPixels': int(np.any(current != baseline, axis=2).sum()),
                'currentPartialAlphaPixels': int(((current[:, :, 3] > 0) & (current[:, :, 3] < 255)).sum()),
            }
        fringe_box = Image.fromarray(np.array(cls.current['hair_fringe_center'])[:, :, 3]).getbbox()
        sheet.save(reports/'hair_seam_rois.png')
        (reports/'hair_seam_test.json').write_text(json.dumps({
            'regions': evidence,
            'movableFringeBbox': list(fringe_box) if fringe_box else None,
            'visualReviewRequired': True,
            'note': 'Automated checks prove source/scope/eye safety; edge aesthetics require review of hair_seam_rois.png.',
        }, indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
