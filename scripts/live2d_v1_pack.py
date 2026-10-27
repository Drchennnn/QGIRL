"""Pack full-canvas RGBA artwork into a verified layered PSD.

The manifest order is painter order: the first layer is at the bottom and the
last layer is at the top. Run with the project's isolated dependency pattern:

    uv run --with psd-tools --with pillow --with numpy \
      python scripts/live2d_v1_pack.py path/to/manifest.json

This packages artwork only. It does not infer semantic parts, paint concealed
regions, generate meshes, or produce a Live2D model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from psd_tools import PSDImage


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_error(expected: Image.Image, actual: Image.Image) -> int:
    a = np.asarray(expected.convert("RGBA"))
    b = np.asarray(actual.convert("RGBA"))
    active = (a[:, :, 3] > 0) | (b[:, :, 3] > 0)
    return int(np.count_nonzero(np.any(a != b, axis=2) & active))


def load_manifest(path: Path) -> tuple[tuple[int, int], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    canvas = data.get("canvas")
    if (not isinstance(canvas, list) or len(canvas) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0
                   for value in canvas)):
        raise ValueError("manifest canvas must be [positive_integer_width, positive_integer_height]")
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValueError("manifest layers must be a non-empty list")
    names: set[str] = set()
    checked: list[dict[str, Any]] = []
    for index, item in enumerate(layers):
        if not isinstance(item, dict):
            raise ValueError(f"layer {index} must be an object")
        name, filename = item.get("name"), item.get("file")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"layer {index} requires a non-empty name")
        if name in names:
            raise ValueError(f"duplicate layer name: {name}")
        names.add(name)
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"layer {name!r} requires a file")
        visible = item.get("visible", True)
        if not isinstance(visible, bool):
            raise ValueError(f"layer {name!r} visible must be boolean")
        checked.append({"name": name, "file": filename, "visible": visible})
    return (canvas[0], canvas[1]), checked


def resolve_layer_path(manifest: Path, filename: str) -> Path:
    path = (manifest.parent / filename).resolve()
    root = manifest.parent.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"layer file escapes manifest directory: {filename}")
    if not path.is_file():
        raise FileNotFoundError(f"missing layer file: {path}")
    return path


def composite(layers: list[dict[str, Any]], size: tuple[int, int]) -> Image.Image:
    result = Image.new("RGBA", size)
    for entry in layers:
        if entry["visible"]:
            result.alpha_composite(entry["image"])
    return result


def decode_visible_layers(psd: PSDImage, size: tuple[int, int]) -> Image.Image:
    decoded = Image.new("RGBA", size)
    for layer in psd:
        if layer.visible:
            decoded.alpha_composite(layer.topil().convert("RGBA"), (layer.left, layer.top))
    return decoded


def pack(manifest_path: Path, output_dir: Path, stem: str) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    size, layer_specs = load_manifest(manifest_path)
    entries: list[dict[str, Any]] = []
    for spec in layer_specs:
        path = resolve_layer_path(manifest_path, spec["file"])
        with Image.open(path) as source:
            if source.format != "PNG":
                raise ValueError(f"layer {spec['name']!r} is not a PNG: {path}")
            if source.mode != "RGBA":
                raise ValueError(f"layer {spec['name']!r} must be RGBA, got {source.mode}")
            if source.size != size:
                raise ValueError(
                    f"layer {spec['name']!r} must match canvas {size}, got {source.size}"
                )
            image = source.copy()
        bounds = image.getbbox()
        if bounds is None:
            raise ValueError(f"layer {spec['name']!r} has no non-transparent pixels")
        alpha = np.asarray(image.getchannel("A"))
        entries.append({
            **spec,
            "path": path,
            "image": image,
            "bounds": bounds,
            "nonemptyAlphaPixels": int(np.count_nonzero(alpha)),
            "sha256": sha256(path),
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    psd_path = output_dir / f"{stem}.psd"
    composite_path = output_dir / f"{stem}_composite.png"
    report_path = output_dir / f"{stem}_report.json"

    psd = PSDImage.new("RGBA", size, depth=8)
    for entry in entries:
        x0, y0, x1, y1 = entry["bounds"]
        layer = psd.create_pixel_layer(
            entry["image"].crop((x0, y0, x1, y1)),
            name=entry["name"],
            top=y0,
            left=x0,
        )
        layer.visible = entry["visible"]
    psd.save(psd_path)

    expected = composite(entries, size)
    expected.save(composite_path)
    reread = PSDImage.open(psd_path)
    decoded = decode_visible_layers(reread, size)
    pixel_changes = visible_error(expected, decoded)
    expected_names = [entry["name"] for entry in entries]
    decoded_names = [layer.name for layer in reread]
    expected_visibility = [entry["visible"] for entry in entries]
    decoded_visibility = [layer.visible for layer in reread]
    if decoded_names != expected_names:
        raise ValueError(f"PSD layer order/name mismatch: {decoded_names!r}")
    if decoded_visibility != expected_visibility:
        raise ValueError("PSD layer visibility changed during roundtrip")
    if reread.size != size:
        raise ValueError(f"PSD canvas changed during roundtrip: {reread.size}")
    if pixel_changes:
        raise ValueError(f"PSD channel roundtrip changed {pixel_changes} visible pixels")

    report: dict[str, Any] = {
        "schemaVersion": 1,
        "manifest": str(manifest_path),
        "canvas": list(size),
        "mode": "RGBA source / RGB PSD with transparency channels",
        "depth": 8,
        "painterOrder": "bottom-to-top",
        "outputs": {
            "psd": str(psd_path.resolve()),
            "composite": str(composite_path.resolve()),
            "psdSha256": sha256(psd_path),
            "compositeSha256": sha256(composite_path),
        },
        "layers": [
            {
                "index": index,
                "name": entry["name"],
                "file": str(entry["path"]),
                "visible": entry["visible"],
                "bounds": list(entry["bounds"]),
                "dimensions": list(entry["image"].size),
                "nonemptyAlphaPixels": entry["nonemptyAlphaPixels"],
                "sha256": entry["sha256"],
            }
            for index, entry in enumerate(entries)
        ],
        "validation": {
            "psdReadbackAvailable": True,
            "psdCanvas": list(reread.size),
            "layerCount": len(entries),
            "visibleLayerCount": sum(expected_visibility),
            "hiddenLayerCount": len(entries) - sum(expected_visibility),
            "decodedChannelPixelChanges": pixel_changes,
            "layerNamesAndOrderMatch": True,
            "layerVisibilityMatches": True,
        },
        "limitations": [
            "Inputs must already be semantically separated full-canvas RGBA PNGs.",
            "The packer crops only the PSD storage rectangles; report dimensions preserve the full input canvas.",
            "No concealed artwork, masks, eye states, mesh, parameters, physics, or Live2D binding are generated.",
            "PSD readback proves pixel-layer packaging, not Cubism Editor or runtime compatibility.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON manifest; layer files are relative to it")
    parser.add_argument("--output-dir", type=Path, help="default: <manifest-dir>/packed")
    parser.add_argument("--stem", default="live2d_front_master", help="output filename stem")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir or args.manifest.parent / "packed"
    report = pack(args.manifest, output_dir, args.stem)
    print(json.dumps(report["validation"], indent=2))


if __name__ == "__main__":
    main()
