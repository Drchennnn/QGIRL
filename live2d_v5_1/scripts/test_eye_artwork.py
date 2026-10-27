"""Generated-art provenance and geometry checks for the first v4 eye group.

These checks deliberately avoid colour bans and connected-component counts:
blue highlights, shaded sclera, broken liner, and separate small lashes are all
valid design choices.  Source purity is instead an explicit manifest contract,
and accidental hair/face fragments are rejected by registered geometry.
"""
from pathlib import Path
import hashlib
import json
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'eye_manifest.json').read_text())
SIDES = ('screen_left', 'screen_right')
PARTS = ('upper_lid', 'lower_lid', 'eyewhite', 'iris_full', 'brow')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GeneratedEyeArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canvas = tuple(MANIFEST['canvas'])
        cls.artwork = MANIFEST['artwork']
        cls.components = cls.artwork['components']

    def test_exactly_ten_generated_only_semantic_sources_are_registered(self):
        expected = {f'{part}_{side}' for side in SIDES for part in PARTS}
        self.assertEqual(set(self.components), expected)
        self.assertEqual(self.artwork['sourcePolicy'], 'generated-only')

        generated_sources = []
        generated_hashes = []
        registered_files = []
        for key in sorted(expected):
            entry = self.components[key]
            source = ROOT / entry['generatedSource']
            registered = ROOT / entry['registeredFile']
            if key.startswith('brow_'):
                expected_registered = f'assets/hair_refined/{key}.png'
            elif key.startswith('eyewhite_'):
                expected_registered = f'assets/eyes/{key.replace("eyewhite_", "eyewhite_full_")}.png'
            else:
                expected_registered = f'assets/eyes/{key}.png'
            with self.subTest(component=key):
                self.assertEqual(entry['generatedSource'], f'generation/eyes/{key}.png')
                self.assertEqual(entry['registeredFile'], expected_registered)
                self.assertTrue(source.is_file())
                self.assertTrue(registered.is_file())
                self.assertEqual(digest(source), entry['sourceSha256'])
                self.assertEqual(digest(registered), entry['sha256'])
                self.assertIsInstance(entry['transform'], dict)
                self.assertTrue(entry['transform'])
            generated_sources.append(entry['generatedSource'])
            generated_hashes.append(entry['sourceSha256'])
            registered_files.append(entry['registeredFile'])

        self.assertEqual(len(set(generated_sources)), 10)
        self.assertEqual(len(set(generated_hashes)), 10)
        self.assertEqual(len(set(registered_files)), 10)

    def test_registered_pngs_have_real_alpha_and_truthful_bboxes(self):
        for key, entry in self.components.items():
            path = ROOT / entry['registeredFile']
            with Image.open(path) as image:
                with self.subTest(component=key):
                    self.assertEqual(image.format, 'PNG')
                    self.assertIn('A', image.getbands())
                    alpha = np.array(image.getchannel('A'))
                    actual_bbox = image.getchannel('A').getbbox()
                    self.assertEqual(image.size, self.canvas)
                    self.assertGreater(int(alpha.max()), 0)
                    self.assertEqual(int(alpha.min()), 0)
                    self.assertEqual(list(actual_bbox), entry['bbox'])

    def test_eye_parts_stay_local_to_their_declared_eye_boxes(self):
        for side in SIDES:
            x0, y0, x1, y1 = MANIFEST['eyes'][side]['box']
            for part in ('upper_lid', 'lower_lid', 'eyewhite'):
                key = f'{part}_{side}'
                bx0, by0, bx1, by1 = self.components[key]['bbox']
                with self.subTest(component=key):
                    self.assertGreater(bx1, x0)
                    self.assertLess(bx0, x1)
                    self.assertGreater(by1, y0)
                    self.assertLess(by0, y1)
                    self.assertGreaterEqual(bx0, x0 - 14)
                    self.assertLessEqual(bx1, x1 + 14)
                    self.assertGreaterEqual(by0, y0 - 14)
                    self.assertLessEqual(by1, y1 + 14)

    def test_full_irises_are_complete_and_not_aperture_crops(self):
        for side in SIDES:
            key = f'iris_full_{side}'
            path = ROOT / self.components[key]['registeredFile']
            with Image.open(path) as image:
                alpha = np.array(image.getchannel('A'))
            aperture = np.array(Image.open(
                ROOT / MANIFEST['runtime']['aperture'].format(side=side)).convert('L'))
            x0, y0, x1, y1 = self.components[key]['bbox']
            cx, cy = MANIFEST['eyes'][side]['center']
            width, height = x1 - x0, y1 - y0
            ys, xs = np.nonzero(alpha)
            with self.subTest(side=side):
                self.assertGreaterEqual(width, 14)
                self.assertGreaterEqual(height, 14)
                self.assertLessEqual(width, 64)
                self.assertLessEqual(height, 64)
                self.assertGreaterEqual(width / height, .55)
                self.assertLessEqual(width / height, 1.30)
                self.assertLessEqual(abs(float(xs.mean()) - cx), 6)
                self.assertLessEqual(abs(float(ys.mean()) - cy), 6)
                self.assertLess(int(xs.min()), cx - 5)
                self.assertGreater(int(xs.max()), cx + 5)
                self.assertLess(int(ys.min()), cy - 5)
                self.assertGreater(int(ys.max()), cy + 5)
                self.assertTrue(np.any(alpha[y0:y0 + max(2, height // 4), x0:x1]))
                self.assertTrue(np.any(alpha[y1 - max(2, height // 4):y1, x0:x1]))
                self.assertTrue(np.any(alpha[y0:y1, x0:x0 + max(2, width // 4)]))
                self.assertTrue(np.any(alpha[y0:y1, x1 - max(2, width // 4):x1]))
                self.assertGreater(int(((alpha > 0) & (aperture == 0)).sum()), 0)

    def test_brows_do_not_contain_large_hair_or_face_chunks(self):
        for side in SIDES:
            key = f'brow_{side}'
            path = ROOT / self.components[key]['registeredFile']
            with Image.open(path) as image:
                alpha = np.array(image.getchannel('A'))
            bx0, by0, bx1, by1 = self.components[key]['bbox']
            x0, y0, x1, _ = MANIFEST['eyes'][side]['box']
            with self.subTest(side=side):
                self.assertGreater(bx1, x0)
                self.assertLess(bx0, x1)
                self.assertGreaterEqual(bx0, x0 - 20)
                self.assertLessEqual(bx1, x1 + 20)
                self.assertGreaterEqual(by0, y0 - 35)
                self.assertLessEqual(by1, y0 + 20)
                self.assertLessEqual(bx1 - bx0, 85)
                self.assertLessEqual(by1 - by0, 35)
                self.assertLessEqual(int((alpha > 0).sum()), 2200)


if __name__ == '__main__':
    unittest.main()
