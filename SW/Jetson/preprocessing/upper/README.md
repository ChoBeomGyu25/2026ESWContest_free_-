# 상의 의류 조작 Runtime

이 디렉터리는 팀 옷개스트라의 자동 의류 정리 로봇 시스템 **「접신」**에서 사용하는 상의 의류 조작용 Jetson Runtime을 포함합니다.

## 개요

상의 Runtime은 두 대의 RoArm M2-S와 상부 ELP OV2710 카메라를 이용하여 의류를 인식하고 파지, 이동, 공중 정렬, 배치하는 과정을 수행합니다.

주요 동작 흐름은 다음과 같습니다.

1. ARM2가 바구니에서 의류를 파지
2. 의류를 폴딩 보드 위로 이동 및 배치
3. 의류를 보드 중앙 방향으로 재정렬
4. 새로운 카메라 프레임에서 Segmentation 및 상의 Pose 추론 수행
5. 의류 형상과 Keypoint를 기반으로 최종 파지점 결정
6. 두 로봇팔이 동시에 의류 파지
7. 두 팔의 파지 간격을 유지하며 공중으로 상승
8. 폴딩 보드 기준으로 의류 위치 정렬
9. 두 로봇팔이 Laydown 궤적 수행
10. 의류를 놓고 두 로봇팔이 Standby 위치로 복귀

---

## 실행 방법

최종 실행은 `run_upper.py`를 사용합니다.

### 실제 로봇 동작

    python3 run_upper.py --physical-auto

### 파일 경로 확인

카메라와 로봇을 실제로 동작시키지 않고 필요한 Runtime 파일의 경로와 존재 여부만 확인합니다.

    python3 run_upper.py --paths-only

### Source Merge 구조 확인

    python3 run_upper.py --merge-self-test

`run_upper.py`는 GitHub 저장소 내부의 상대경로를 기준으로 모델, 카메라 보정 파일, Homography, 로봇 보정 파일 및 Runtime 소스의 위치를 자동으로 계산합니다.

이를 통해 실제 동작 검증이 끝난 핵심 Runtime 소스 내부의 기존 경로 및 Source Patch 구조를 대규모로 변경하지 않고도 GitHub 저장소 구조에서 실행할 수 있도록 구성했습니다.

---

## 주요 Runtime 파일

### 최종 통합 Runtime

- `d50_v14_fix11_basket_frontend_fix111_second_grasp_open_statefix.py`
  - 최종 상의 통합 실행 코드

### 기반 Runtime

- `basket_hover_torque_auto_grasp_dual_handoff_v25_fix11_raw_preview_post_mask_v8.py`
  - 바구니 파지, 보드 배치 및 Dual-Arm 조작을 담당하는 기반 Runtime

- `d50_v13.py`
  - 의류 인식, 형상 분석 및 조작 판단에 필요한 Runtime 기능 제공

### 보조 모듈

- `step_d25_v2.py`
- `step_e49_bottom_perception.py`
- `step_e62_bottom_perception.py`

일부 보조 모듈은 개발 과정에서 사용한 기존 파일명을 그대로 유지하고 있습니다.

`step_e49_bottom_perception.py`, `step_e62_bottom_perception.py`와 같은 파일은 현재 상의 통합 Runtime의 Dependency로 사용되지만, 검증된 Import 및 Source Patch 구조와의 호환성을 유지하기 위해 파일명을 변경하지 않았습니다.

FIX111, FIX11, D50 계열 코드는 일부 Source-Text Patch 방식으로 동작하므로 검증 없이 파일명을 변경하거나 자동 Formatter를 적용하지 않는 것을 권장합니다.

---

## 공통 Dependency

상의와 하의 Runtime에서 공통으로 사용하는 파일은 중복 저장하지 않고 `SW/Jetson/common`과 `SW/Jetson/models` 디렉터리에 배치합니다.

### Camera

- `SW/Jetson/common/camera/camera_undistort.py`
- `SW/Jetson/common/camera/elp_ov2710_1280x720_calibration.npz`

### Calibration

- `SW/Jetson/common/calibration/dual_roarm_folding_board_config.json`
- `SW/Jetson/common/calibration/basket_arm2_5point_affine.json`
- `SW/Jetson/common/calibration/elp_ov2710_folding_board_homography_cache.json`

### AI Model

- `SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine`
- `SW/Jetson/models/pose/upper/tshirt_pose_yolo26m_synth_artf_board_v1_best.engine`

Homography는 실제 상의 Runtime에서 검증된 H-only Calibration 파일을 사용합니다.

---

## Runtime 환경

- NVIDIA Jetson Orin Nano
- Ubuntu 22.04.3
- Python 3.10.12
- TensorRT 10.7.0
- OpenCV 4.11.0
- NumPy 1.26.4
- Ultralytics 8.4.45
- Dual RoArm M2-S
- ELP OV2710 Camera
- ARM1 Serial Port: `/dev/roarm_1`
- ARM2 Serial Port: `/dev/roarm_2`
- Camera Device: `/dev/video0`

---

## Runtime Manifest

`UPPER_RUNTIME_MANIFEST.json`에는 제출용 상의 Runtime에 필요한 주요 파일과 각 파일의 SHA-256 해시값이 기록되어 있습니다.

제출용 Runtime은 코드, 보정 파일, 카메라 Calibration 및 TensorRT Engine의 누락이나 잘못된 교체를 방지하기 위해 실제 검증된 파일의 SHA-256을 기준으로 구성했습니다.
