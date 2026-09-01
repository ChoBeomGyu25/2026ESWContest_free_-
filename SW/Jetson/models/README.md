# Models

이 디렉터리는 자동 의류 정리 로봇 시스템 **「접신」**의 Jetson Runtime에서 사용하는 AI 추론 모델을 관리합니다.

의류 영역을 검출하기 위한 공용 Segmentation Model과 상의 및 하의의 주요 특징점을 검출하기 위한 Pose Estimation Model을 TensorRT Engine 형식으로 저장하여 NVIDIA Jetson Orin Nano에서 실시간 추론에 사용합니다.

현재 제출본에서는 다음 세 종류의 TensorRT Engine을 사용합니다.

- Garment Segmentation Model
- Upper-Garment Pose Model
- Lower-Garment Pose Model

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

상의와 하의는 동일한 Garment Segmentation Model을 공유하며, 의류 구조의 차이를 반영하기 위해 Pose Model은 각각 별도로 사용합니다.

---

## 2. Segmentation Model

파일:

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

카메라 영상에서 의류가 차지하는 영역을 Pixel 단위의 Mask로 검출하는 TensorRT Segmentation Model입니다.

Segmentation 결과는 다음 정보 계산에 사용됩니다.

- 의류 전체 영역 검출
- Garment Mask 생성
- Garment Center 계산
- 외곽 Contour 분석
- Bounding Geometry 계산
- 파지 가능한 내부 영역 계산
- 의류 정렬 상태 분석
- Pose 결과와의 기하 관계 분석
- Wrinkle / Fold 분석을 위한 유효 의류 영역 생성

검출된 Mask는 단순한 의류 존재 여부 판단뿐만 아니라 실제 Robot Grasp Point 계산, Geometry 분석 및 Manipulation Planning에도 사용됩니다.

본 Segmentation Model은 상의와 하의 Runtime에서 공통으로 사용합니다.

---

## 3. Upper Pose Model

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
- Dual-Arm 조작을 위한 기준점 생성

상의 Runtime에서는 Segmentation 결과와 Pose Keypoint를 결합하여 의류의 현재 배치 상태를 분석하고 실제 Dual RoArm M2-S가 파지할 위치를 계산합니다.

Repository-Relative Runtime Entry:

    SW/Jetson/preprocessing/upper/run_upper.py

Dependency Path 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

---

## 4. Lower Pose Model

파일:

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_beige_finetune_v2_best.engine

하의 의류의 주요 Landmark와 구조를 추론하기 위한 Pose Estimation TensorRT Model입니다.

하의 Pose 결과는 다음 분석에 사용됩니다.

- Waistband 구조 분석
- Crotch 위치 및 Concavity 분석
- Leg 구조 분석
- Hem 영역 판단
- 하의 방향 추정
- Garment Axis 분석
- Mask Geometry와의 결합
- Grasp Candidate 생성
- Alignment Planning
- Waist Pull / Laydown Planning
- Finish State 평가

하의 Runtime에서는 Pose 결과를 Segmentation Mask 및 Geometry 분석 결과와 결합하여 하의의 현재 형상과 조작 상태를 판단합니다.

주요 Perception Module:

    SW/Jetson/preprocessing/lower/dual/
    ├── step_e49_bottom_perception.py
    ├── step_e62_bottom_perception.py
    └── step_d25_v2.py

Repository-Relative Runtime Entry:

    SW/Jetson/preprocessing/lower/run_lower.py

Dependency Path 확인:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

현재 제출본 검증 기준:

    PASS=19 FAIL=0 TOTAL=19

---

## 5. TensorRT Engine

본 프로젝트는 NVIDIA Jetson Orin Nano에서 AI Model의 추론 속도를 높이기 위해 TensorRT Engine 형식을 사용합니다.

TensorRT Engine은 NVIDIA GPU 환경에 최적화된 Inference Runtime에서 실행되며, 생성 환경의 영향을 받을 수 있습니다.

특히 다음 요소가 달라질 경우 재검증이 필요할 수 있습니다.

- NVIDIA GPU Architecture
- JetPack 환경
- TensorRT Version
- CUDA Runtime
- Model Export 설정
- Precision 설정

따라서 제출본의 `.engine` 파일을 임의로 다른 환경에서 다시 생성하거나 동일한 파일명으로 교체하지 않는 것을 권장합니다.

---

## 6. 모델 사용 흐름

전체적인 의류 인식 과정은 다음과 같습니다.

    ELP OV2710 Camera
            ↓
    Camera Calibration / Undistortion
            ↓
    Garment Segmentation
            ↓
    Garment Mask
            ↓
    Upper 또는 Lower Pose Estimation
            ↓
    Mask + Pose + Geometry 분석
            ↓
    Landmark / Grasp Candidate 계산
            ↓
    Calibration 기반 Robot Workspace 좌표 변환
            ↓
    Dual RoArm M2-S Manipulation

상의와 하의 모두 Segmentation Model을 사용하지만 Pose Model과 후속 Geometry 및 Manipulation Logic은 각 의류 구조에 맞게 별도로 구성됩니다.

---

## 7. Runtime 연동

### 상의

Wrapper:

    SW/Jetson/preprocessing/upper/run_upper.py

Segmentation Model:

    SW/Jetson/models/segmentation/kfashion_yolo26s_seg3_e100_best.engine

Upper Pose Model:

    SW/Jetson/models/pose/upper/tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

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

## 8. 모델 무결성 검증

제출본에서는 실제 개발 및 Robot Runtime 검증 과정에서 사용한 TensorRT Engine과 GitHub 로컬 제출본이 동일한지 SHA-256 Hash를 이용하여 확인했습니다.

### Segmentation Engine

    kfashion_yolo26s_seg3_e100_best.engine

SHA-256:

    ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725

### Upper Pose Engine

    tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

SHA-256:

    8a5a737f1c019ca87b1889ed187553dc6d3769b1fdc6a77ccf35f6d873c8607c

### Lower Pose Engine

    bottom_pose8_beige_finetune_v2_best.engine

SHA-256:

    5bc3bc60fd545b3c62bbef8c8d41ac4ac372c6d169bc18da01d283fa82f3cbe8

검증된 Lower Pose Engine 크기:

    46,579,644 bytes

---

## 9. 제출 시 주의사항

본 디렉터리의 `.engine` 파일은 실제 Runtime Dependency입니다.

따라서 다음 작업을 임의로 수행하지 않는 것을 권장합니다.

- `.engine` 파일을 `.gitignore`에 추가
- 동일한 이름의 다른 Engine으로 교체
- 다른 Jetson / TensorRT 환경에서 생성한 Engine으로 무검증 교체
- Upper / Lower Pose Model 위치 변경
- Model 파일명 임의 변경
- Wrapper 수정 없이 Model 경로 변경

상의와 하의 Pose Model은 서로 다른 의류 구조에 맞게 구성되어 있으므로 서로 교체해서 사용할 수 없습니다.

---

## 10. 검증 환경

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

---

## 11. 요약

본 디렉터리는 **「접신」**의 Jetson AI Inference에 필요한 다음 Model을 관리합니다.

1. **Garment Segmentation**
   - 상의 / 하의 공용 의류 Mask 검출

2. **Upper Pose Estimation**
   - 상의 Landmark 및 Grasp Geometry 분석

3. **Lower Pose Estimation**
   - 하의 Waist, Crotch, Leg, Hem 및 Manipulation Geometry 분석

각 TensorRT Engine은 실제 Jetson Orin Nano Runtime에서 사용한 파일을 기준으로 구성되며 SHA-256을 이용하여 제출본의 무결성을 검증합니다.
