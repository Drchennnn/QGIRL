"""Single-input Modal runner for the pinned See-through head experiment.

Importing this module is safe. Cloud resources are used only when the local
entrypoint is explicitly executed with ``modal run``.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
import time
import traceback
from pathlib import Path

import modal


SOURCE_DIR = Path(__file__).resolve().parent
LOCAL_MODE = SOURCE_DIR.name == "adapters"
ROOT = SOURCE_DIR.parent if LOCAL_MODE else Path("/opt")
UPSTREAM = ROOT / "upstream/see-through" if LOCAL_MODE else ROOT / "see-through"
SPEC_PATH = ROOT / "adapters/modal_run_spec.json"
OUTPUT_DIR = ROOT / "layers/seethrough_run_004"
MAX_RESULT_BYTES = 90 * 1024 * 1024
REMOTE_REPO = "/opt/see-through"

app = modal.App("character-seethrough-head-experiment")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.1-runtime-ubuntu22.04", add_python="3.12"
    )
    .apt_install("git", "libgl1", "libglib2.0-0")
    .uv_pip_install(
        "torch==2.8.0+cu128",
        "torchvision==0.23.0+cu128",
        index_url="https://download.pytorch.org/whl/cu128",
    )
    .uv_pip_install(
        "numpy==2.2.6",
        "opencv-python==4.13.0.92",
        "pillow==12.1.1",
        "pillow-jxl-plugin==1.3.7",
        "pyyaml==6.0.3",
        "transformers==5.0.0",
        "diffusers==0.37.0",
        "huggingface-hub==1.7.2",
        "tokenizers==0.22.2",
        "accelerate==1.13.0",
        "safetensors==0.7.0",
        "timm @ git+https://github.com/huggingface/pytorch-image-models@6e3fdda39508db30766f9d9e6ec32380ebee8b8c",
        "simple-parsing==0.1.8",
        "kornia==0.8.2",
        "omegaconf==2.3.0",
        "pycocotools==2.0.11",
        "grad-cam==1.5.5",
        "scipy==1.15.3",
        "scikit-image==0.25.2",
        "scikit-learn==1.7.2",
        "pandas==2.3.3",
        "psd-tools[composite]==1.14.2",
        "einops==0.8.2",
        "tqdm==4.67.3",
        "click==8.3.1",
        "termcolor==3.3.0",
        "colorama==0.4.6",
    )
    .add_local_dir(
        UPSTREAM,
        remote_path=REMOTE_REPO,
        copy=True,
        ignore=[
            ".git",
            "**/.git/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.ipynb",
            "ui/test_screenshots/**",
            "common/assets/representative.jpg",
            "common/assets/test_image*.png",
        ],
    )
    .run_commands(
        f"cd {REMOTE_REPO} && pip install -e common -e annotators",
        f"cd {REMOTE_REPO} && ln -s common/assets assets",
    )
)


@app.function(
    image=image,
    gpu="L4",
    cpu=4.0,
    memory=8192,
    timeout=1800,
    retries=0,
    scaledown_window=60,
    max_containers=1,
)
def decompose_head(image_bytes: bytes, source_name: str) -> bytes:
    import os
    import subprocess
    import tempfile

    if source_name not in {"reference_profile.png", "reference_back.png", "reference_three_quarter.png", "beeftv_generated.png"}:
        raise ValueError("Unreviewed source name")

    if len(image_bytes) > 5 * 1024 * 1024:
        raise ValueError("Input exceeds the fixed 5 MiB guard")

    with tempfile.TemporaryDirectory(prefix="seethrough-head-") as workdir:
        source = Path(workdir) / source_name
        output = Path(workdir) / "output"
        source.write_bytes(image_bytes)
        output.mkdir()
        env = os.environ.copy()
        env["HF_HUB_DISABLE_TELEMETRY"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        env["CHARACTER_HEAD_MODE"] = ("back_body_only" if source_name == "reference_back.png"
                                      else "full_input_head_crop")
        print(f"Starting {source_name}", flush=True)
        command = [
            "python",
            "inference/scripts/inference_psd.py",
            "--srcp",
            str(source),
            "--save_dir",
            str(output),
            "--resolution",
            "1280",
            "--seed",
            "42",
            "--inference_steps",
            "30",
            "--save_to_psd",
            "--tblr_split",
        ]
        subprocess.run(command, cwd=REMOTE_REPO, env=env, check=True)

        result_dir = output / source.stem
        psd_path = output / f"{source.stem}.psd"
        if not result_dir.is_dir():
            raise RuntimeError("See-through did not produce its output directory")
        if not psd_path.is_file():
            raise RuntimeError("See-through did not produce the requested PSD")

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for path in sorted(output.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(output))
        payload = archive.getvalue()
        if len(payload) > MAX_RESULT_BYTES:
            raise RuntimeError(
                f"Compressed result exceeds {MAX_RESULT_BYTES} bytes; refusing oversized return"
            )
        return payload


@app.local_entrypoint()
def main(back_only: bool = False, three_quarter_only: bool = False, beeftv_only: bool = False) -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["status"] == "remaining_views_recovery_authorized"
    assert spec["upstream"]["commit"] == "df019de5129d6c4b406587a14c3501669441a783"
    patch_path = UPSTREAM / "common/utils/inference_utils.py"
    if hashlib.sha256(patch_path.read_bytes()).hexdigest() != spec["upstream"]["localPatchSha256"]:
        raise RuntimeError("Upstream crop patch differs from reviewed specification")
    expected_inputs = [
        "inputs/reference_profile.png",
        "inputs/reference_back.png",
    ]
    if [item["file"] for item in spec["inputs"]] != expected_inputs:
        raise RuntimeError("Inputs differ from the reviewed remaining-view recovery specification")

    if sum((back_only, three_quarter_only, beeftv_only)) > 1:
        raise ValueError("Select only one recovery view")
    selected_inputs = [item for item in spec["inputs"]
                       if not back_only or item["file"] == "inputs/reference_back.png"]
    output_dir = ROOT / "layers/seethrough_run_006" if back_only else OUTPUT_DIR
    if three_quarter_only:
        extra = spec["additionalRecoveryInput"]
        if extra["file"] != "inputs/reference_three_quarter.png":
            raise RuntimeError("Unexpected three-quarter recovery input")
        selected_inputs = [extra]
        output_dir = ROOT / "layers/seethrough_run_007"
    if beeftv_only:
        selected_inputs = [{"file": "layers/front_hair_tips_008/exports/beeftv_generated.png", "sha256": "602b6936c60c3a84bce49e2e2304421de862b36618395860737aff0a962b8a98"}]
        output_dir = ROOT / "layers/seethrough_beeftv_008"

    # Validate the complete batch before any paid remote call.
    for configured in selected_inputs:
        input_path = ROOT / configured["file"]
        if hashlib.sha256(input_path.read_bytes()).hexdigest() != configured["sha256"]:
            raise RuntimeError(f"Input hash differs: {input_path.name}")

    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty output: {output_dir}")

    records = []
    failed = False
    for configured in selected_inputs:
        input_path = ROOT / configured["file"]
        started = time.monotonic()
        record = {"input": configured, "startedAt": datetime.now(timezone.utc).isoformat()}
        try:
            call = decompose_head.spawn(input_path.read_bytes(), input_path.name)
            record["functionCallId"] = call.object_id
            print(f"Submitted {input_path.name}: {call.object_id}", flush=True)
            record["status"] = "submitted"
            (output_dir / "run_history.json").write_text(json.dumps(records + [record], indent=2) + "\n")
            payload = call.get()
            destination = output_dir / input_path.stem
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                for member in zf.namelist():
                    if Path(member).is_absolute() or ".." in Path(member).parts:
                        raise RuntimeError("Unsafe archive path")
                zf.extractall(destination)
            record["status"] = "received"
            record["outputDirectory"] = str(destination.relative_to(ROOT))
            print(f"Saved {input_path.name} to {destination}", flush=True)
        except Exception as exc:
            failed = True
            record["status"] = "failed"
            record["error"] = str(exc)
            record["errorType"] = type(exc).__name__
            record["traceback"] = traceback.format_exc()
            print(f"Failed {input_path.name}: {exc!r}\n{record['traceback']}", flush=True)
        finally:
            record["elapsedSeconds"] = round(time.monotonic() - started, 2)
            records.append(record)
            (output_dir / "run_history.json").write_text(json.dumps(records, indent=2) + "\n")
    if failed:
        raise RuntimeError("Some views failed; see run_history.json. No automatic retry.")
