"""Delivery regressions: visible hair, runtime/PSD parity, current package inputs."""
from pathlib import Path
import hashlib
import json
import unittest

import numpy as np
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]


def rgba(path):
    return Image.open(ROOT / path).convert('RGBA')


def visible_difference(a, b):
    a, b = np.array(a), np.array(b)
    active = (a[:, :, 3] > 0) | (b[:, :, 3] > 0)
    return int((np.any(a != b, axis=2) & active).sum())


class DeliveryTests(unittest.TestCase):
    def test_movable_side_hair_has_no_forehead_skin_fragments(self):
        for side in ('screen_left', 'screen_right'):
            image = np.array(rgba(f'assets/hair_refined/hair_side_{side}.png')).astype(int)
            r, g, b, alpha = (image[:, :, i] for i in range(4))
            y = np.indices(r.shape)[0]
            skin = (alpha > 0) & (y >= 105) & (y < 190) & (r > 155) & (r > g+6) & (g > b+2)
            with self.subTest(side=side):
                self.assertEqual(int(skin.sum()), 0, 'Forehead skin was carried on a hair layer')

    def test_face_completion_does_not_cover_reviewed_side_hair(self):
        source = np.array(rgba('assets/front_master_clean.png'))
        current = np.array(rgba('reports/neutral.png'))
        y, x = np.indices(source.shape[:2])
        cheeks = (y >= 190) & (y < 235) & (((x >= 420) & (x < 447)) |
                                                          ((x >= 578) & (x < 602)))
        reviewed_hair = cheeks & (source[:, :, 3] == 255) & (source[:, :, :3].max(2) < 130)
        skin_over_hair = reviewed_hair & (current[:, :, :3].min(2) > 170)
        self.assertEqual(int(skin_over_hair.sum()), 0, 'Face backing painted over visible hair')

    def test_psd_iris_uses_the_runtime_soft_mask(self):
        for side in ('screen_left', 'screen_right'):
            with self.subTest(side=side):
                iris = rgba(f'assets/eyes/iris_{side}.png')
                mask = Image.open(ROOT / f'assets/eyes/aperture_{side}.png').convert('L')
                iris.putalpha(ImageChops.multiply(iris.getchannel('A'), mask))
                static = rgba(f'assets/eyes/iris_neutral_{side}.png')
                self.assertEqual(visible_difference(iris, static), 0)

    def test_package_matches_runtime_neutral(self):
        self.assertEqual(visible_difference(rgba('reports/neutral.png'),
                         rgba('packed/character_front_v2_composite.png')), 0)

    def test_package_inputs_are_current(self):
        report = json.loads((ROOT / 'packed/character_front_v2_report.json').read_text())
        for layer in report['layers']:
            with self.subTest(layer=layer['name']):
                digest = hashlib.sha256(Path(layer['file']).read_bytes()).hexdigest()
                self.assertEqual(digest, layer['sha256'], 'Rebuild PSD after changing assets')
        actual = hashlib.sha256((ROOT / 'packed/character_front_v2.psd').read_bytes()).hexdigest()
        self.assertEqual(actual, report['outputs']['psdSha256'])


if __name__ == '__main__':
    unittest.main()
