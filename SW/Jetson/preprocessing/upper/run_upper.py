#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository-relative launcher for the upper-garment FIX111 runtime.

This wrapper does not modify FIX111/FIX11/D50. It resolves the GitHub repository
layout and passes explicit paths to the validated runtime.

Usage:
    python3 run_upper.py --paths-only
    python3 run_upper.py --merge-self-test
    python3 run_upper.py --physical-auto
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

UPPER_DIR = Path(__file__).resolve().parent
JETSON_DIR = UPPER_DIR.parent.parent

ENTRY = UPPER_DIR / "d50_v14_fix11_basket_frontend_fix111_second_grasp_open_statefix.py"
FIX11 = UPPER_DIR / "basket_hover_torque_auto_grasp_dual_handoff_v25_fix11_raw_preview_post_mask_v8.py"
D50 = UPPER_DIR / "d50_v13.py"

COMMON_CAMERA = JETSON_DIR / "common" / "camera"
COMMON_CALIB = JETSON_DIR / "common" / "calibration"
MODELS = JETSON_DIR / "models"

CONFIG = COMMON_CALIB / "dual_roarm_folding_board_config.json"
HFILE = COMMON_CALIB / "elp_ov2710_folding_board_homography_cache.json"
BASKET = COMMON_CALIB / "basket_arm2_5point_affine.json"
CAMERA_CALIB = COMMON_CAMERA / "elp_ov2710_1280x720_calibration.npz"
SEG_MODEL = MODELS / "segmentation" / "kfashion_yolo26s_seg3_e100_best.engine"
POSE_MODEL = MODELS / "pose" / "upper" / "tshirt_pose_yolo26m_synth_artf_board_v1_best.engine"

REQUIRED = {
    "entrypoint": ENTRY,
    "fix11": FIX11,
    "d50": D50,
    "config": CONFIG,
    "homography": HFILE,
    "basket_calibration": BASKET,
    "camera_calibration": CAMERA_CALIB,
    "segmentation_model": SEG_MODEL,
    "upper_pose_model": POSE_MODEL,
}


def print_paths() -> None:
    print("[UPPER-REPO-LAYOUT]")
    print(f"upper_dir={UPPER_DIR}")
    print(f"jetson_dir={JETSON_DIR}")
    for key, path in REQUIRED.items():
        print(f"{key}={path} exists={path.is_file()}")
    print(f"common_camera={COMMON_CAMERA} exists={COMMON_CAMERA.is_dir()}")


def main() -> int:
    user_args = list(sys.argv[1:])
    paths_only = False
    if "--paths-only" in user_args:
        user_args.remove("--paths-only")
        paths_only = True

    missing = [f"{key}: {path}" for key, path in REQUIRED.items() if not path.is_file()]
    if missing:
        print("[UPPER-LAUNCH-BLOCKED] required submission files are missing:", file=sys.stderr)
        for item in missing:
            print("  " + item, file=sys.stderr)
        return 2

    # FIX11 imports camera_undistort by module name. Keep the shared camera
    # directory on PYTHONPATH instead of duplicating it under upper/.
    pythonpath_parts = [str(UPPER_DIR), str(COMMON_CAMERA)]
    old_pythonpath = os.environ.get("PYTHONPATH", "")
    if old_pythonpath:
        pythonpath_parts.append(old_pythonpath)
    os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    print_paths()
    if paths_only:
        return 0

    canonical_args = [
        "--fix11-source", str(FIX11),
        "--d50-source", str(D50),
        "--config", str(CONFIG),
        "--hfile", str(HFILE),
        "--calib-file", str(BASKET),
        "--camera-calibration", str(CAMERA_CALIB),
        "--seg-model", str(SEG_MODEL),
        "--tshirt-pose-model", str(POSE_MODEL),
        "--camera", "0",
        "--backend", "v4l2",
        "--width", "1280",
        "--height", "720",
        "--arm1-port", "/dev/roarm_1",
        "--arm2-port", "/dev/roarm_2",
        "--speed", "1.12",
    ]

    argv = [sys.executable, str(ENTRY)] + canonical_args + user_args
    print("[UPPER-LAUNCH] executing canonical repository-relative FIX111 runtime")
    print("[UPPER-LAUNCH] " + " ".join(argv))
    os.execv(sys.executable, argv)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
