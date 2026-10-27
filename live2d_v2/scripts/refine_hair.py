from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "live2d_v1"
V2 = ROOT / "live2d_v2"
OUT = V2 / "assets/hair_refined"
REPORTS = V2 / "reports"
OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

SOURCE = np.array(Image.open(V2 / "assets/front_master_clean.png").convert("RGBA"))
H, W = SOURCE.shape[:2]
Y, X = np.indices((H, W))
manifest = json.loads((V1 / "head_manifest.json").read_text())
old = {entry["name"]: np.array(Image.open(V1 / entry["file"]).convert("RGBA"))
       for entry in manifest["layers"]}

HAIR = ["hair_back", "hair_crown", "hair_side_screen_left",
        "hair_side_screen_right", "hair_fringe_center"]
STREAKS = ["hair_streak_screen_left", "hair_streak_screen_right"]
EYES = {"eyewhite_screen_left", "eyewhite_screen_right", "iris_screen_left",
        "iris_screen_right", "upper_lid_screen_left", "upper_lid_screen_right",
        "lower_lid_screen_left", "lower_lid_screen_right"}

def region(x0, y0, x1, y1):
    return (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)

def nearest_fill(rgb, visible, target):
    indices = ndi.distance_transform_edt(~visible, return_distances=False, return_indices=True)
    return rgb[indices[0][target], indices[1][target]]

# Use the original ownership as a conservative spatial prior, then remove source
# pixels that are demonstrably skin or belong to eye apertures. This prevents a
# moving fringe from revealing a second, fixed copy of its antialiased edge.
skin_rgb = np.array([252.0, 228.0, 218.0])
src_rgb = SOURCE[:, :, :3].astype(float)
skin_distance = np.linalg.norm(src_rgb - skin_rgb, axis=2)
skin_like = skin_distance < 47
eye_zone = region(428, 168, 591, 215)
forehead_zone = region(430, 105, 590, 190)

refined = {name: image.copy() for name, image in old.items() if name not in EYES}
side_skin_transfer = np.zeros((H, W), dtype=bool)
for name in HAIR:
    if name in ("hair_side_screen_left", "hair_side_screen_right"):
        # Return warm skin and its shadow to the fixed face. Restricting this to
        # almost-flat skin leaves jagged skin fragments in the fringe corridor.
        image = old[name].copy()
        exact_source = np.all(image == SOURCE, axis=2)
        rgb = image[:, :, :3].astype(int)
        warm_skin = (rgb[:, :, 0] > 155) & (rgb[:, :, 0] > rgb[:, :, 1] + 6) & (rgb[:, :, 1] > rgb[:, :, 2] + 2)
        visible_skin = (image[:, :, 3] > 0) & exact_source & warm_skin
        side_skin_transfer |= visible_skin
        image[warm_skin | ((image[:, :, 3] > 0) & exact_source & (skin_distance < 12))] = 0
        refined[name] = image
        continue
    image = refined[name]
    owned = image[:, :, 3] > 0
    remove = owned & (skin_distance < 12)
    if name == "hair_crown":
        # Retain the reviewed crown silhouette. Only exact skin contamination is
        # removed here; concealed overlap is cleared after the fringe is known.
        pass
    elif name == "hair_fringe_center":
        remove |= owned & eye_zone & (skin_distance < 12)
    else:
        remove |= owned & eye_zone & (skin_distance < 12)
    image[remove] = 0

    # Rebuild mixed hair/skin edge pixels as transparent hair over the completed
    # face backing. Use the nearest unquestionably dark source pixel as the local
    # foreground colour and solve C = alpha*F + (1-alpha)*skin.
    candidate = owned & ~remove
    solid = candidate & (np.max(src_rgb, axis=2) < 145)
    mixed = candidate & ~solid & (skin_distance < 95)
    if solid.any() and mixed.any():
        fg = nearest_fill(src_rgb, solid, mixed)
        c = src_rgb[mixed]
        denom = np.sum((fg - skin_rgb) ** 2, axis=1)
        alpha = np.divide(np.sum((c - skin_rgb) * (fg - skin_rgb), axis=1), denom,
                          out=np.zeros_like(denom), where=denom > 1e-6)
        alpha = np.clip(alpha, 0, 1)
        ys, xs = np.nonzero(mixed)
        image[ys, xs, :3] = np.clip(np.rint(fg), 0, 255).astype(np.uint8)
        image[ys, xs, 3] = np.clip(np.rint(alpha * 255), 0, 255).astype(np.uint8)
    refined[name] = image

# Clear only the fixed crown copy concealed by the original fringe. This keeps
# the neutral crown silhouette intact while avoiding a duplicate after motion.
crown = refined["hair_crown"]
fringe = refined["hair_fringe_center"]
fringe_corridor = ndi.binary_erosion(fringe[:, :, 3] > 0, iterations=1) & forehead_zone & (Y >= 95)
crown[fringe_corridor] = 0
refined["hair_crown"] = crown
refined["hair_fringe_center"] = fringe

# A continuous face backing is required under all movable bangs. Preserve the
# reviewed jaw/ear edge pixels, but replace concealed forehead/eye backing with
# a clean flat skin fill. Eye artwork will be inserted above this layer.
face = np.zeros_like(refined["face"])
mask_img = Image.new("1", (W, H))
ImageDraw.Draw(mask_img).ellipse((424, 82, 594, 274), fill=1)
# Constrain completion to the original semantic face ownership. Dilate it only
# upward beneath the bangs; never grow below the reviewed jaw silhouette.
old_face_mask = old["face"][:, :, 3] > 0
upper_completion = ndi.binary_dilation(old_face_mask, iterations=18) & (Y < 175)
# Completion is needed beneath the forehead fringe. Growing it alongside the
# cheeks covers the ear layers below the face, erasing their visible dark hair.
face_fill = np.array(mask_img, dtype=bool) & (old_face_mask | upper_completion)
face[face_fill, :3] = skin_rgb.astype(np.uint8)
face[face_fill, 3] = 255
# Restore the reviewed jaw outline and lower-face antialiasing. Brows, eyes,
# nose, and mouth remain independent foreground layers.
# Restore every original face-owned pixel so the visible jaw/cheeks are exact.
# The synthetic flat fill remains only in previously concealed additions.
face[old_face_mask] = old["face"][old_face_mask]
face[side_skin_transfer] = SOURCE[side_skin_transfer]
refined["face"] = face

# Keep only the long, thin eyebrow component. The v1 masks also captured small
# triangular hair fragments below the real brow, visible after eye refinement.
for name in ("brow_screen_left", "brow_screen_right"):
    brow = refined[name]
    mask = brow[:, :, 3] > 0
    components, count = ndi.label(mask)
    candidates = []
    for label in range(1, count + 1):
        ys, xs = np.nonzero(components == label)
        if not len(xs):
            continue
        width = int(xs.max() - xs.min() + 1)
        height = int(ys.max() - ys.min() + 1)
        candidates.append((width / max(height, 1), len(xs), label))
    keep_label = max(candidates)[2]
    brow[components != keep_label] = 0
    refined[name] = brow

order = [entry["name"] for entry in manifest["layers"] if entry["name"] not in EYES]
layers = []
for name in order:
    path = OUT / f"{name}.png"
    Image.fromarray(refined[name]).save(path)
    layers.append({"name": name, "file": f"assets/hair_refined/{name}.png", "visible": True})

# Eye layers are inserted after brow_screen_right and before nose. This explicit
# contract lets the parent preserve its independently refined eye assets.
eye_slot_after = "brow_screen_right"
report = {
    "canvas": [W, H],
    "layers": layers,
    "eyeSlot": {
        "after": eye_slot_after,
        "before": "nose",
        "expectedOrder": ["eyewhite_screen_left", "eyewhite_screen_right",
                          "iris_screen_left", "iris_screen_right",
                          "upper_lid_screen_left", "upper_lid_screen_right",
                          "lower_lid_screen_left", "lower_lid_screen_right"],
    },
    "method": "Remove skin/eye contamination; reconstruct mixed dark-hair edges as alpha over flat face backing.",
}
(V2 / "hair_manifest.json").write_text(json.dumps(report, indent=2) + "\n")

def image_for(name):
    if name in EYES:
        return Image.fromarray(old[name])
    return Image.fromarray(refined[name])

def deform_fringe(image, amount):
    arr = np.array(image)
    moved = np.zeros_like(arr)
    # Hair root remains fixed through y=95. Movement eases in and reaches the
    # requested amount from y=150 downward, avoiding an artificial root seam.
    t = np.clip((Y - 95) / 55, 0, 1)
    t = t * t * (3 - 2 * t)
    dx = np.rint(amount * t).astype(int)
    source_x = np.clip(X - dx, 0, W - 1)
    moved = arr[Y, source_x]
    moved[(X - dx < 0) | (X - dx >= W)] = 0
    return Image.fromarray(moved)

def render(fringe_amount=0):
    result = Image.new("RGBA", (W, H))
    for entry in manifest["layers"]:
        image = image_for(entry["name"])
        if entry["name"] == "hair_fringe_center" and fringe_amount:
            image = deform_fringe(image, fringe_amount)
        result.alpha_composite(image)
    return result

neutral = render()
reference = SOURCE.copy()
body_mask = (Y >= 300) | ((Y >= 270) & (X >= 482) & (X < 538))
reference[body_mask] = 0
neutral_arr = np.array(neutral)
active_neutral = (neutral_arr[:, :, 3] > 0) | (reference[:, :, 3] > 0)
neutral_changes = int((np.any(neutral_arr != reference, axis=2) & active_neutral).sum())
neutral_max_difference = int(np.abs(neutral_arr.astype(int) - reference.astype(int)).max())
fixed_hair = np.zeros((H, W), dtype=bool)
for fixed_name in ("hair_back", "hair_crown", "hair_side_screen_left",
                   "hair_side_screen_right", *STREAKS):
    fixed_hair |= refined[fixed_name][:, :, 3] > 0
fringe_sweep = ndi.binary_dilation(refined["hair_fringe_center"][:, :, 3] > 0, iterations=4)
fixed_dark_ghosts = int((fixed_hair & fringe_sweep & forehead_zone &
                         (np.max(SOURCE[:, :, :3], axis=2) < 150)).sum())

samples = Image.new("RGB", (900, 330), "#b4bac0")
sample_checks = []
for index, amount in enumerate((-3, 0, 3)):
    pose = render(amount)
    crop = pose.crop((365, 15, 655, 315))
    samples.paste(crop, (index * 300, 0), crop)
    arr = np.array(pose)
    # A completed face backing should leave no transparent holes throughout the
    # central forehead/eye neighbourhood when the fringe deforms.
    inspect = region(445, 105, 575, 216)
    holes = int((inspect & (arr[:, :, 3] < 250)).sum())
    sample_checks.append({"fringeX": amount, "transparentPixelsInInspectionRegion": holes})
samples.save(REPORTS / "hair_motion_samples.png")
neutral.save(REPORTS / "hair_refined_neutral.png")

sheet = Image.new("RGB", (1000, 800), "#adb3b8")
draw = ImageDraw.Draw(sheet)
names = ["face", "hair_crown", "hair_fringe_center",
         "hair_side_screen_left", "hair_side_screen_right"]
for index, name in enumerate(names):
    part = image_for(name).crop((420, 70, 600, 235)).resize((540, 495), Image.Resampling.NEAREST)
    x, y = (index % 2) * 500, (index // 2) * 260
    part.thumbnail((480, 240))
    sheet.paste(part, (x, y), part)
    draw.text((x + 3, y + 242), name, fill="black")
sheet.save(REPORTS / "hair_layers_refined.png")

report["validation"] = {
    "neutralChangedPixels": neutral_changes,
    "neutralMaxChannelDifference": neutral_max_difference,
    "fixedDarkHairPixelsInsideFringeSweep": fixed_dark_ghosts,
    "rootPinnedFringeTests": sample_checks,
}
(V2 / "hair_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"layers": len(layers), "eyeSlotAfter": eye_slot_after,
                  **report["validation"]}))
