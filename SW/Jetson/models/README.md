# Models

이 디렉터리는 자동 의류 정리 로봇 시스템 **「접신」**의 Jetson Runtime에서 사용하는 AI 추론 모델을 관리합니다.

카메라 영상에서 의류 영역을 검출하기 위한 Segmentation 모델과 상의·하의의 주요 특징점을 검출하기 위한 Pose 모델을 사용합니다.

또한 상의 Runtime에서는 현재 의류 상태를 분석하여 다음 조작 동작을 결정하기 위해 별도로 학습한 동작 결정 모델을 사용합니다.

Jetson에서 사용하는 주요 추론 모델은 NVIDIA Jetson Orin Nano에서 빠르게 추론할 수 있도록 TensorRT Engine 형식으로 변환했습니다.

현재 Runtime에서는 다음 모델을 사용합니다.

- Garment Segmentation 모델
- 상의 Pose 모델
- 하의 Pose 모델
- 상의 동작 결정 모델

---

## 1. 디렉터리 구성

주요 Segmentation 및 Pose 모델의 디렉터리 구조는 다음과 같습니다.

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
            └── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine

상의와 하의는 동일한 Garment Segmentation 모델을 공유하며, 의류 구조의 차이를 반영하기 위해 Pose 모델은 각각 별도로 사용합니다.

상의 Runtime에서는 Segmentation 및 Pose 결과와 함께 현재 의류 상태를 입력으로 사용하는 별도의 동작 결정 모델을 사용합니다.

---

## 2. Segmentation Model

파일:

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

카메라 영상에서 의류가 차지하는 영역을 픽셀 단위의 Mask로 검출하는 TensorRT 기반 Segmentation 모델입니다.

Segmentation 결과는 다음 정보 계산에 사용됩니다.

- 의류 전체 영역 검출
- Garment Mask 생성
- 의류 중심 위치 계산
- 외곽선 분석
- 의류 크기 및 형태 분석
- 파지 가능한 내부 영역 계산
- 의류 정렬 상태 분석
- Pose 결과와의 기하 관계 분석
- 주름 및 접힘 분석을 위한 유효 의류 영역 생성

검출된 Mask는 단순히 의류의 존재 여부를 판단하는 데 그치지 않고, 실제 로봇팔의 파지점 계산과 의류 형태 분석, 동작 계획 생성에도 사용됩니다.

본 Segmentation 모델은 상의와 하의 Runtime에서 공통으로 사용합니다.

---

## 3. 상의 Pose Model

파일:

    SW/Jetson/models/pose/upper/
    └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

상의의 주요 구조를 나타내는 특징점을 검출하는 TensorRT 기반 Pose 모델입니다.

Pose 결과는 다음 작업에 사용됩니다.

- 상의 방향 판단
- 주요 특징점 검출
- 의류 형상 분석
- 파지점 후보 생성
- 최종 파지점 결정
- Segmentation Mask와의 기하 관계 분석
- 로봇팔 조작을 위한 기준점 생성

상의 Runtime에서는 Segmentation 결과와 Pose 특징점을 결합하여 현재 의류의 배치 상태를 분석하고, 두 로봇팔이 파지할 위치를 계산합니다.

Runtime 실행 파일:

    SW/Jetson/preprocessing/upper/run_upper.py

의존성 경로 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

---

## 4. 상의 Action Decision Model

상의 자동 조작에서는 현재 의류 상태를 바탕으로 **다음에 수행할 조작 동작을 결정하기 위해 별도로 학습한 커스텀 모델**을 사용합니다.

주요 파일:

    top_board_state_v2_fp32.engine
    state_normalization.npz

`top_board_state_v2_fp32.engine`은 실제 Jetson Runtime에서 다음 동작을 판단하는 TensorRT 모델입니다.

`state_normalization.npz`는 모델에 입력되는 의류 상태값의 범위를 맞추기 위한 정규화 정보입니다.

모델은 크게 다음 두 종류의 정보를 입력으로 사용합니다.

- 폴딩보드 위의 현재 의류 영상
- Segmentation, Pose, 주름, 중심 위치 등에서 계산한 의류 상태값

의류 영상의 특징과 수치화된 상태 정보를 함께 분석하여 현재 상태에서 필요한 다음 조작을 판단합니다.

주요 판단 대상은 다음과 같습니다.

- `CENTER`
- `SPREAD`
- `LONG_PULL`
- `PRESS`
- `ROTATE`
- `ORTHO_SPREAD`
- `FINISH`

학습에는 PyTorch 기반의 **ResNet18 이미지 특징 추출부와 상태값을 처리하는 MLP를 결합한 분류 모델**을 사용했습니다.

학습이 완료된 모델은 다음 과정을 거쳐 Jetson에서 사용할 수 있는 TensorRT Engine으로 변환했습니다.

    PyTorch Model (.pt)
            ↓
    ONNX
            ↓
    TensorRT Engine
            ↓
    Jetson Runtime

현재 상의 Runtime은 **학습 모델과 기존 규칙 기반 상태 판단을 함께 사용하는 Hybrid 구조**로 구성했습니다.

모델의 신뢰도가 충분하고 실제 동작으로 연결할 수 있는 조건을 만족하면 학습 모델의 판단을 우선 사용합니다.

반대로 모델의 신뢰도가 부족하거나 안전 및 실행 조건을 만족하지 못하는 경우에는 기존 규칙 기반 상태 판단 로직을 사용합니다.

동작 결정 모델은 어떤 종류의 조작이 필요한지를 판단하는 역할을 담당하며, 실제 로봇의 파지점과 이동 경로를 직접 생성하지는 않습니다.

최종 파지점과 이동 경로는 각 동작별로 실제 로봇에서 검증된 조작 계획 및 안전 검사 로직을 통해 계산합니다.

---

## 5. 하의 Pose Model

파일:

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine

하의 의류의 주요 특징점을 추론하기 위한 TensorRT 기반 Pose 모델입니다.

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
- `FINISH` 상태 평가에 필요한 구조 정보 제공

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

전체적인 의류 인식 과정은 다음과 같습니다.

    ELP OV2710 Camera
            ↓
    카메라 보정 및 왜곡 보정
            ↓
    의류 Segmentation
            ↓
    의류 Mask 생성
            ↓
    상의 또는 하의 Pose 추론
            ↓
    Mask + Pose + 의류 형태 분석
            ↓
    특징점 및 파지 후보 계산
            ↓
    보정 정보를 이용한 로봇 좌표 변환
            ↓
    두 로봇팔 조작

상의와 하의는 공통 Segmentation 모델을 사용하지만, 의류의 구조와 조작 방식이 다르기 때문에 Pose 모델과 이후 상태 판단 및 동작 계획은 각각 별도로 구성했습니다.

### 상의 자동 조작 흐름

상의의 경우 의류 인식 이후 별도로 학습한 동작 결정 모델을 이용하여 다음 Action을 판단합니다.

    현재 의류 영상
            +
    Segmentation / Pose / 주름 / 위치 기반 상태값
            ↓
    상의 Action Decision Model
            ↓
    다음 Action 결정
            ↓
    동작 계획 생성
            ↓
    두 로봇팔 조작
            ↓
    새 영상 재관찰
            ↓
    다음 Action 판단 / FINISH

동작 결정 모델은 다음에 어떤 조작이 필요한지를 선택하며, 실제 파지 위치와 로봇 이동 경로는 각 Action Runtime에서 계산합니다.

### 하의 자동 조작 흐름

하의 Runtime은 바구니에서 의류를 가져오는 `BASKET_GRASP`부터 시작하여, 의류의 초기 위치를 보정하는 `POSITION_ADJUST`를 1회 수행한 뒤 현재 상태를 자동으로 분석합니다.

    X 입력
            ↓
    BASKET_GRASP
            ↓
    POSITION_ADJUST
            ↓
    새 영상 획득
            ↓
    Segmentation + Pose 추론
            ↓
    형태 / 주름 / 접힘 / 정렬 상태 분석
            ↓
    현재 하의 상태 판단
            ↓
    다음 Action 자동 결정
            ↓
    고정 동작 계획(Frozen Plan) 생성
            ↓
    두 로봇팔 조작
            ↓
    새 영상 재관찰
            ↓
    상태 재평가
            ↓
    다음 Action 판단 / FINISH

현재 하의 Runtime에서 사용하는 주요 Action은 다음과 같습니다.

- `BASKET_GRASP`
- `POSITION_ADJUST`
- `OUTER_PULL`
- `PRESS_SWEEP`
- `WAIST_PULL_LAYDOWN`
- `ALIGN`
- `FINISH`
- `REJUDGE`

`BASKET_GRASP`는 바구니에서 의류를 파지하여 폴딩보드 위로 가져오는 초기 동작이며, `POSITION_ADJUST`는 이후 자동 정리를 시작하기 전에 의류의 초기 위치를 보정하는 동작입니다.

`REJUDGE`는 실제 로봇 조작을 수행하는 Action이 아니라, 새로운 카메라 영상을 획득하여 현재 의류 상태와 다음 Action을 다시 판단하는 제어 Action입니다.

한 번의 카메라 관찰에서 파지점, 목표점 및 이동 경로가 계산되면 해당 결과를 **Frozen Plan**으로 고정합니다.

각 로봇 동작이 끝난 뒤에는 새로운 카메라 영상을 획득하여 변화된 의류 상태를 다시 분석하고 다음 Action을 결정합니다.

---

## 7. Runtime 연동

### 상의

Runtime 실행 파일:

    SW/Jetson/preprocessing/upper/run_upper.py

Segmentation 모델:

    SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine

상의 Pose 모델:

    SW/Jetson/models/pose/upper/tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

상의 Action Decision Model:

    top_board_state_v2_fp32.engine
    state_normalization.npz

상의 Runtime은 Segmentation 및 Pose 결과를 이용하여 현재 의류 상태를 분석하고, 커스텀 학습 모델을 통해 다음 조작 동작을 판단합니다.

모델의 판단 결과는 기존 규칙 기반 상태 판단 및 안전 검사 로직과 함께 사용됩니다.

동작 결정 이후 실제 파지점과 이동 경로는 각 Action의 기존 조작 계획 및 안전 검사 로직을 이용하여 계산합니다.

---

### 하의

Runtime 실행 파일:

    SW/Jetson/preprocessing/lower/run_lower.py

Segmentation 모델:

    SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine

하의 Pose 모델:

    SW/Jetson/models/pose/lower/bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine

`run_lower.py`는 GitHub Repository 내부 경로를 기준으로 하의 Runtime에 필요한 모델과 카메라·로봇 보정 파일의 경로를 전달합니다.

현재 하의 Runtime은 Segmentation 및 Pose 결과와 의류의 형태, 주름, 접힘 및 정렬 상태를 함께 분석하여 현재 상태에 필요한 다음 Action을 결정합니다.

주요 Action은 다음과 같습니다.

- `BASKET_GRASP`
- `POSITION_ADJUST`
- `OUTER_PULL`
- `PRESS_SWEEP`
- `WAIST_PULL_LAYDOWN`
- `ALIGN`
- `FINISH`
- `REJUDGE`

`REJUDGE`는 로봇을 직접 움직이는 동작이 아니라, 새로운 카메라 영상을 획득하여 현재 의류 상태와 다음 Action을 다시 판단하기 위한 제어 Action입니다.

한 번의 카메라 관찰에서 생성한 파지점, 목표점 및 이동 경로는 고정 동작 계획(Frozen Plan)으로 유지한 뒤 실제 로봇 동작에 사용합니다.

각 동작이 끝난 뒤에는 새로운 카메라 영상을 획득하고 변화된 의류 상태를 다시 분석하여 다음 Action을 결정합니다.

이를 통해 하의 Runtime은 **인식 → 상태 판단 → Action 결정 → 로봇 조작 → 재관찰 → 상태 재평가**가 반복되는 구조로 동작합니다.

---

## 8. 검증 환경

현재 TensorRT Engine을 사용하는 Jetson Runtime의 개발 및 검증 환경은 다음과 같습니다.

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
