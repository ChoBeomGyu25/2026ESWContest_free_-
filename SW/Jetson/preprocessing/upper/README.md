# 상의 의류 조작 Runtime

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서 사용하는 상의 의류 조작용 Jetson 실행 코드를 포함합니다.

현재 상의 시스템은 두 단계로 구성되어 있습니다.

1. `run_upper.py`를 이용한 바구니 파지, Folding Board 배치 및 초기 정렬
2. `upper.py`를 이용한 학습 모델 기반 반복 의류 조작 및 종료 판단

현재는 두 실행 코드를 분리하여 사용하고 있으며, 추후 하나의 상의 통합 실행 코드로 연결할 예정입니다.

---

## 1. 개요

상의 시스템은 두 대의 로봇팔과 상부 ELP OV2710 카메라를 이용하여 의류를 인식하고, 파지·이동·정렬한 뒤 Folding이 가능한 상태까지 자동으로 조작합니다.

전체 동작 흐름은 다음과 같습니다.

    바구니의 상의 파지
            ↓
    Folding Board 위로 이동
            ↓
    의류 배치 및 초기 정렬
            ↓
    Segmentation / 상의 Pose 추론
            ↓
    초기 파지점 계산
            ↓
    두 로봇팔 파지
            ↓
    공중 정렬 및 Laydown
            ↓
    상의 자동 조작 코드 실행
            ↓
    현재 의류 상태 재관찰
            ↓
    학습 모델 기반 다음 동작 판단
            ↓
    필요한 조작 수행
            ↓
    재관찰 및 다음 동작 판단
            ↓
    FINISH

첫 번째 단계에서는 의류를 바구니에서 꺼내 Folding Board 위에 안정적으로 배치합니다.

두 번째 단계에서는 배치된 의류의 상태를 반복적으로 관찰하면서 필요한 조작을 자동으로 수행합니다.

---

## 2. 실행 구조

### 1단계: 상의 전처리 및 초기 배치

현재 상의 전처리 실행은 `run_upper.py`를 사용합니다.

실제 로봇 실행:

    python3 run_upper.py --physical-auto

`run_upper.py`는 다음 과정을 수행합니다.

1. ARM2가 바구니에서 의류 파지
2. Folding Board 위로 의류 이동
3. 의류 배치
4. Segmentation 및 상의 Pose 추론
5. 의류 형상과 Keypoint 분석
6. 최종 파지점 계산
7. 두 로봇팔이 의류 파지
8. 공중 상승 및 위치 정렬
9. Laydown
10. 로봇팔 대기 위치 복귀

---

### 2단계: 상의 자동 의류 조작

`run_upper.py`의 초기 배치 과정이 끝난 뒤에는 별도의 상의 자동 조작 코드인

    upper.py

를 실행합니다.

`upper.py`는 Folding Board 위에 놓인 상의를 다시 관찰하고, 현재 상태에 필요한 조작을 자동으로 결정하여 수행합니다.

기본 흐름:

    Camera Observation
            ↓
    Segmentation / Pose
            ↓
    의류 상태 분석
            ↓
    커스텀 학습 모델
            ↓
    다음 조작 동작 결정
            ↓
    파지점 및 이동 경로 계산
            ↓
    안전 조건 검사
            ↓
    로봇팔 조작
            ↓
    Standby 복귀
            ↓
    새로운 상태 재관찰
            ↓
    다음 동작 판단

이 과정을 반복하며 추가 조작이 필요하지 않은 상태에서는 `FINISH`를 판단하여 해당 의류의 자동 조작을 종료합니다.

현재 `run_upper.py`와 `upper.py`는 각각 검증된 기능을 유지하기 위해 분리되어 있으며, 추후 **초기 배치부터 반복 자동 조작 및 FINISH까지 하나의 실행 흐름으로 동작하도록 통합할 예정**입니다.

---

## 3. 상의 자동 동작 판단

상의 자동 조작에는 현재 의류 상태를 바탕으로 다음 동작을 결정하기 위해 직접 학습한 **커스텀 동작 결정 모델**을 사용합니다.

모델은 다음 정보를 함께 사용합니다.

- Folding Board 위의 현재 의류 영상
- Segmentation 결과
- 상의 Pose 결과
- 의류 중심 위치
- Mask 형상 및 크기
- Solidity
- 의류 방향
- 주름 및 CCA 분석 결과
- 기타 의류 상태값

학습 모델은 현재 상태에서 필요한 조작 동작을 분류합니다.

주요 동작:

- `CENTER`
- `SPREAD`
- `LONG_PULL`
- `PRESS`
- `ROTATE`
- `ORTHO_SPREAD`
- `FINISH`

현재 상의 자동 조작에서는 **커스텀 학습 모델의 판단을 우선 사용**합니다.

모델의 신뢰도가 부족하거나 적용 조건을 만족하지 못하는 경우에는 기존 **규칙 기반 상태 판단 로직**을 이용하여 동작을 결정합니다.

학습 모델은 어떤 동작이 필요한지를 판단하며, 실제 로봇의 파지점과 이동 경로는 기존에 검증된 조작 계획 및 안전 검사 로직에서 계산합니다.

---

## 4. 실행 방법

### 상의 전처리 및 초기 배치

실제 로봇 동작:

    python3 run_upper.py --physical-auto

### 파일 경로 확인

카메라와 로봇을 실제로 동작시키지 않고 필요한 파일의 경로와 존재 여부를 확인합니다.

    python3 run_upper.py --paths-only

### Source Merge 구조 확인

    python3 run_upper.py --merge-self-test

`run_upper.py`는 GitHub 저장소 내부의 상대경로를 기준으로 모델, 카메라 보정 파일, Homography, 로봇 보정 파일 및 실행 소스의 위치를 계산합니다.

이를 통해 기존 로봇에서 검증된 핵심 코드의 구조를 크게 변경하지 않고 GitHub 저장소에서도 실행할 수 있도록 구성했습니다.

---

## 5. 주요 실행 파일

### 상의 전처리 및 초기 배치

- `run_upper.py`
  - 상의 초기 실행 진입점
  - 필요한 파일 경로 확인 및 실제 상의 전처리 과정 실행

### 기존 상의 통합 코드

- `d50_v14_fix11_basket_frontend_fix111_second_grasp_open_statefix.py`
  - 바구니 파지부터 Folding Board 배치, 로봇팔 조작까지 수행하는 기존 상의 통합 코드

### 기반 코드

- `basket_hover_torque_auto_grasp_dual_handoff_v25_fix11_raw_preview_post_mask_v8.py`
  - 바구니 파지, 보드 배치 및 로봇팔 조작 기능 제공

- `d50_v13.py`
  - 의류 인식, 형상 분석 및 조작에 필요한 주요 기능 제공

### 상의 자동 조작 코드

- `upper.py`
  - Folding Board 위에 배치된 상의를 반복 관찰
  - 커스텀 학습 모델을 이용한 다음 동작 판단
  - 규칙 기반 판단 보조
  - 파지점 및 이동 경로 계산
  - 로봇팔 조작
  - 조작 후 재관찰
  - `FINISH`까지 자동 반복

### 보조 모듈

- `step_d25_v2.py`
- `step_e49_bottom_perception.py`
- `step_e62_bottom_perception.py`

일부 보조 모듈은 개발 과정에서 사용한 기존 파일명을 그대로 유지하고 있습니다.

`step_e49_bottom_perception.py`, `step_e62_bottom_perception.py`와 같은 파일은 현재 상의 실행 코드의 의존성으로 사용되며, 호환성을 유지하기 위해 파일명을 변경하지 않았습니다.

---

## 6. 공통 의존 파일

상의와 하의에서 공통으로 사용하는 파일은 중복 저장하지 않고 `SW/Jetson/common`과 `SW/Jetson/models` 디렉터리에 배치되었습니다.

### Camera

- `SW/Jetson/common/camera/camera_undistort.py`
- `SW/Jetson/common/camera/elp_ov2710_1280x720_calibration.npz`

### Calibration

- `SW/Jetson/common/calibration/dual_roarm_folding_board_config.json`
- `SW/Jetson/common/calibration/basket_arm2_5point_affine.json`
- `SW/Jetson/common/calibration/elp_ov2710_folding_board_homography_cache.json`

### 의류 인식 모델

- `SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine`
- `SW/Jetson/models/pose/upper/tshirt_pose_yolo26m_synth_artf_board_v1_best.engine`

### 상의 동작 결정 모델

상의 자동 조작 코드에서는 별도의 커스텀 학습 모델을 사용합니다.

주요 파일:

    top_board_state_v2_fp32.engine
    state_normalization.npz

- `top_board_state_v2_fp32.engine`
  - 현재 의류 상태에서 필요한 다음 조작 동작을 판단하는 TensorRT 모델

- `state_normalization.npz`
  - 모델 입력으로 사용하는 상태값의 정규화 정보

학습 원본과 모델 변환 과정에서는 `.pt`와 `.onnx` 파일을 사용했으며, Jetson에서 실제 추론할 때는 TensorRT Engine과 상태 정규화 파일을 사용합니다.

Homography는 실제 상의 실행 코드에서 검증된 Calibration 파일을 사용합니다.

---

## 7. 상의 자동화 구조

현재 상의 자동화는 **초기 배치를 담당하는 전처리 코드와 반복 의류 조작을 담당하는 자동화 코드를 연속적으로 동작시키는 구조**입니다.

현재는 개발 및 검증 과정에서 두 코드를 분리하여 관리하고 있으며, 추후 다음과 같이 하나의 통합 실행 구조로 구성할 예정입니다.

    run_upper.py
        ↓
    바구니 파지
        ↓
    Folding Board 배치
        ↓
    초기 의류 인식 및 정렬
        ↓
    Laydown
        ↓
    upper.py
        ↓
    현재 의류 상태 관찰
        ↓
    학습 모델 기반 동작 판단
        ↓
    필요한 조작 수행
        ↓
    재관찰
        ↓
    다음 동작 판단
        ↓
    FINISH

---

## 8. Runtime 환경

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

## 9. Runtime Manifest

`UPPER_RUNTIME_MANIFEST.json`에는 제출용 상의 실행에 필요한 주요 파일과 각 파일의 SHA-256 해시값이 기록되어 있습니다.

---
