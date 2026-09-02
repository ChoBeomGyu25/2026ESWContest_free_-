#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository-relative launcher for the submitted Upper garment-state automation.

The authoritative colleague source (upper.py) is intentionally kept byte-identical.
This launcher only resolves repository paths and passes them through the runtime's
existing CLI arguments.

Default execution is SAFE:
    --no-send --dry-run

Physical RoArm execution requires the explicit wrapper flag:
    --physical

Examples:
    python3 run_upper_automation.py --paths-only
    python3 run_upper_automation.py
    python3 run_upper_automation.py --physical
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path


AUTOMATION_DIR = Path(__file__).resolve().parent
UPPER_DIR = AUTOMATION_DIR.parent
JETSON_DIR = UPPER_DIR.parent.parent

ENTRY = AUTOMATION_DIR / "upper.py"

COMMON_CAMERA = JETSON_DIR / "common" / "camera"
COMMON_CALIB = JETSON_DIR / "common" / "calibration"
MODELS = JETSON_DIR / "models"

CONFIG = COMMON_CALIB / "dual_roarm_folding_board_config.json"
HFILE = COMMON_CALIB / "elp_ov2710_folding_board_homography_cache.json"

CAMERA_UNDISTORT = COMMON_CAMERA / "camera_undistort.py"
CAMERA_CALIB = COMMON_CAMERA / "elp_ov2710_1280x720_calibration.npz"
CAMERA_CONTROLS = COMMON_CAMERA / "elp_ov2710_camera_controls.json"

SEG_MODEL = (
    MODELS
    / "segmentation"
    / "kfashion_yolo26s_seg3_e100_best.engine"
)

POSE_MODEL = (
    MODELS
    / "pose"
    / "upper"
    / "tshirt_pose_yolo26m_synth_artf_board_v1_best.engine"
)

STATE_MODEL_DIR = (
    MODELS
    / "decision"
    / "upper"
    / "top_board_state_v2"
)

STATE_ENGINE = STATE_MODEL_DIR / "top_board_state_v2_fp32.engine"
STATE_NORM = STATE_MODEL_DIR / "state_normalization.npz"


REQUIRED = {
    "automation_source": ENTRY,
    "camera_undistort": CAMERA_UNDISTORT,
    "camera_calibration": CAMERA_CALIB,
    "camera_controls": CAMERA_CONTROLS,
    "board_config": CONFIG,
    "homography": HFILE,
    "segmentation_model": SEG_MODEL,
    "upper_pose_model": POSE_MODEL,
    "board_state_engine": STATE_ENGINE,
    "state_normalization": STATE_NORM,
}


EXPECTED_SHA256 = {
    "automation_source":
        "5925e404c5be87516b76b2d60e36221f4873f79f7b7d46eb8b79daea89165ee2",

    "camera_undistort":
        "4dcf2b0f74e2dff518184fca5a6910c2ec1813c109491b46502b6c06304cc348",

    "camera_calibration":
        "343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6",

    "camera_controls":
        "222e1b6826666a80918a271ea3c29dff62c77ecc94002dc4027a185e075bb206",

    "board_config":
        "807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373",

    "homography":
        "282ebbcb635068031f0c238b7ab1b7c715819771ced86d614311ff875a13f397",

    "segmentation_model":
        "ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725",

    "upper_pose_model":
        "8a5a737f1c019ca87b1889ed187553dc6d3769b1fdc6a77ccf35f6d873c8607c",

    "board_state_engine":
        "1a007dd9fb3277a6ccca3746dc63cfd4e6a734e45f8af7a579ecfefdeaff140c",

    "state_normalization":
        "d0c40c791845b39778a7ce44de79ef71d4bcf69da6f4a7f2523982c0943ff7b9",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_files() -> list[str]:
    failures: list[str] = []

    for key, path in REQUIRED.items():
        if not path.is_file():
            failures.append(f"MISSING {key}: {path}")
            continue

        expected = EXPECTED_SHA256.get(key)
        if expected:
            actual = sha256_file(path)
            if actual != expected:
                failures.append(
                    f"SHA256 MISMATCH {key}: expected={expected} actual={actual} path={path}"
                )

    return failures


def print_paths() -> None:
    print("[UPPER-AUTOMATION-REPO-LAYOUT]")
    print(f"automation_dir={AUTOMATION_DIR}")
    print(f"jetson_dir={JETSON_DIR}")

    for key, path in REQUIRED.items():
        exists = path.is_file()
        expected = EXPECTED_SHA256.get(key)

        if exists and expected:
            actual = sha256_file(path)
            hash_ok = actual == expected
        else:
            actual = None
            hash_ok = False

        print(
            f"{key}={path} "
            f"exists={exists} "
            f"sha256_ok={hash_ok}"
        )


def main() -> int:
    user_args = list(sys.argv[1:])

    paths_only = False
    physical = False

    if "--paths-only" in user_args:
        user_args.remove("--paths-only")
        paths_only = True

    if "--physical" in user_args:
        user_args.remove("--physical")
        physical = True

    failures = validate_files()

    if failures:
        print(
            "[UPPER-AUTOMATION-LAUNCH-BLOCKED] "
            "required submission files failed validation:",
            file=sys.stderr,
        )

        for item in failures:
            print("  " + item, file=sys.stderr)

        return 2

    # upper.py imports camera_undistort by module name.
    # Keep the shared camera directory on PYTHONPATH instead of duplicating it.
    pythonpath_parts = [
        str(AUTOMATION_DIR),
        str(COMMON_CAMERA),
    ]

    old_pythonpath = os.environ.get("PYTHONPATH", "")
    if old_pythonpath:
        pythonpath_parts.append(old_pythonpath)

    os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    print_paths()

    if paths_only:
        print("[UPPER-AUTOMATION] paths-only validation PASS")
        return 0

    canonical_args = [
        "--config", str(CONFIG),
        "--hfile", str(HFILE),
        "--camera-controls-json", str(CAMERA_CONTROLS),
        "--camera-calibration", str(CAMERA_CALIB),

        "--grasp-model", str(SEG_MODEL),
        "--pose-model", str(POSE_MODEL),

        "--vla-shadow-engine", str(STATE_ENGINE),
        "--vla-shadow-state-norm", str(STATE_NORM),

        "--camera", "0",
        "--backend", "v4l2",

        "--arm1-port", "/dev/roarm_1",
        "--arm2-port", "/dev/roarm_2",
    ]

    if physical:
        safety_args = ["--send"]

        print()
        print("=" * 78)
        print("WARNING: PHYSICAL MODE")
        print("RoArm serial control is enabled.")
        print("This mode can move ARM1 and ARM2.")
        print("=" * 78)
        print()
    else:
        # IMPORTANT:
        # upper.py opens serial devices whenever args.send is True,
        # even when dry_run=True. Therefore safe validation requires BOTH.
        #
        # Place these LAST so a user-provided --send cannot accidentally
        # override the wrapper's safe default.
        safety_args = [
            "--no-send",
            "--dry-run",
        ]

        print(
            "[UPPER-AUTOMATION] SAFE MODE: "
            "--no-send --dry-run enforced; RoArm serial control disabled"
        )

    argv = (
        [sys.executable, str(ENTRY)]
        + canonical_args
        + user_args
        + safety_args
    )

    print("[UPPER-AUTOMATION-LAUNCH]")
    print(" ".join(argv))

    os.execv(sys.executable, argv)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
