# Models

이 디렉터리는 자동 의류 정리 로봇 시스템 **「접신」**의 Jetson Runtime에서 사용하는 AI 추론 모델을 포함합니다.

의류 영역을 검출하기 위한 Segmentation 모델, 상의 및 하의의 주요 특징점을 검출하기 위한 Pose Estimation 모델, 상의의 다음 조작 동작을 결정하기 위한 커스텀 학습 모델을 사용합니다.

각 모델은 NVIDIA Jetson Orin Nano에서 실시간 추론에 사용할 수 있도록 TensorRT Engine 형식으로 변환했습니다.

현재 제출본에서는 다음 모델을 사용합니다.

- Garment Segmentation 모델
- 상의 Pose 모델
- 하의 Pose 모델
- 상의 동작 결정 모델

---

## 1. 디렉터리 구성

    SW/Jetson/models/
    ├── README.md
    ├── segmentation/
    │   └── kfashion_yolo26s_seg3_e100_best.engine
    │
    └── pose/
        ├── upper/
        │   └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine
        │
        └── lower/
            └── bottom_pose8_beige_finetune_v2_best.engine

상의와 하의는 동일한 Garment Segmentation 모델을 공유하며, 의류 구조의 차이를 반영하기 위해 Pose 모델은 각각 별도로 사용합니다.

상의 자동 조작에서는 Segmentation 및 Pose 결과와 함께 현재 의류 상태를 입력으로 사용하는 별도의 동작 결정 모델을 사용합니다.

---

## 2. Segmentation Model

파일:

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

카메라 영상에서 의류가 차지하는 영역을 픽셀 단위의 마스크로 검출하는 TensorRT Segmentation Model입니다.

Segmentation 결과는 다음 정보 계산에 사용됩니다.

- 의류 전체 영역 검출
- Garment Mask 생성
- 의류 중심 계산
- 외곽 Contour 분석
- Bounding Geometry 계산
- 파지 가능한 내부 영역 계산
- 의류 정렬 상태 분석
- Pose 결과와의 기하 관계 분석
- Wrinkle / Fold 분석을 위한 유효 의류 영역 생성

검출된 Mask는 단순한 의류 존재 여부 판단뿐만 아니라 실제 로봇팔 파지점 계산, Geometry 분석 및 Manipulation Planning에도 사용됩니다.

본 Segmentation Model은 상의와 하의 Runtime에서 공통으로 사용합니다.

---

## 3. 상의 Pose Model

파일:

    SW/Jetson/models/pose/upper/
    └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

상의의 주요 구조를 나타내는 Keypoint를 검출하는 Pose Estimation TensorRT Model입니다.

Pose 결과는 다음 작업에 사용됩니다.

- 상의 방향 판단
- 주요 Landmark 검출
- 의류 형상 분석
- 파지점 후보 생성
- 최종 파지점 결정
- Segmentation Mask와의 기하 관계 분석
- 로봇팔 조작을 위한 기준점 생성

상의 Runtime에서는 Segmentation 결과와 Pose Keypoint를 결합하여 의류의 현재 배치 상태를 분석하고 두 로봇팔이 파지할 위치를 계산합니다.

Repository-Relative Runtime Entry:

    SW/Jetson/preprocessing/upper/run_upper.py

Dependency Path 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

---

## 4. 상의 Action Decision Model

상의 자동 조작에서는 현재 의류 상태를 바탕으로 **다음에 수행할 조작 동작을 결정하기 위해 별도로 학습한 커스텀 모델**을 사용합니다.

주요 파일:

    top_board_state_v2_fp32.engine
    state_normalization.npz

`top_board_state_v2_fp32.engine`은 실제 Jetson에서 동작 판단에 사용하는 TensorRT 모델이며, `state_normalization.npz`는 모델에 입력되는 상태값을 정규화할 때 사용합니다.

모델은 크게 다음 두 종류의 정보를 입력으로 사용합니다.

- Folding Board 위의 현재 의류 영상
- Segmentation, Pose, 주름, 중심 위치 등에서 계산한 의류 상태값

의류 영상의 특징과 상태값을 함께 분석하여 현재 상태에서 필요한 다음 조작을 판단합니다.

주요 판단 대상:

- CENTER
- SPREAD
- LONG_PULL
- PRESS
- ROTATE
- ORTHO_SPREAD
- FINISH

학습에는 PyTorch 기반의 **ResNet18 이미지 특징 추출부와 상태값을 처리하는 MLP를 결합한 분류 모델**을 사용했습니다.

학습이 완료된 모델은 다음 순서로 Jetson용 TensorRT Engine으로 변환했습니다.

    PyTorch Model (.pt)
            ↓
    ONNX
            ↓
    TensorRT Engine
            ↓
    Jetson Runtime

현재 상의 Runtime에서는 커스텀 학습 모델의 판단을 우선 사용하며, 모델의 신뢰도가 부족하거나 적용 조건을 만족하지 못하는 경우 기존 규칙 기반 상태 판단 로직을 사용합니다.

실제 로봇의 파지점과 이동 경로는 동작 결정 모델이 직접 생성하지 않으며, 기존에 검증된 조작 계획 및 안전 검사 로직에서 최종 계산합니다.

---

## 5. 하의 Pose Model

파일:

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine

하의 의류의 주요 특징점을 추론하기 위한 TensorRT 기반 Pose Model입니다.

본 모델은 허리, 가랑이, 양쪽 밑단의 주요 위치를 검출하며, 검출된 Pose 결과는 하의의 형태와 방향을 분석하고 실제 로봇 동작을 계획하는 데 사용됩니다.

하의 Pose 결과는 다음 분석 및 동작 계획에 활용됩니다.

- 허리선 구조 분석
- 가랑이 위치 분석
- 양쪽 다리 구조 분석
- 밑단 영역 판단
- 하의 방향 추정
- 의류 중심축 분석
- Segmentation Mask와의 결합
- 접힘 및 좌우 비대칭 분석
- 로봇 파지 후보 생성
- `PRESS_SWEEP` 동작 계획
- `WAIST_PULL_LAYDOWN` 동작 계획
- `ALIGN` 정렬 계획
- `FINISH` 상태 평가

하의 Runtime에서는 Pose 결과를 Segmentation Mask, 주름 정보 및 의류 형태 분석 결과와 결합하여 현재 하의의 위치, 방향, 펼쳐진 정도와 추가 조작 필요 여부를 판단합니다.

주요 인식 모듈:

    SW/Jetson/preprocessing/lower/dual/undistort/
    ├── step_e49_bottom_perception.py
    ├── step_e62_bottom_perception.py
    └── step_d25_v2.py

Runtime 실행 파일:

    SW/Jetson/preprocessing/lower/run_lower.py

의존성 경로 확인:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

---
## 6. 모델 사용 흐름

전체적인 의류 인식 및 판단 과정은 다음과 같습니다.

    ELP OV2710 Camera
            ↓
    Camera Calibration / Undistortion
            ↓
    의류 Segmentation
            ↓
    의류 Mask
            ↓
    상의 또는 하의 특징점 추론
            ↓
    Mask + Pose + Geometry 분석
            ↓
    Landmark / Grasp Candidate 계산
            ↓
    Calibration 기반 Robot Workspace 좌표 변환
            ↓
    Two Robotic Arms Manipulation

상의의 경우 의류 인식 이후 다음 동작을 결정하는 과정이 추가됩니다.

    현재 의류 이미지
            +
    의류 상태
            ↓
    상의 동작 결정 모델
            ↓
    다음 조작 동작 판단
            ↓
    Manipulation Planning
            ↓
    Two Robotic Arms Manipulation
            ↓
    Re-observation
            ↓
    다음 동작 판단 / FINISH

상의와 하의 모두 Segmentation Model을 사용하지만 Pose Model과 후속 Geometry 및 Manipulation Logic은 각 의류 구조에 맞게 별도로 구성했습    SW/Jetson/preprocessing/lower/dual/
    ├── step_e49_bottom_perception.py
    ├── step_e62_bottom_perception.py
    └── step_d25_v2.py

Repository-Relative Runtime Entry:

    SW/Jetson/preprocessing/lower/run_lower.py

Dependency Path 확인:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

---

## 6. 모델 사용 흐름

전체적인 의류 인식 및 판단 과정은 다음과 같습니다.

    ELP OV2710 Camera
            ↓
    Camera Calibration / Undistortion
            ↓
    의류 Segmentation
            ↓
    의류 Mask
            ↓
    상의 또는 하의 특징점 추론
            ↓
    Mask + Pose + Geometry 분석
            ↓
    Landmark / Grasp Candidate 계산
            ↓
    Calibration 기반 Robot Workspace 좌표 변환
            ↓
    Two Robotic Arms Manipulation

상의의 경우 의류 인식 이후 다음 동작을 결정하는 과정이 추가됩니다.

    현재 의류 이미지
            +
    의류 상태
            ↓
    상의 동작 결정 모델
            ↓
    다음 조작 동작 판단
            ↓
    Manipulation Planning
            ↓
    Two Robotic Arms Manipulation
            ↓
    Re-observation
            ↓
    다음 동작 판단 / FINISH

상의와 하의 모두 Segmentation Model을 사용하지만 Pose Model과 후속 Geometry 및 Manipulation Logic은 각 의류 구조에 맞게 별도로 구성했습니다.

---

## 7. Runtime 연동

### 상의

Wrapper:

    SW/Jetson/preprocessing/upper/run_upper.py

Segmentation Model:

    SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine

Upper Pose Model:

    SW/Jetson/models/pose/upper/tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

Upper Action Decision Model:

    top_board_state_v2_fp32.engine
    state_normalization.npz

상의 Runtime은 Segmentation 및 Pose 결과를 이용해 의류 상태를 분석하고, 커스텀 학습 모델을 통해 다음 조작 동작을 판단합니다.

---

### 하의

Wrapper:

    SW/Jetson/preprocessing/lower/run_lower.py

Segmentation Model:

    SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine

Lower Pose Model:

    SW/Jetson/models/pose/lower/bottom_pose8_beige_finetune_v2_best.engine

`run_lower.py`는 GitHub Repository 내부 경로를 계산하여 기존 하의 Runtime에 필요한 Model 및 Calibration 경로를 전달합니다.

이를 통해 검증된 하의 핵심 Source를 직접 수정하지 않고 Repository-Relative 실행 구조를 사용할 수 있습니다.

---

## 8. 검증 환경

현재 TensorRT Engine이 사용된 Jetson Runtime 환경:

- NVIDIA Jetson Orin Nano
- Ubuntu 22.04.3
- Python 3.10.12
- TensorRT 10.7.0
- OpenCV 4.11.0
- PyTorch 2.10.0
- PyTorch CUDA 12.6
- NumPy 1.26.4
- Ultralytics 8.4.45
- XGBoost 3.2.0
- Docker 29.7.2
