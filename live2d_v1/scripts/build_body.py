"""Split the cleaned front master body into reproducible Live2D artwork layers.

The head/body handoff is explicit: body is every retained source pixel at
y >= 300 plus the central neck strip x=482..537, y=270..299. Screen-side names
refer to the viewer, never the character's anatomical side.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/front_master_clean.png"
OUT = ROOT / "assets/body"
REPORTS = ROOT / "reports"


def polygon(size: tuple[int, int], points: list[tuple[int, int]]) -> np.ndarray:
    mask = Image.new("1", size)
    ImageDraw.Draw(mask).polygon(points, fill=1)
    return np.asarray(mask, dtype=bool)


def save_layer(name: str, source: np.ndarray, mask: np.ndarray) -> str:
    layer = np.zeros_like(source)
    layer[mask] = source[mask]
    filename = f"{name}.png"
    Image.fromarray(layer).save(OUT / filename)
    return f"assets/body/{filename}"


def composite(files: list[str], size: tuple[int, int]) -> Image.Image:
    result = Image.new("RGBA", size)
    for filename in files:
        result.alpha_composite(Image.open(ROOT / filename).convert("RGBA"))
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    source_image = Image.open(SOURCE).convert("RGBA")
    source = np.asarray(source_image)
    h, w = source.shape[:2]
    yy, xx = np.indices((h, w))
    subject = source[:, :, 3] > 0

    # Shared contract with the head builder.  The interval is half-open in code:
    # neck x=482..537 means 482 <= x < 538.
    neck = subject & (yy >= 270) & (yy < 330) & (xx >= 482) & (xx < 538)
    body = subject & ((yy >= 300) | ((yy >= 270) & (xx >= 482) & (xx < 538)))

    left_arm_region = polygon((w, h), [
        (365, 315), (455, 315), (453, 445), (420, 570), (370, 690),
        (325, 785), (300, 880), (235, 900), (245, 735), (300, 590),
    ])
    right_arm_region = polygon((w, h), [
        (569, 315), (659, 315), (724, 590), (779, 735), (789, 900),
        (724, 880), (699, 785), (654, 690), (604, 570), (571, 445),
    ])
    left_leg_region = polygon((w, h), [
        (360, 720), (512, 720), (512, 1536), (330, 1536), (385, 1120),
    ])
    right_leg_region = polygon((w, h), [
        (512, 720), (664, 720), (639, 1120), (694, 1536), (512, 1536),
    ])

    masks: dict[str, np.ndarray] = {}
    remaining = body.copy()
    masks["neck"] = neck
    remaining &= ~neck

    # Distal-to-proximal semantic partitioning. Intersecting with the source
    # subject silhouette prevents rectangular cutouts at any outside edge.
    candidates = {
        "screen_left_hand": left_arm_region & (yy >= 735),
        "screen_right_hand": right_arm_region & (yy >= 735),
        "screen_left_forearm": left_arm_region & (yy >= 555),
        "screen_right_forearm": right_arm_region & (yy >= 555),
        "screen_left_upper_arm": left_arm_region,
        "screen_right_upper_arm": right_arm_region,
        "screen_left_foot": left_leg_region & (yy >= 1375),
        "screen_right_foot": right_leg_region & (yy >= 1375),
        "screen_left_lower_leg": left_leg_region & (yy >= 1030),
        "screen_right_lower_leg": right_leg_region & (yy >= 1030),
        "screen_left_thigh": left_leg_region & (yy >= 745),
        "screen_right_thigh": right_leg_region & (yy >= 745),
    }
    for name, candidate in candidates.items():
        masks[name] = remaining & candidate
        remaining &= ~masks[name]
    masks["torso_pelvis"] = remaining

    visible_union = np.zeros((h, w), dtype=bool)
    for mask in masks.values():
        if np.any(visible_union & mask):
            raise RuntimeError("visible semantic masks overlap")
        visible_union |= mask
    if not np.array_equal(visible_union, body):
        raise RuntimeError(f"body partition missed {np.count_nonzero(body ^ visible_union)} pixels")

    # Add copied, programmatic overlap under the later-painted parent. Restrict
    # to fully opaque interior pixels so the neutral composite remains exact.
    opaque = source[:, :, 3] == 255
    parent = {
        "screen_left_hand": "screen_left_forearm",
        "screen_right_hand": "screen_right_forearm",
        "screen_left_forearm": "screen_left_upper_arm",
        "screen_right_forearm": "screen_right_upper_arm",
        "screen_left_upper_arm": "torso_pelvis",
        "screen_right_upper_arm": "torso_pelvis",
        "screen_left_foot": "screen_left_lower_leg",
        "screen_right_foot": "screen_right_lower_leg",
        "screen_left_lower_leg": "screen_left_thigh",
        "screen_right_lower_leg": "screen_right_thigh",
        "screen_left_thigh": "torso_pelvis",
        "screen_right_thigh": "torso_pelvis",
        "neck": "torso_pelvis",
    }
    rendered = {name: mask.copy() for name, mask in masks.items()}
    overlap_counts: dict[str, int] = {}
    for child, parent_name in parent.items():
        width = 14 if "arm" in child or "forearm" in child else 12
        extension = ndi.binary_dilation(masks[child], iterations=width) & masks[parent_name] & opaque
        rendered[child] |= extension
        overlap_counts[child] = int(np.count_nonzero(extension))

    order = [
        "neck",
        "screen_left_hand", "screen_right_hand",
        "screen_left_forearm", "screen_right_forearm",
        "screen_left_upper_arm", "screen_right_upper_arm",
        "screen_left_foot", "screen_right_foot",
        "screen_left_lower_leg", "screen_right_lower_leg",
        "screen_left_thigh", "screen_right_thigh",
        "torso_pelvis",
    ]
    files = {name: save_layer(name, source, rendered[name]) for name in order}
    rebuilt = composite([files[name] for name in order], (w, h))
    expected = np.zeros_like(source)
    expected[body] = source[body]
    actual = np.asarray(rebuilt)
    changed = int(np.count_nonzero(np.any(expected != actual, axis=2)))
    max_difference = int(np.max(np.abs(expected.astype(int) - actual.astype(int))))
    if changed:
        raise RuntimeError(f"neutral body composite changed {changed} pixels")

    manifest = {
        "schemaVersion": 1,
        "canvas": [w, h],
        "coordinateConvention": "screen_left/screen_right are viewer sides",
        "headBodyBoundary": {
            "bodyMask": "source alpha > 0 AND (y >= 300 OR (270 <= y < 300 AND 482 <= x < 538))",
            "headExclusion": "head builder must exclude exactly the bodyMask above",
            "pixelCoordinates": "zero-based; x/y intervals are half-open",
        },
        "painterOrder": "bottom-to-top",
        "layers": [{"name": name, "file": files[name], "visible": True} for name in order],
        "overlapPolicy": "Child layers copy fully opaque source pixels up to 12-14 px into the later-painted parent; these are programmatic concealed fills, not artist-reviewed new artwork.",
    }
    (ROOT / "body_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    rebuilt.save(REPORTS / "body_composite.png")
    gray = Image.new("RGBA", (w, h), (210, 210, 210, 255))
    gray.alpha_composite(rebuilt)
    gray.convert("RGB").save(REPORTS / "body_composite_gray.png")
    palette = [(245,80,80),(80,210,245),(255,180,65),(150,100,245),(70,210,120),(245,100,190)]
    diagnostic = np.zeros_like(source)
    for index, name in enumerate(order):
        color = palette[index % len(palette)]
        diagnostic[masks[name], :3] = color
        diagnostic[masks[name], 3] = 220
    Image.fromarray(diagnostic).save(REPORTS / "body_masks.png")
    crops = [(235,300,460,900),(564,300,789,900),(330,700,694,930),(330,980,694,1536)]
    montage = Image.new("RGBA", (800, 600), (220,220,220,255))
    for i, box in enumerate(crops):
        crop = Image.fromarray(diagnostic).crop(box)
        crop.thumbnail((390,290), Image.Resampling.LANCZOS)
        montage.alpha_composite(crop, ((i%2)*400, (i//2)*300))
    montage.convert("RGB").save(REPORTS / "body_joints.png")

    report = {
        "source": str(SOURCE), "canvas": [w, h],
        "bodyVisiblePixels": int(np.count_nonzero(body)),
        "semanticVisiblePixels": {name: int(np.count_nonzero(masks[name])) for name in order},
        "programmaticConcealedOverlapPixels": overlap_counts,
        "validation": {
            "visiblePartitionMissedPixels": int(np.count_nonzero(body ^ visible_union)),
            "neutralCompositeChangedPixels": changed,
            "neutralCompositeMaxChannelDifference": max_difference,
            "allLayersFullCanvasRGBA": True,
        },
        "limitations": [
            "Overlap is copied from currently visible source pixels; it supports small joint rotations only.",
            "No AI inpainting, anatomical repainting, mesh, deformers, or Cubism binding is included.",
        ],
    }
    (REPORTS / "body_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["validation"], indent=2))
    print(json.dumps(overlap_counts, indent=2))


if __name__ == "__main__":
    main()
