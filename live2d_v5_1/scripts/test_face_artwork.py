"""Provenance and structural checks for the second, generated face group.

The tests lock source identity, alpha integrity, semantic layer scope, and a
featureless face base.  Ear-root shape and final facial aesthetics remain
visual-review decisions rather than brittle colour or pixel-count assertions.
"""
from pathlib import Path
import hashlib
import json
import unittest

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'face_manifest.json'
EXPECTED = {
    'face', 'neck_bridge', 'ear_screen_left', 'ear_screen_right',
    'nose', 'mouth',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GeneratedFaceArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text())
        cls.canvas = tuple(cls.manifest['canvas'])
        cls.artwork = cls.manifest['artwork']
        cls.components = cls.artwork['components']

    def test_exactly_six_generated_semantic_sources_are_registered(self):
        self.assertEqual(set(self.components), EXPECTED)
        self.assertEqual(self.artwork['sourcePolicy'], 'generated-only')
        self.assertEqual(self.artwork['generationCalls'], 7)
        self.assertEqual(self.artwork['successfulOutputs'], 6)

        generated_sources = []
        registered_files = []
        for key in sorted(EXPECTED):
            entry = self.components[key]
            source = ROOT / entry['generatedSource']
            cleaned = ROOT / entry['cleanedSource']
            registered = ROOT / entry['registeredFile']
            with self.subTest(component=key):
                self.assertEqual(source.parent, ROOT / 'generation/face')
                self.assertEqual(registered, ROOT / f'assets/hair_refined/{key}.png')
                self.assertTrue(source.is_file())
                self.assertTrue(cleaned.is_file())
                self.assertTrue(registered.is_file())
                self.assertEqual(digest(source), entry['sourceSha256'])
                self.assertEqual(digest(registered), entry['sha256'])
                self.assertIsInstance(entry['transform'], dict)
                self.assertTrue(entry['transform'])
            generated_sources.append(entry['generatedSource'])
            registered_files.append(entry['registeredFile'])

        self.assertEqual(len(set(generated_sources)), 6)
        self.assertEqual(len(set(registered_files)), 6)

    def test_registered_pngs_have_real_alpha_and_truthful_bboxes(self):
        for key, entry in self.components.items():
            with Image.open(ROOT / entry['registeredFile']) as image:
                with self.subTest(component=key):
                    self.assertEqual(image.format, 'PNG')
                    self.assertIn('A', image.getbands())
                    alpha = np.array(image.getchannel('A'))
                    self.assertEqual(image.size, self.canvas)
                    self.assertEqual(int(alpha.min()), 0)
                    self.assertGreater(int(alpha.max()), 0)
                    self.assertEqual(list(image.getchannel('A').getbbox()), entry['bbox'])
                    self.assertEqual(int(alpha[0, 0]), 0)

    def test_face_base_is_a_single_filled_featureless_silhouette(self):
        entry = self.components['face']
        alpha = np.array(Image.open(ROOT / entry['registeredFile']).convert('RGBA'))[:, :, 3]
        x0, y0, x1, y1 = entry['bbox']
        mask = alpha[y0:y1, x0:x1] > 16
        labels, count = ndi.label(mask, structure=np.ones((3, 3)))
        sizes = np.bincount(labels.ravel())[1:]
        significant = sizes[sizes >= max(8, int(mask.sum() * .001))]
        holes = ndi.binary_fill_holes(mask) & ~mask

        self.assertEqual(len(significant), 1)
        self.assertLessEqual(int(holes.sum()), 8)
        self.assertGreater(x1 - x0, 140)
        self.assertGreater(y1 - y0, 150)
        self.assertGreater(float(mask.mean()), .55)

    def test_small_features_cannot_hide_large_opaque_skin_patches(self):
        limits = {'nose': (50, 50, 1600), 'mouth': (90, 55, 2600)}
        for key, (max_width, max_height, max_pixels) in limits.items():
            entry = self.components[key]
            image = Image.open(ROOT / entry['registeredFile']).convert('RGBA')
            alpha = np.array(image)[:, :, 3]
            x0, y0, x1, y1 = entry['bbox']
            with self.subTest(component=key):
                self.assertLessEqual(x1 - x0, max_width)
                self.assertLessEqual(y1 - y0, max_height)
                self.assertLessEqual(int((alpha > 16).sum()), max_pixels)
                self.assertEqual(int(alpha[0, 0]), 0)

    def test_ears_and_head_join_stay_in_head_scale_bounds(self):
        for key in ('ear_screen_left', 'ear_screen_right'):
            x0, y0, x1, y1 = self.components[key]['bbox']
            with self.subTest(component=key):
                self.assertGreaterEqual(x1 - x0, 12)
                self.assertLessEqual(x1 - x0, 70)
                self.assertGreaterEqual(y1 - y0, 30)
                self.assertLessEqual(y1 - y0, 100)

        x0, y0, x1, y1 = self.components['neck_bridge']['bbox']
        self.assertLessEqual(x1 - x0, 120)
        self.assertLessEqual(y1 - y0, 100)


if __name__ == '__main__':
    unittest.main()
