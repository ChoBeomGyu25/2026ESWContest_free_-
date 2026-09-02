#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repository-relative launcher for the Lower V38 Full-Auto runtime.

Full-Auto stack:
    run_lower.py
      -> bottom_vla-38_submission_full_auto.py
      -> bottom_vla-23_submission_runtime.py
      -> main-33_submission_runtime.py

Default execution mode is dry-run.

Safe dependency-only validation:
    python3 run_lower.py --paths-only

Dry-run:
    python3 run_lower.py

IMPORTANT:
    --physical enables actual RoArm motion.

WARNING:
    Native hover mode is NOT assumed motion-free by this stack.  The underlying
    Main33 runtime can enable arm sending in hover mode.  Do not use --hover
    around powered robots unless that behavior is intentionally being tested.
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
COMMON_CAMERA = JETSON_ROOT / "common" / "camera"
MODELS = JETSON_ROOT / "models"

ENTRY = UNDISTORT / "bottom_vla-38_submission_full_auto.py"

PATHS = {
    # Full-Auto entry/runtime
    "v38": ENTRY,
    "v23": UNDISTORT / "bottom_vla-23_submission_runtime.py",
    "main33": UNDISTORT / "main-33_submission_runtime.py",

    # Action/runtime sources
    "d50": UNDISTORT / "50-1.py",
    "d54": UNDISTORT / "54-3.py",
    "d55": UNDISTORT / "55-5.py",
    "d58": UNDISTORT / "58-3.py",
    "d60": UNDISTORT / "60-15.py",
    "align": UNDISTORT / "align-11.py",

    # Full-Auto perception set.
    # These intentionally live beside the action modules so bare imports resolve
    # to the exact collaborator-tested undistort versions.
    "e49": UNDISTORT / "step_e49_bottom_perception.py",
    "e62": UNDISTORT / "step_e62_bottom_perception.py",
    "d25": UNDISTORT / "step_d25_v2.py",

    # Camera / Lower geometry
    "camera_undistort": UNDISTORT / "camera_undistort.py",
    "camera_calibration": COMMON_CAMERA / "elp_ov2710_1280x720_calibration.npz",
    "lower_homography": UNDISTORT / "elp_ov2710_folding_board_homography_cache.json",
    "camera_controls": DUAL / "elp_ov2710_camera_controls.json",

    # Shared calibration
    "config": COMMON_CALIB / "dual_roarm_folding_board_config.json",
    "basket_calib": COMMON_CALIB / "basket_arm2_5point_affine.json",

    # Models
    "seg_model": MODELS / "segmentation" / "kfashion_yolo26s_seg3_e100_best.engine",
    "pose_model": MODELS / "pose" / "lower" / "bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine",
}


EXPECTED_SHA256 = {
    "v38": "7008aed88e9c3ab304e3b823574039857a954fa2329fcf25a88cf54f12c727bc",
    "v23": "6e9011bd7aedc3c5a4f9190fd03ff39b72ee80cd445ec65f245aca19b4116776",
    "main33": "d681c0c92d0e70360c76bb376409e02b7cb51d040d7def35ee7f5cf32f1d4b86",

    "d50": "476c65eaa3659db346608b88acf7eeaa47e87b5e2604d0bcc32c88fc447e7e9d",
    "d54": "8ba27ec9f7daf5384a3bbc58c9c4d2e645be11319b23d3444aed96fc952f74ba",
    "d55": "4e79d141f87d211fcf7ec6d49d23c6589ea11fcdde23ed5be8834056c7098d22",
    "d58": "6635382ed3b812689fbd1c265d2766604a77c64d2d77c678b5c12d54b0c5dd2c",
    "d60": "208508d10d1f4c7825910218691c42afd623162e0f94748d35b14e75da455b4f",
    "align": "09e84795afbd959a6071954028d28363f4d2d2ba9f24f08ddc4aeb195833ca39",

    "e49": "95fbce3aab9eb7fe2239e83a5b1ba45fd6084fbf6199667914469bd365df7744",
    "e62": "fd2c4fefedc1d2e4dbcc371795809359093a705cb0f005f34950a2bda5ed4229",
    "d25": "7bafb834f8cc0d4114c6943fef73781599d6b12d72254a6b6300cabf28df3d3d",

    "camera_undistort": "4dcf2b0f74e2dff518184fca5a6910c2ec1813c109491b46502b6c06304cc348",
    "camera_calibration": "343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6",
    "lower_homography": "0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45",
    "camera_controls": "222e1b6826666a80918a271ea3c29dff62c77ecc94002dc4027a185e075bb206",

    "config": "807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373",
    "basket_calib": "546dc9c74cc629e407bad4967b9c94d267012e85bd0ef0d86ac5fe73a536d8d8",

    "seg_model": "ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725",
    "pose_model": "d40861c7db06b59bda50016fe2041b8d566d18060ff5f1ab1199d06a1ee7646f",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_paths() -> bool:
    print("=" * 96)
    print("LOWER V38 FULL-AUTO RUNTIME DEPENDENCY CHECK")
    print("=" * 96)

    failures = 0
    passes = 0

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

        if hash_ok:
            passes += 1
        else:
            print(f"       EXPECT = {expected}")
            failures += 1

    print()
    print("=" * 96)
    print("LOWER HOMOGRAPHY SEMANTIC CHECK")
    print("=" * 96)

    h_path = PATHS["lower_homography"]

    try:
        data = json.loads(h_path.read_text(encoding="utf-8"))
        keys = sorted(data.keys())
        required = {"H", "raw_H", "camera_geometry", "schema_version"}
        missing = sorted(required.difference(data.keys()))

        print(f"path = {h_path}")
        print(f"keys = {keys}")

        if missing:
            print(f"[FAIL] missing keys: {missing}")
            failures += 1
        else:
            print("[PASS] H + raw_H + camera_geometry + schema_version")
    except Exception as exc:
        print(f"[FAIL] Homography read failed: {exc!r}")
        failures += 1

    print()
    print("=" * 96)
    print(f"SUMMARY: PASS={passes} FAIL={failures} TOTAL={len(PATHS)}")
    print("=" * 96)

    return failures == 0


def has_option(argv: list[str], name: str) -> bool:
    return any(x == name or x.startswith(name + "=") for x in argv)


def build_runtime_argv(mode: str, extra: list[str]) -> list[str]:
    outputs = HERE / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    argv = [
        str(ENTRY),

        # V23 front-end source resolution
        "--base-main", str(PATHS["main33"]),
        "--d60-source", str(PATHS["d60"]),
        "--position-source", str(PATHS["d58"]),
        "--align-source", str(PATHS["align"]),
        "--basket-calib", str(PATHS["basket_calib"]),

        # Main33 action sources
        "--d50-source", str(PATHS["d50"]),
        "--d54-source", str(PATHS["d54"]),
        "--d55-source", str(PATHS["d55"]),
        "--d50-basket-calib", str(PATHS["basket_calib"]),

        # Repository-contained calibration / camera geometry
        "--config", str(PATHS["config"]),
        "--hfile", str(PATHS["lower_homography"]),
        "--camera-calibration", str(PATHS["camera_calibration"]),
        "--camera-controls-json", str(PATHS["camera_controls"]),

        # Repository-contained model artifacts
        "--seg-model", str(PATHS["seg_model"]),
        "--pose-model", str(PATHS["pose_model"]),

        # Writable runtime-generated artifacts
        "--empty-board-raw-path", str(outputs / "d34_empty_board.png"),
        "--empty-board-corrected-path", str(outputs / "d34_empty_board_corrected.png"),
    ]

    # Advanced passthrough may explicitly supply the native --mode.
    if not has_option(extra, "--mode"):
        argv.extend(["--mode", mode])

    argv.extend(extra)
    return argv


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Repository-relative launcher for Lower V38 Full-Auto runtime"
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
        help=(
            "Use native hover mode. WARNING: underlying Lower modules may still "
            "send robot commands in hover mode."
        ),
    )
    modes.add_argument(
        "--dry-run",
        action="store_true",
        help="Use dry-run mode. This is the default.",
    )

    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="Verify frozen runtime dependencies and exit before camera/robot startup.",
    )

    return parser.parse_known_args()


def main() -> int:
    wrapper, extra = parse_wrapper_args()

    if not verify_paths():
        print("[RUN-LOWER] dependency validation failed; runtime will not start.")
        return 2

    if wrapper.paths_only:
        print("[RUN-LOWER] paths-only validation complete. Runtime was NOT started.")
        return 0

    if wrapper.physical:
        mode = "physical"
    elif wrapper.hover:
        mode = "hover"
    else:
        mode = "dry-run"

    if mode == "physical":
        print("=" * 96)
        print("[RUN-LOWER-WARNING] PHYSICAL MODE: ACTUAL ROARM MOTION IS ENABLED")
        print("=" * 96)
    elif mode == "hover":
        print("=" * 96)
        print("[RUN-LOWER-WARNING] HOVER MODE MAY STILL SEND ROARM COMMANDS")
        print("=" * 96)

    argv = build_runtime_argv(mode, extra)

    print("[RUN-LOWER] entry =", ENTRY)
    print("[RUN-LOWER] mode  =", mode)
    print("[RUN-LOWER] executing V38 Full-Auto runtime")

    os.execv(
        sys.executable,
        [sys.executable] + argv,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
