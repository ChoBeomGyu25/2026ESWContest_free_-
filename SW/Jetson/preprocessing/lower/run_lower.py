#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repository-relative launcher for the lower-garment runtime.

The original lower-garment source files are intentionally left untouched.
This launcher only supplies repository-relative dependency paths and performs
an optional frozen-artifact integrity check.

Execution modes:
    python3 run_lower.py --paths-only
    python3 run_lower.py
    python3 run_lower.py --hover
    python3 run_lower.py --physical

IMPORTANT:
    --physical enables actual RoArm motion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
JETSON_ROOT = HERE.parent.parent

DUAL = HERE / "dual"
UNDISTORT = DUAL / "undistort"

COMMON_CALIB = JETSON_ROOT / "common" / "calibration"
MODELS = JETSON_ROOT / "models"

ENTRY = UNDISTORT / "bottom_vla-16.py"

PATHS = {
    # Main / motion runtime
    "bottom_vla": ENTRY,
    "main33": UNDISTORT / "main-33.py",
    "d50": UNDISTORT / "50-1.py",
    "d54": UNDISTORT / "54-3.py",
    "d55": UNDISTORT / "55-5.py",
    "d58": UNDISTORT / "58-3.py",
    "d60": UNDISTORT / "60-13.py",
    "align": UNDISTORT / "align-11.py",

    # Perception
    "e49": DUAL / "step_e49_bottom_perception.py",
    "e62": DUAL / "step_e62_bottom_perception.py",
    "d25": DUAL / "step_d25_v2.py",

    # Lower camera geometry
    "camera_undistort": UNDISTORT / "camera_undistort.py",
    "camera_calibration": UNDISTORT / "elp_ov2710_1280x720_calibration.npz",
    "lower_homography": UNDISTORT / "elp_ov2710_folding_board_homography_cache.json",
    "camera_controls": DUAL / "elp_ov2710_camera_controls.json",

    # Shared calibration
    "config": COMMON_CALIB / "dual_roarm_folding_board_config.json",
    "basket_calib": COMMON_CALIB / "basket_arm2_5point_affine.json",

    # Models
    "seg_model": MODELS / "segmentation" / "kfashion_yolo26s_seg3_e100_best.engine",
    "pose_model": MODELS / "pose" / "lower" / "bottom_pose8_beige_finetune_v2_best.engine",
}


EXPECTED_SHA256 = {
    "bottom_vla": "30d3a074ef648df4b132cf90775d02d0ae1698fdab789ea855b05b5d42463f4f",
    "main33": "8e3ad66082094aafb8162cc142e9cbf9695cec199838f17d7cebdc9278e959fb",
    "d50": "476c65eaa3659db346608b88acf7eeaa47e87b5e2604d0bcc32c88fc447e7e9d",
    "d54": "8ba27ec9f7daf5384a3bbc58c9c4d2e645be11319b23d3444aed96fc952f74ba",
    "d55": "4e79d141f87d211fcf7ec6d49d23c6589ea11fcdde23ed5be8834056c7098d22",
    "d58": "6635382ed3b812689fbd1c265d2766604a77c64d2d77c678b5c12d54b0c5dd2c",
    "d60": "ca8c13ae00e07717e3e6674328e246d02adf01c79389cf49c4884d08304f7945",
    "align": "09e84795afbd959a6071954028d28363f4d2d2ba9f24f08ddc4aeb195833ca39",

    "e49": "7b0cd0c9e41db24c4932979d0cd0fb9b3f9a14806bcb7a1c168ea45e83c7d356",
    "e62": "e670340289ccb782d3e52078878f92d402e18e235dfdabf25431fa4676361a67",
    "d25": "68524697d497d2c3fb53ad1ba0d6a5306ba2d9b9b7e252c2df81caeeb65d60b5",

    "camera_undistort": "4dcf2b0f74e2dff518184fca5a6910c2ec1813c109491b46502b6c06304cc348",
    "camera_calibration": "343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6",
    "lower_homography": "0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45",
    "camera_controls": "222e1b6826666a80918a271ea3c29dff62c77ecc94002dc4027a185e075bb206",

    "config": "807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373",
    "basket_calib": "546dc9c74cc629e407bad4967b9c94d267012e85bd0ef0d86ac5fe73a536d8d8",

    "seg_model": "ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725",
    "pose_model": "5bc3bc60fd545b3c62bbef8c8d41ac4ac372c6d169bc18da01d283fa82f3cbe8",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_paths() -> bool:
    print("=" * 92)
    print("LOWER RUNTIME DEPENDENCY CHECK")
    print("=" * 92)

    failures = 0

    for name, path in PATHS.items():
        expected = EXPECTED_SHA256.get(name)

        if not path.is_file():
            print(f"[FAIL] {name}")
            print(f"       MISSING: {path}")
            failures += 1
            continue

        actual = sha256(path)
        hash_ok = expected is None or actual == expected

        print(f"[{'PASS' if hash_ok else 'FAIL'}] {name}")
        print(f"       path   = {path}")
        print(f"       size   = {path.stat().st_size} bytes")
        print(f"       sha256 = {actual}")

        if not hash_ok:
            print(f"       EXPECT = {expected}")
            failures += 1

    print()
    print("=" * 92)
    print("LOWER HOMOGRAPHY SEMANTIC CHECK")
    print("=" * 92)

    h_path = PATHS["lower_homography"]

    try:
        data = json.loads(h_path.read_text(encoding="utf-8"))
        keys = sorted(data.keys())

        print(f"path = {h_path}")
        print(f"keys = {keys}")

        required = {"H", "raw_H", "camera_geometry", "schema_version"}
        missing = sorted(required.difference(data.keys()))

        if missing:
            print(f"[FAIL] lower Homography missing keys: {missing}")
            failures += 1
        else:
            print("[PASS] lower Homography contains H + raw_H + camera_geometry + schema_version")
    except Exception as exc:
        print(f"[FAIL] lower Homography JSON read failed: {exc!r}")
        failures += 1

    print()
    print("=" * 92)
    print(
        f"SUMMARY: PASS={len(PATHS) - failures} "
        f"FAIL={failures} TOTAL={len(PATHS)}"
    )
    print("=" * 92)

    return failures == 0


def has_option(argv: list[str], name: str) -> bool:
    return any(x == name or x.startswith(name + "=") for x in argv)


def build_runtime_argv(mode: str, extra: list[str]) -> list[str]:
    outputs = HERE / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    argv = [
        str(ENTRY),

        # bottom_vla-16 front-end sources
        "--base-main", str(PATHS["main33"]),
        "--d60-source", str(PATHS["d60"]),
        "--position-source", str(PATHS["d58"]),
        "--align-source", str(PATHS["align"]),
        "--basket-calib", str(PATHS["basket_calib"]),

        # main-33 action sources
        "--d50-source", str(PATHS["d50"]),
        "--d54-source", str(PATHS["d54"]),
        "--d55-source", str(PATHS["d55"]),
        "--d50-basket-calib", str(PATHS["basket_calib"]),

        # calibration / camera geometry
        "--config", str(PATHS["config"]),
        "--hfile", str(PATHS["lower_homography"]),
        "--camera-calibration", str(PATHS["camera_calibration"]),
        "--camera-controls-json", str(PATHS["camera_controls"]),

        # model artifacts
        "--seg-model", str(PATHS["seg_model"]),
        "--pose-model", str(PATHS["pose_model"]),

        # generated runtime artifacts
        "--empty-board-raw-path", str(outputs / "d34_empty_board.png"),
        "--empty-board-corrected-path", str(outputs / "d34_empty_board_corrected.png"),
        "--dataset-root", str(outputs / "vla_training_data"),
    ]

    # Allow an explicit native --mode in passthrough arguments.
    if not has_option(extra, "--mode"):
        argv.extend(["--mode", mode])

    argv.extend(extra)
    return argv


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Repository-relative launcher for bottom_vla-16.py"
    )

    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--physical",
        action="store_true",
        help="Enable actual RoArm motion (--mode physical).",
    )
    modes.add_argument(
        "--hover",
        action="store_true",
        help="Use hover validation mode (--mode hover).",
    )
    modes.add_argument(
        "--dry-run",
        action="store_true",
        help="Use dry-run mode. This is the default.",
    )

    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="Verify all frozen runtime dependencies and exit without camera/robot startup.",
    )

    return parser.parse_known_args()


def main() -> int:
    wrapper, extra = parse_wrapper_args()

    if not verify_paths():
        print("[RUN-LOWER] dependency validation failed; runtime will not start.")
        return 2

    if wrapper.paths_only:
        print("[RUN-LOWER] paths-only validation complete.")
        return 0

    if wrapper.physical:
        mode = "physical"
    elif wrapper.hover:
        mode = "hover"
    else:
        mode = "dry-run"

    runtime_argv = build_runtime_argv(mode, extra)

    print()
    print("=" * 92)
    print("LOWER RUNTIME LAUNCH")
    print("=" * 92)
    print(f"mode       = {mode}")
    print(f"entry      = {ENTRY}")
    print(f"workingDir = {UNDISTORT}")
    print(f"config     = {PATHS['config']}")
    print(f"homography = {PATHS['lower_homography']}")
    print(f"segModel   = {PATHS['seg_model']}")
    print(f"poseModel  = {PATHS['pose_model']}")

    if mode == "physical":
        print("[WARNING] PHYSICAL MODE: robot motion is enabled.")

    print("=" * 92)

    # Preserve the original runtime's expected working directory.
    os.chdir(UNDISTORT)

    os.execv(
        sys.executable,
        [sys.executable, *runtime_argv],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
