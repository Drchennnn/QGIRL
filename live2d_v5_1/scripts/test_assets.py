"""Delivery regressions for the v5.1 hair-seam fix and packed PSD."""
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
    def test_only_two_front_hair_layers_change_from_v5(self):
        changed_hair_group = {'hair_front_fixed', 'hair_fringe_center'}
        baseline_root = ROOT.parent / 'live2d_v5'
        current_layers = {
            layer['name']: layer
            for layer in json.loads((ROOT / 'manifest.json').read_text())['layers']
        }
        baseline_layers = {
            layer['name']: layer
            for layer in json.loads((baseline_root / 'manifest.json').read_text())['layers']
        }
        self.assertEqual(set(current_layers), set(baseline_layers))
        self.assertEqual(len(current_layers), 33)
        self.assertTrue(changed_hair_group <= set(current_layers))

        changed = set()
        checked = []
        for name in sorted(current_layers):
            current = ROOT / current_layers[name]['file']
            baseline = baseline_root / baseline_layers[name]['file']
            current_digest = hashlib.sha256(current.read_bytes()).hexdigest()
            baseline_digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
            with self.subTest(layer=name):
                self.assertTrue(current.is_file())
                self.assertTrue(baseline.is_file())
                if name in changed_hair_group:
                    self.assertNotEqual(current_digest, baseline_digest)
                    changed.add(name)
                else:
                    self.assertEqual(current_digest, baseline_digest)
                    checked.append(name)
        self.assertEqual(changed, changed_hair_group)
        self.assertEqual(len(checked), 31)

    def test_original_neck_join_has_no_new_transparent_holes(self):
        source = np.array(rgba('assets/front_master_clean.png'))
        current = np.array(rgba('reports/neutral.png'))
        y, x = np.indices(source.shape[:2])
        join = (y >= 262) & (y < 280) & (x >= 491) & (x < 531) & (source[:, :, 3] == 255)
        self.assertEqual(int((join & (current[:, :, 3] < 250)).sum()), 0)

    def test_browser_clip_alpha_matches_cpu_luminance(self):
        eye = json.loads((ROOT/'eye_manifest.json').read_text())
        for side in eye['eyes']:
            cpu = np.array(Image.open(ROOT / eye['runtime']['aperture'].format(side=side)).convert('L'))
            browser = np.array(rgba(eye['runtime']['apertureAlpha'].format(side=side)))[:, :, 3]
            with self.subTest(side=side):
                self.assertTrue(np.array_equal(cpu, browser))
                self.assertEqual(int(browser[0, 0]), 0)

    def test_foreground_hair_contains_no_skin_or_eye_fragments(self):
        for name in ('hair_front_fixed', 'hair_fringe_center'):
            image = np.array(rgba(f'assets/hair_refined/{name}.png')).astype(int)
            r, g, b, alpha = (image[:, :, i] for i in range(4))
            y, x = np.indices(r.shape)
            # Yellow/green clip is the only intentional warm-colour hair detail.
            clip = (x > 405) & (x < 448) & (y > 115) & (y < 178)
            skin = (alpha > 64) & ~clip & (r > 155) & (r > g+6) & (g > b+2)
            with self.subTest(name=name):
                self.assertEqual(int(skin.sum()), 0)
            for px, py in ((468, 193), (549, 193), (461, 165)):
                self.assertEqual(int(alpha[py, px]), 0)

    def test_no_stationary_fringe_below_root(self):
        fixed = np.array(rgba('assets/hair_refined/hair_front_fixed.png'))
        fringe = np.array(rgba('assets/hair_refined/hair_fringe_center.png'))
        y = np.indices(fixed.shape[:2])[0]
        overlap = (fixed[:, :, 3] > 0) & (fringe[:, :, 3] > 0) & (y >= 132)
        self.assertEqual(int(overlap.sum()), 0)

    def test_eyes_are_below_brows_and_all_front_hair(self):
        names = [l['name'] for l in json.loads((ROOT/'manifest.json').read_text())['layers']]
        self.assertFalse(any(n.startswith('eye_socket_') for n in names))
        self.assertLess(names.index('ear_screen_left'), names.index('face'))
        self.assertLess(names.index('ear_screen_right'), names.index('face'))
        for side in ('screen_left', 'screen_right'):
            self.assertLess(names.index('face'), names.index(f'eyewhite_{side}'))
            self.assertLess(names.index(f'iris_{side}'), names.index(f'upper_lid_{side}'))
            self.assertLess(names.index(f'upper_lid_{side}'), names.index(f'brow_{side}'))
            self.assertLess(names.index(f'upper_lid_{side}'), names.index('hair_front_fixed'))
            self.assertLess(names.index(f'upper_lid_{side}'), names.index('hair_fringe_center'))

    def test_psd_iris_uses_runtime_full_iris_and_mask(self):
        eye = json.loads((ROOT/'eye_manifest.json').read_text())
        for side in eye['eyes']:
            iris = rgba(eye['runtime']['iris'].format(side=side))
            mask = Image.open(ROOT / eye['runtime']['aperture'].format(side=side)).convert('L')
            iris.putalpha(ImageChops.multiply(iris.getchannel('A'), mask))
            with self.subTest(side=side):
                self.assertEqual(visible_difference(iris, rgba(f'assets/eyes/iris_{side}.png')), 0)

    def test_package_matches_runtime_neutral(self):
        self.assertEqual(visible_difference(rgba('reports/neutral.png'), rgba('packed/character_front_v5_composite.png')), 0)

    def test_package_inputs_are_current(self):
        report = json.loads((ROOT/'packed/character_front_v5_report.json').read_text())
        for layer in report['layers']:
            with self.subTest(layer=layer['name']):
                digest = hashlib.sha256(Path(layer['file']).read_bytes()).hexdigest()
                self.assertEqual(digest, layer['sha256'])
        digest = hashlib.sha256((ROOT/'packed/character_front_v5.psd').read_bytes()).hexdigest()
        self.assertEqual(digest, report['outputs']['psdSha256'])


if __name__ == '__main__':
    unittest.main()
