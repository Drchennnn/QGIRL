"""Geometry regressions for the gaze layers.

These checks prove the fixed eyelid artwork wins over the moving iris at every
supported extreme. Merely observing zero alpha outside a clip mask is not
enough: the upper lash pixels themselves must stay invariant.
"""
from pathlib import Path
import json
import unittest

import numpy as np
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'eye_manifest.json').read_text())
POSES = ((-4, -2), (0, -2), (4, -2), (-4, 0), (0, 0), (4, 0),
         (-4, 2), (0, 2), (4, 2), (-1.5, .75), (2.25, -1.25))


def rgba(path):
    return Image.open(ROOT / path).convert('RGBA')


def render_eye(side, dx, dy):
    white = rgba(f'assets/eyes/eyewhite_{side}.png')
    iris = rgba(MANIFEST['runtime']['iris'].format(side=side))
    aperture = Image.open(ROOT / MANIFEST['runtime']['aperture'].format(side=side)).convert('L')
    moved = iris.transform(iris.size, Image.Transform.AFFINE,
                           (1, 0, -dx, 0, 1, -dy),
                           resample=Image.Resampling.BICUBIC)
    moved.putalpha(ImageChops.multiply(moved.getchannel('A'), aperture))
    result = white.copy()
    result.alpha_composite(moved)
    result.alpha_composite(rgba(f'assets/eyes/lower_lid_{side}.png'))
    result.alpha_composite(rgba(f'assets/eyes/upper_lid_{side}.png'))
    return result, moved


class EyeOcclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = MANIFEST

    def test_semantic_painter_order(self):
        names = [layer['name'] for layer in self.manifest['layers']]
        self.assertFalse(any(name.startswith('eye_socket_') for name in names))
        for side in self.manifest['eyes']:
            with self.subTest(side=side):
                self.assertLess(names.index(f'eyewhite_{side}'), names.index(f'iris_{side}'))
                self.assertLess(names.index(f'iris_{side}'), names.index(f'lower_lid_{side}'))
                self.assertLess(names.index(f'lower_lid_{side}'), names.index(f'upper_lid_{side}'))

    def test_declared_tracking_range_is_preserved(self):
        for side, eye in self.manifest['eyes'].items():
            with self.subTest(side=side):
                self.assertEqual(eye['rangePixels'], {'x': [-4, 4], 'y': [-2, 2]})
        self.assertEqual(self.manifest['runtime']['iris'], 'assets/eyes/iris_full_{side}.png')

    def test_iris_is_clipped_to_the_inset_eye_opening(self):
        for side in self.manifest['eyes']:
            aperture = np.array(Image.open(
                ROOT / self.manifest['runtime']['aperture'].format(side=side)).convert('L'))
            for dx, dy in POSES:
                with self.subTest(side=side, dx=dx, dy=dy):
                    _, moved = render_eye(side, dx, dy)
                    alpha = np.array(moved.getchannel('A'))
                    self.assertEqual(int(((alpha > 0) & (aperture == 0)).sum()), 0)

    def test_upper_lash_pixels_are_invariant_across_gaze(self):
        for side in self.manifest['eyes']:
            lid = np.array(rgba(f'assets/eyes/upper_lid_{side}.png'))
            # Only fully opaque liner must be bit-for-bit invariant. At
            # antialiased edges the composited RGB legitimately depends on
            # the moving layer underneath.
            covered = lid[:, :, 3] == 255
            self.assertGreater(int(covered.sum()), 10)
            neutral, _ = render_eye(side, 0, 0)
            expected = np.array(neutral)[covered]
            for dx, dy in POSES:
                with self.subTest(side=side, dx=dx, dy=dy):
                    posed, _ = render_eye(side, dx, dy)
                    self.assertTrue(np.array_equal(np.array(posed)[covered], expected))

    def test_static_eye_layers_do_not_enter_the_forehead(self):
        for layer in self.manifest['layers']:
            image = np.array(rgba(layer['file']))
            with self.subTest(layer=layer['name']):
                self.assertEqual(int((image[:171, :, 3] > 0).sum()), 0)


if __name__ == '__main__':
    unittest.main()
