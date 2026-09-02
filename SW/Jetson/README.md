# Jetson Software

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서 NVIDIA Jetson Orin Nano를 기반으로 실행되는 **AI 기반 컴퓨터 비전, 의류 상태 분석, 조작 계획 및 Dual Robotic Arms 소프트웨어**를 포함합니다.

Jetson은 상부 ELP OV2710 카메라 영상을 입력받아 의류의 위치와 형상을 인식하고, 카메라 픽셀 좌표를 실제 Folding Board 및 로봇 작업공간 좌표로 변환한 뒤 상의와 하의 상태에 맞는 조작 동작을 수행하는 핵심 연산 장치입니다.

현재 저장소에서는 실제 로봇에서 검증된 실행 코드와 학습 기반 동작 판단 모델을 함께 관리합니다.

---

# 1. 디렉터리 구성

    SW/Jetson/
    ├── README.md
    │
    ├── preprocessing/
    │   ├── README.md
    │   ├── upper/
    │   │   ├── README.md
    │   │   ├── run_upper.py
    │   │   └── ...
    │   │
    │   └── lower/
    │       ├── README.md
    │       ├── run_lower.py
    │       ├── dual/
    │       │   ├── step_e49_bottom_perception.py
    │       │   ├── step_e62_bottom_perception.py
    │       │   ├── step_d25_v2.py
    │       │   └── undistort/
    │       │       ├── bottom_vla-16.py
    │       │       ├── main-33.py
    │       │       ├── 50-1.py
    │       │       ├── 54-3.py
    │       │       ├── 55-5.py
    │       │       ├── 58-3.py
    │       │       ├── 60-13.py
    │       │       ├── align-11.py
    │       │       └── ...
    │       └── outputs/
    │
    ├── common/
    │   ├── camera/
    │   └── calibration/
    │
    ├── models/
    │   ├── segmentation/
    │   └── pose/
    │       ├── upper/
    │       └── lower/
    │
    ├── policy/
    │
    └── runtime/

---

# 2. Jetson의 역할

Jetson 소프트웨어의 주요 기능은 다음과 같습니다.

1. ELP OV2710 카메라 영상 획득
2. 카메라 보정 및 렌즈 왜곡 보정
3. YOLO 기반 의류 Segmentation
4. 상의 / 하의 Pose 및 특징점 추론
5. 의류 Mask 및 Contour 분석
6. Keypoint / Landmark 분석
7. 의류 방향 및 위치 분석
8. 접힘 / 주름 및 의류 형상 분석
9. 카메라 픽셀 좌표를 Folding Board / 로봇 좌표로 변환
10. 로봇 파지점 계산
11. 조작 계획 생성
12. 듀얼 로봇팔 제어
13. 조작 후 새로운 의류 상태 재관찰
14. 학습 모델 기반 다음 조작 동작 결정
15. Folding-ready 종료조건 판단
---

# 3. 전처리 및 실행 코드 (`preprocessing/`)

`preprocessing/`은 상의와 하의의 실제 의류 인식 및 로봇 조작 실행 코드를 관리합니다.

    SW/Jetson/preprocessing/
    ├── upper/
    └── lower/

상의와 하의는 구조와 조작 방법이 서로 다르기 때문에 각각 실제 로봇에서 검증된 실행 구조를 유지합니다.

단순한 소스 통합이나 중복 제거보다 **실제 로봇에서 검증된 의존성과 실행 재현성**을 우선합니다.
---

# 4. 현재 상의 실행 코드

현재 상의 메인 실행 코드는 GitHub 저장소에 포함되어 있습니다.

경로:

    SW/Jetson/preprocessing/upper/

실행 파일:

    SW/Jetson/preprocessing/upper/run_upper.py

현재 상의 시스템은 초기 의류 배치부터 **학습 모델 기반 동작 판단, 반복 조작 및 FINISH 판단까지 자동으로 수행하는 구조**로 구성되어 있습니다.

전체 흐름:

    Basket Garment Grasp
            ↓
    Folding Board 위 이동
            ↓
    Garment Laydown
            ↓
    YOLO Segmentation + YOLO Pose
            ↓
    의류 상태 분석
            ↓
    커스텀 동작 결정 모델
            ↓
    안전한 조작 계획 생성
            ↓
    듀얼 로봇팔 동작 수행
            ↓
    Standby 복귀
            ↓
    새로운 의류 상태 재관찰
            ↓
    다음 동작 자동 판단
            ↓
    반복 조작 / FINISH

의존성 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

실제 로봇 자동 실행:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

`--physical-auto`는 실제 듀얼 로봇팔을 사용하는 상의 자동 정리 실행 옵션입니다.
---

# 5. 상의 학습 기반 자동 조작

상의에는 **현재 의류 상태를 보고 다음 조작 동작을 결정하는 커스텀 학습 모델**이 적용되어 있습니다.

의류 영상과 Segmentation, Pose, 주름 및 위치 분석 결과를 이용하여 현재 상태를 표현하고, **Board+State v2 커스텀 모델**이 다음 동작을 우선 판단합니다. Jetson에서는 TensorRT 엔진으로 추론합니다.

현재 판단 구조:

    Camera Observation
            ↓
    Segmentation / Pose / State Analysis
            ↓
    Board+State v2 Model
            ↓
    다음 조작 동작 후보 결정
            ↓
    신뢰도 및 적용 조건 확인
       /                    \
    통과                     미통과
     ↓                        ↓
    모델 판단 사용        규칙 기반 상태 판단 로직 사용
       \                    /
        ↓
    최종 조작 계획 및 안전 검사
            ↓
    로봇 실행
            ↓
    Re-observation
            ↓
    다음 동작 자동 판단

현재 커스텀 모델은 7개 동작 클래스를 학습했으며, 제출용 실행 코드에서는 신뢰도와 margin 조건을 만족한 `CENTER`, `SPREAD`, `ROTATE`, `FINISH` 판단을 우선 직접 사용합니다. 그 외 경우에는 규칙 기반 상태 판단 로직으로 넘어갑니다.

즉, 현재 상의 코드는 **커스텀 모델을 우선 사용하여 동작을 판단하고, 모델 판단을 직접 채택하기 어려운 경우 규칙 기반 상태 판단 로직을 보조 경로로 사용**합니다.

실제 파지점과 이동 경로는 기존 검증된 조작 계획 및 안전 검사 로직을 통해 최종 결정됩니다.

조작이 끝나면 로봇팔이 대기 위치로 복귀한 뒤 새로운 영상을 다시 관찰하고 필요한 동작을 반복합니다. `FINISH`가 선택되면 해당 의류의 자동 조작 루프를 종료합니다.
---

# 6. 현재 하의 실행 코드

현재 하의 실행 코드 역시 GitHub 저장소에 포함되어 있습니다.

경로:

    SW/Jetson/preprocessing/lower/

실행 파일:

    SW/Jetson/preprocessing/lower/run_lower.py

하의 주요 코드:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-16.py

통합 기반 코드:

    SW/Jetson/preprocessing/lower/dual/undistort/main-33.py

현재 하의는 완전 자동 동작 선택 단계가 아니라 **사용자 판단 기반 반자동 조작 시스템**으로 동작합니다.

카메라와 AI 모델이 현재 하의 상태를 인식하고 각 동작에 필요한 조작 계획을 생성하며, 현재 단계에서는 사용자가 수행할 동작을 선택합니다.

현재 동작:

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

기본 흐름:

    카메라 관찰
        ↓
    의류 인식
        ↓
    의류 상태 분석
        ↓
    사용자 동작 선택
        ↓
    자동 조작 계획 생성
        ↓
    Frozen Plan
        ↓
    ENTER 승인
        ↓
    로봇 실행
        ↓
    결과 확인

한 번 생성된 Frozen Plan은 `ENTER` 실행 시 다시 추론하지 않고 승인된 계획을 그대로 사용합니다.
---

# 7. 하의 VLA 데이터 수집

현재 하의에서 사용자가 동작을 직접 선택하는 가장 중요한 이유는 **VLA(Vision-Language-Action) 기반 자동 동작 판단 모델을 학습하기 위한 데이터를 수집하기 위해서입니다.**

현재 데이터 수집에서는 다음 관계를 축적합니다.

    의류 상태
        ↓
    선택한 동작
        ↓
    로봇 실행
        ↓
    동작 결과
        ↓
    다음 의류 상태

즉 현재 사람이 입력하는 `1 ~ 8` 동작은 단순한 수동 조작 인터페이스가 아니라, 향후 VLA 모델이 학습할 **의류 상태 → 동작 결정** 관계를 생성하는 역할을 합니다.

현재 하의 상태 분석에는 다음 정보를 함께 사용합니다.

- Garment Segmentation
- Bottom Pose
- Mask Geometry
- Contour
- Waistband
- Crotch
- Leg / Hem
- Fold / Wrinkle
- Alignment State
- Finish State
---

# 8. 하의 VLA 기반 자동화 방향

충분한 VLA 데이터를 수집하고 학습을 완료한 뒤에는 현재 사람이 수행하는 동작 선택을 VLA 기반 모델로 대체하는 것을 목표로 합니다.

현재:

    의류 인식 및 상태 분석
        ↓
    사용자 동작 선택
        ↓
    조작 계획 생성
        ↓
    로봇 실행

자동화 목표:

    의류 인식 및 상태 분석
        ↓
    VLA 기반 동작 자동 선택
        ↓
    조작 계획 생성
        ↓
    로봇 실행
        ↓
    재관찰
        ↓
    다음 동작 자동 선택

현재 사용자가 입력하는 `1 ~ 8` 동작을 VLA 모델의 출력으로 대체하는 것이 핵심 목표입니다.
---

# 9. 하의 종료조건 자동 판단 목표

하의의 최종 목표는 단순한 동작 자동 선택에서 끝나지 않습니다.

VLA 및 의류 상태 평가를 통해 다음 항목을 종합적으로 판단하고, 추가 조작이 필요한지 또는 Folding 단계로 이동할 수 있는지 결정하는 구조를 목표로 합니다.

- 의류가 충분히 펼쳐졌는가
- 큰 접힘이 제거되었는가
- 허리선 구조가 정상적인가
- 가랑이 및 다리 구조가 정상적으로 배치되었는가
- 양쪽 밑단 영역이 적절한가
- 의류 중심이 적절한가
- Folding Board 기준 방향이 충분히 정렬되었는가
- 추가 로봇 조작이 필요한가
- Folding-ready 상태인가

최종 하의 반복 구조:

    의류 관찰
        ↓
    상태 분석
        ↓
    VLA 동작 결정
        ↓
    로봇 조작
        ↓
    재관찰
        ↓
    추가 동작 필요?
       /          \
     YES          NO
      ↓            ↓
    반복       Folding-ready
                    ↓
               Folding Board
---

# 10. 상의 / 하의 최종 통합 방향

상의와 하의는 현재 자동화 단계가 서로 다르지만 최종적으로 같은 **폐루프(Closed-loop) 의류 조작 구조**를 지향합니다.

    Garment Input
        ↓
    의류 인식
        ↓
    의류 상태 분석
        ↓
    동작 판단
        ↓
    두 로봇팔 조작
        ↓
    재관찰
        ↓
    상태 재평가
        ↓
    추가 동작 / 종료 판단
        ↓
    Folding-ready
        ↓
    Folding Board

상의는 현재 **학습 모델 우선 판단 + 규칙 기반 상태 판단 로직**을 이용한 자동 반복 조작 구조를 적용하고 있으며, 하의는 VLA 학습을 위한 데이터 수집 및 자동화 개발을 진행하고 있습니다.
---

# 11. 모델

TensorRT 기반 AI 모델은 다음 디렉터리에서 관리합니다.

    SW/Jetson/models/

현재 의류 인식 모델:

    models/
    ├── segmentation/
    │   └── kfashion_yolo26s_seg3_e100_best.engine
    │
    └── pose/
        ├── upper/
        │   └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine
        │
        └── lower/
            └── bottom_pose8_beige_finetune_v2_best.engine

상의에서는 의류 인식 모델과 별도로 **다음 조작 동작을 판단하기 위한 Board+State v2 커스텀 모델**을 사용합니다.

주요 파일:

    top_board_state_v2_fp32.engine
    state_normalization.npz

- `top_board_state_v2_fp32.engine` : Jetson에서 사용하는 TensorRT 동작 결정 모델
- `state_normalization.npz` : 모델 입력에 사용되는 상태값 정규화 정보

Jetson의 실제 동작 결정 추론에서는 TensorRT 엔진과 `state_normalization.npz`를 사용합니다.

자세한 내용:

    SW/Jetson/models/README.md
---

# 12. 공통 보정 리소스

`common/`은 카메라 좌표와 실제 Folding Board / 로봇 작업공간을 연결하기 위한 카메라 및 보정 리소스를 포함합니다.

    SW/Jetson/common/
    ├── camera/
    └── calibration/

주요 리소스:

- ELP OV2710 카메라 왜곡 보정
- 카메라 내부 파라미터 보정
- Dual Robotic Arms / Folding Board 설정
- Basket ARM2 Affine Calibration
- Folding Board Homography

---

## Homography 주의사항

상의 공통 실행 코드와 하의 실행 코드에는 동일한 이름의 Homography 파일이 존재하지만 서로 다른 좌표계 처리 요구사항을 가집니다.

상의 / 공통:

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

하의 전용:

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

하의 버전은 Raw / Corrected Frame Geometry를 구분하기 위해 `H`, `raw_H`, `camera_geometry`, `schema_version` 정보를 사용합니다.

따라서 두 Homography 파일을 서로 덮어쓰거나 임의로 하나로 통합하면 안 됩니다.

자세한 내용:

    SW/Jetson/common/README.md
---

# 13. 동작 판단 정책

`policy/`는 의류 상태와 로봇 조작 동작 사이의 상위 판단 구조를 포함합니다.

현재 상태:

### 상의

- YOLO Segmentation / Pose 기반 의류 상태 인식
- Board+State v2 커스텀 모델 기반 동작 판단 적용
- 커스텀 모델 판단을 우선 사용하고 필요한 경우 규칙 기반 상태 판단 로직으로 보완
- 기존 검증된 조작 계획과 안전 검사 로직을 통해 실제 로봇 동작 생성
- 동작 후 자동 재관찰 및 다음 동작 판단 반복
- `FINISH` 판단 시 해당 의류 조작 종료

### 하의

- 현재 사용자 판단 기반 동작 선택
- VLA 학습 데이터 수집 진행
- 향후 VLA 모델을 이용한 동작 자동 선택 목표
- 반복 조작과 Folding-ready 종료조건 판단까지 자동화 목표
---

# 14. 실행 구조

「접신」의 실제 실행 구조는 **의류 인식 → 동작 판단 → 로봇 실행 → 재관찰 → 종료 판단**의 흐름으로 구성됩니다.

현재 실제 검증된 소스 코드는 다음 디렉터리에 위치합니다.

Upper:

    SW/Jetson/preprocessing/upper/

Lower:

    SW/Jetson/preprocessing/lower/

검증된 기존 소스 의존성과 Dynamic Source Loading 구조를 유지하기 위해 실행 소스 자체를 `runtime/`로 임의 이동하지 않습니다.

`runtime/` 디렉터리는 전체 실행 구조와 상·하의 실행 관계를 설명하는 계층으로 사용합니다.
---

# 15. 하의 GitHub 새 환경 검증

하의 실행 코드는 GitHub `main`에 업로드한 뒤 완전히 새로운 디렉터리에 저장소를 다시 Clone하여 검증했습니다.

검사 결과:

### 의존성 검사

    PASS=19
    FAIL=0

### Python Compile

    PASS=13
    FAIL=0

### 정적 의존성 검사

    PASS=36
    FAIL=0

또한 새로 Clone한 저장소 내부의 파일만 이용하여 다음 초기화 과정을 확인했습니다.

- Lower Source Dynamic Loading
- E49 / E62 / D25 연결
- 하의 전용 Homography Loading
- ELP OV2710 카메라 연결
- 카메라 설정 적용
- 카메라 왜곡 보정
- Segmentation TensorRT Engine Loading
- Bottom Pose TensorRT Engine Loading
- TensorRT Execution Context Warm-up
- Bottom VLA 실행 코드 진입

이를 통해 기존 개발 디렉터리의 소스에 의존하지 않고 GitHub 저장소 내부의 소스, 모델 및 보정 파일만으로 하의 실행 코드를 초기화할 수 있음을 확인했습니다.

새로 Clone한 환경에서의 실제 로봇 동작 시험은 저장소 의존성 / 초기화 검증과 별도의 하드웨어 검증 단계로 관리합니다.

---

## Clean Docker 추가 검증

Fresh Clone 검증 이후에는 기존 개발 디렉터리의 숨은 의존성 가능성을 추가로 배제하기 위해 별도의 Clean Docker Container에서도 하의 실행 코드를 검증했습니다.

검증 환경은 실제 실행 환경과 동일한 Docker Image인

    roarm_dual_working_20260814:latest

를 사용했으며 다음과 같이 구성했습니다.

- NVIDIA Container Runtime 사용
- `/workspace/project_train`을 파일 수 0개의 빈 Read-only Directory로 대체
- 기존 Project Source Mount 제거
- `PYTHONPATH`에 기존 Project Directory 없음
- `/dev/roarm_1` 미전달
- `/dev/roarm_2` 미전달
- `/dev/ttyACM0` 미전달
- `/dev/video0`만 전달
- GitHub 저장소를 Container 내부 `/tmp`에 새롭게 Clone

해당 환경에서 다음 단계까지 정상 수행되는 것을 확인했습니다.

    GitHub Fresh Clone
        ↓
    Dependency Check 19 / 19 PASS
        ↓
    Lower Homography Validation PASS
        ↓
    Camera Open PASS
        ↓
    Camera Control / Undistortion PASS
        ↓
    Segmentation TensorRT Load PASS
        ↓
    Bottom Pose TensorRT Load PASS
        ↓
    TensorRT Warm-up PASS
        ↓
    Bottom VLA Runtime PASS

실제 소스, 모델 및 보정 파일은 모두 새로 Clone한 저장소의

    /tmp/jeopsin_github_clean/SW/Jetson/...

경로에서 Load되었습니다.

따라서 하의 실행 초기화에 필요한 소스, 모델 및 보정 파일이 기존 `/workspace/project_train` 개발 디렉터리 없이 GitHub 저장소 내부에서 완결됨을 추가로 확인했습니다.

Robot Device는 Clean Container에 전달하지 않았으므로 이 검증은 실제 로봇 동작 시험이 아니라 **저장소 재현성 및 초기화 검증**입니다.

---

# 16. 실행 환경

현재 Jetson 실행 검증 환경:

- Main Processor: NVIDIA Jetson Orin Nano
- Operating System: Ubuntu 22.04.3
- Python: 3.10.12
- TensorRT: 10.7.0
- OpenCV: 4.11.0
- NumPy: 1.26.4
- PyTorch: 2.10.0
- CUDA Runtime: 12.6 (PyTorch)
- Ultralytics: 8.4.45
- XGBoost: 3.2.0
- Docker: 29.7.2
- Robot: Dual RoArm M2-S
- Camera: ELP OV2710
- Camera Resolution: 1280 × 720
- Communication: USB Serial

로봇 장치:

    ARM1: /dev/roarm_1
    ARM2: /dev/roarm_2

카메라 장치:

    /dev/video0

---

# 17. 실행 명령

## 상의 의존성 검사

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

## 상의 실제 로봇 자동 실행

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

---

## 하의 의존성 검사

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

## 하의 Dry-run

    python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run

`--dry-run`은 실제 카메라와 TensorRT 실행 환경을 초기화하지만 실제 로봇 조작 명령은 수행하지 않습니다.

## 하의 실제 로봇 실행

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

`--physical`은 실제 Dual RoArm M2-S 동작을 활성화하므로 로봇과 작업공간의 안전을 확인한 후 실행해야 합니다.

---

# 18. 개발 원칙

현재 저장소는 실제 로봇에서 검증된 실행 코드의 재현성을 우선합니다.

따라서 다음 작업은 전체 실행 코드를 재검증하지 않은 상태에서 수행하지 않는 것을 권장합니다.

- 검증된 소스 파일 이름 변경
- Dynamic Source Loading 구조 변경
- 소스 디렉터리 임의 재구성
- 핵심 Python 소스 자동 Formatting
- 단순 중복 제거를 위한 검증된 Module 통합
- Upper / Lower Homography 임의 통합
- TensorRT Engine 임의 교체

현재 검증된 실행 코드와 학습 기반 판단 모델의 역할을 구분하여 관리함으로써 저장소의 재현성과 로봇 동작의 안전성을 유지합니다.

---

# 19. 최종 목표

Jetson 소프트웨어의 최종 목표는 다음과 같은 **폐루프 자동 의류 조작 시스템**을 구현하는 것입니다.

    Camera
      ↓
    의류 인식
      ↓
    의류 상태 분석
      ↓
    동작 판단
      ↓
    Dual RoArm 조작
      ↓
    재관찰
      ↓
    추가 동작 / 종료 판단
      ↓
    Folding-ready
      ↓
    Folding Board

현재 **상의는 학습 기반 동작 결정 모델과 규칙 기반 상태 판단 로직을 이용하여 의류 상태를 반복 관찰하고 필요한 조작을 자동 수행한 뒤 FINISH까지 판단하는 구조를 구현**했습니다.

하의는 현재 VLA 학습 데이터 수집과 자동화 개발을 진행하고 있으며, 최종적으로 상·하의 모두 사람이 각 조작 단계를 직접 선택하지 않아도 Folding 가능한 상태까지 자동으로 정리하는 것을 목표로 합니다.

