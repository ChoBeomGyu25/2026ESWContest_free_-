# Jetson Software

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서 NVIDIA Jetson Orin Nano를 기반으로 실행되는 Vision AI, Garment State Analysis, Manipulation Planning 및 Dual RoArm M2-S 제어 Software를 관리합니다.

Jetson은 상부 ELP OV2710 Camera로부터 영상을 입력받아 의류의 위치와 형상을 인식하고, Camera Pixel Coordinate를 실제 Folding Board 및 Robot Workspace Coordinate로 변환한 뒤 상의와 하의의 상태에 맞는 Manipulation Runtime을 실행하는 핵심 연산 장치입니다.

현재 Repository에서는 **이미 Robot에서 검증된 Runtime**과 **향후 학습 기반으로 추가할 자율 판단 Policy**를 구분하여 관리합니다.

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

Jetson Software의 주요 기능은 다음과 같습니다.

1. ELP OV2710 Camera 영상 획득
2. Camera Calibration 및 Lens Undistortion
3. Garment Segmentation
4. Upper / Lower Pose Estimation
5. Garment Mask 및 Contour 분석
6. Keypoint / Landmark 분석
7. 의류 방향 및 위치 분석
8. Fold / Wrinkle 및 Garment Geometry 분석
9. Camera Pixel Coordinate를 Folding Board / Robot Coordinate로 변환
10. Robot Grasp Point 계산
11. Manipulation Planning
12. Dual RoArm M2-S Robot Control
13. 조작 후 새로운 Garment State 관찰
14. 향후 학습 기반 Action Decision
15. 향후 Folding-ready 종료조건 판단

---

# 3. Preprocessing

`preprocessing/`은 상의와 하의의 실제 Vision Perception 및 Manipulation Runtime을 관리합니다.

    SW/Jetson/preprocessing/
    ├── upper/
    └── lower/

상의와 하의는 구조와 조작 방법이 서로 다르기 때문에 각각 검증된 Runtime 구조를 유지합니다.

단순한 Source 중복 제거보다 실제 Robot에서 검증된 Dependency와 Runtime 재현성을 우선합니다.

---

# 4. 현재 Upper Runtime

현재 상의 Main Runtime은 GitHub Repository에 포함되어 있습니다.

경로:

    SW/Jetson/preprocessing/upper/

Repository-Relative Launcher:

    SW/Jetson/preprocessing/upper/run_upper.py

현재 상의 Main Pipeline은 다음 과정까지 수행합니다.

    Basket Garment Grasp
            ↓
    Folding Board 위 이동
            ↓
    Garment Laydown
            ↓
    Garment Reposition
            ↓
    Segmentation + Upper Pose
            ↓
    Final Grasp Point Selection
            ↓
    Dual-Arm Grasp
            ↓
    Aerial Lift / Alignment
            ↓
    Laydown
            ↓
    Standby Return

Dependency 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

실제 Robot Sequence:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

`--physical-auto`는 실제 Dual RoArm M2-S를 동작시키므로 Robot 및 Workspace Safety를 확인한 뒤 실행해야 합니다.

---

# 5. Upper 향후 학습 기반 자율화

현재 GitHub에 올라간 Upper Main Runtime은 상의의 초기 배치, 인식, Dual-Arm Grasp, 공중 정렬 및 Laydown까지 수행합니다.

향후에는 이 Main Runtime **이후 단계에 학습 Model 기반의 Garment State Decision Module을 연결**할 예정입니다.

이 후속 Module은 Laydown 후 새로운 Camera Frame을 관찰하여 다음과 같은 조작의 필요 여부를 스스로 판단하는 것을 목표로 합니다.

- Wrinkle Unfold
- Fold 제거
- Garment Position Correction
- 추가 Alignment
- 추가 Pull / Reposition
- Garment Center 보정
- 추가 Manipulation 필요 여부
- Folding-ready 종료조건

목표 구조:

    Current Upper Main Runtime
            ↓
    Laydown
            ↓
    New Camera Observation
            ↓
    Learned Garment-State Model
            ↓
    Next Manipulation Decision
            ↓
    Wrinkle Unfold / Position Adjust / Alignment
            ↓
    Re-observation
            ↓
    Additional Action Decision
            ↓
    Folding-ready 판단

최종적으로 상의 System은 사람이 추가 조작 여부를 지정하지 않아도 학습 기반 Policy가 현재 의류 상태를 분석하고 필요한 조작을 반복한 뒤,

**“현재 상의 상태가 충분히 펴지고 정렬되어 Folding Board로 접는 단계에 진입할 수 있다”**

는 종료조건까지 자동으로 판단하는 것을 목표로 합니다.

현재 이 후속 학습 기반 Module은 개발 단계이며, 검증 완료 후 기존 Upper Main Runtime 뒤에 연결할 예정입니다.

---

# 6. 현재 Lower Runtime

현재 하의 Runtime 역시 GitHub Repository에 포함되어 있습니다.

경로:

    SW/Jetson/preprocessing/lower/

Repository-Relative Launcher:

    SW/Jetson/preprocessing/lower/run_lower.py

Final Semantic Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-16.py

Integrated Base Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/main-33.py

현재 하의는 완전 자동 Action Selection 단계가 아니라 **Human-in-the-loop Semi-Automatic Manipulation System**으로 동작합니다.

Camera와 AI Model이 현재 하의 상태를 인식하고 각 Action에 필요한 Manipulation Plan을 생성하지만, 현재 단계에서는 사용자가 Semantic Action Key를 선택합니다.

현재 Semantic Action:

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

기본 흐름:

    Camera Observation
            ↓
    Garment Perception
            ↓
    Garment State Analysis
            ↓
    사용자 Semantic Action 선택
            ↓
    Automatic Planning
            ↓
    Frozen Plan
            ↓
    ENTER 승인
            ↓
    Robot Execution
            ↓
    Result Review

한 번 생성된 Frozen Plan은 `ENTER` 실행 시 다시 재추론하지 않고 승인된 Plan을 그대로 사용합니다.

---

# 7. Lower VLA Data Collection

현재 하의에서 사용자가 Semantic Action을 직접 선택하는 가장 중요한 이유는 **VLA(Vision-Language-Action) 기반 자동 Action Policy를 학습하기 위한 Data를 수집하기 위해서입니다.**

현재 Data Collection에서는 다음 관계를 축적합니다.

    Garment State
        ↓
    Semantic Action
        ↓
    Robot Execution
        ↓
    Action Result
        ↓
    Next Garment State

즉 현재 사람이 입력하는 `1 ~ 8` Action은 단순한 수동 조작 Interface가 아니라, 향후 VLA Model이 학습할 **Garment State → Action Decision** 관계를 생성하는 역할을 합니다.

현재 Runtime에서는 다음과 같은 요소를 함께 활용하여 하의 상태를 분석합니다.

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

# 8. Lower 향후 VLA 기반 자동화

충분한 VLA Data를 수집하고 학습을 완료한 뒤에는 현재 사람이 수행하는 Semantic Action Selection을 VLA 기반 Model로 대체할 예정입니다.

현재:

    Perception
        ↓
    사용자 Key 입력
        ↓
    Action Planning
        ↓
    Robot Execution

향후:

    Perception
        ↓
    VLA Garment-State Understanding
        ↓
    Semantic Action 자동 선택
        ↓
    Manipulation Planning
        ↓
    Robot Execution
        ↓
    New Observation
        ↓
    Next Action 자동 선택

현재 사용자가 입력하는 `1 ~ 8` Semantic Action Key를 VLA Model의 Action Output으로 교체하는 것이 핵심 목표입니다.

---

# 9. Lower 종료조건 자동 판단 목표

하의의 최종 목표는 단순한 Semantic Action 자동 선택에서 끝나지 않습니다.

VLA 및 Garment-State Evaluation을 통해 다음 항목을 종합적으로 판단하고, 추가 조작이 필요한지 또는 Folding 단계로 이동할 수 있는지 결정하는 구조를 목표로 합니다.

- Garment가 충분히 펼쳐졌는가
- 큰 Fold가 제거되었는가
- Waist 구조가 정상적인가
- Crotch 및 Leg 구조가 정상적으로 배치되었는가
- 두 Hem 영역이 적절한가
- Garment Center가 적절한가
- Folding Board 기준 방향이 충분히 정렬되었는가
- 추가 Robot Manipulation이 필요한가
- Folding-ready 상태인가

최종 Lower Loop:

    Observation
        ↓
    Garment State
        ↓
    VLA Action Decision
        ↓
    Manipulation
        ↓
    Re-observation
        ↓
    Additional Action?
       /           \
     YES           NO
      ↓             ↓
    Repeat      Folding-ready
                     ↓
                Folding Board

---

# 10. Upper / Lower 최종 통합 방향

현재 Upper와 Lower의 구현 단계는 다르지만 최종적으로 같은 Closed-loop Manipulation Architecture를 지향합니다.

    Garment Input
        ↓
    Garment Perception
        ↓
    State Understanding
        ↓
    Learned Action Policy
        ↓
    Dual RoArm Manipulation
        ↓
    Re-observation
        ↓
    State Re-evaluation
        ↓
    Additional Action / Termination Decision
        ↓
    Folding-ready
        ↓
    Folding Board

최종 목표는 의류의 초기 배치와 구김 상태가 매번 달라도 AI가 현재 상태를 반복 관찰하면서 적절한 Manipulation을 선택하고, **Folding Board가 동작해도 되는 종료 상태까지 스스로 판단하는 자동 의류 정리 Pipeline**입니다.

---

# 11. Models

TensorRT 기반 AI Model은 다음 Directory에서 관리합니다.

    SW/Jetson/models/

현재 Runtime Model:

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

현재 Repository에는 실제 Runtime에서 사용하는 Segmentation 및 Pose TensorRT Engine을 포함합니다.

향후 Upper Learned Manipulation Policy 및 Lower VLA Policy에서 사용할 학습 Model은 개발과 검증이 완료된 후 추가할 예정입니다.

자세한 내용:

    SW/Jetson/models/README.md

---

# 12. Common

`common/`은 Vision Coordinate와 실제 Folding Board / Robot Workspace를 연결하기 위한 Camera 및 Calibration Resource를 관리합니다.

    SW/Jetson/common/
    ├── camera/
    └── calibration/

주요 Resource:

- ELP OV2710 Camera Undistortion
- Camera Intrinsic Calibration
- Dual RoArm / Folding Board Configuration
- Basket ARM2 Affine Calibration
- Folding Board Homography

---

## Homography 주의사항

Upper/Common Runtime과 Lower Runtime에는 동일한 이름의 Homography 파일이 존재하지만 두 파일은 서로 다른 Runtime Geometry 요구사항을 가집니다.

Common / Upper:

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

Lower-specific:

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

Lower Version은 Raw / Corrected Frame Geometry를 구분하기 위해 `H`, `raw_H`, `camera_geometry`, `schema_version` 정보를 사용합니다.

따라서 두 Homography는 서로 덮어쓰거나 임의로 하나로 통합하면 안 됩니다.

자세한 내용:

    SW/Jetson/common/README.md

---

# 13. Policy

`policy/`는 Garment State와 Manipulation Action 사이의 상위 Decision Layer를 설명합니다.

현재 상태:

### Upper

- 현재 Main Runtime의 Robot Manipulation Sequence는 구현 및 GitHub 제출 완료
- 일부 판단 Logic은 기존 검증된 Runtime 내부에 포함
- 향후 학습 기반 Upper Garment-State Policy 추가 예정
- Wrinkle / Position / Alignment 보정과 Folding-ready 종료조건 판단 자동화 목표

### Lower

- 현재 Human-in-the-loop Semantic Action Selection
- 현재 VLA Data Collection 진행
- 향후 VLA Model이 Action Selection을 자동 수행
- Manipulation 반복과 Folding-ready 종료조건 판단까지 자동화 목표

---

# 14. Runtime Architecture

「접신」의 실제 Runtime은 Perception, Action Decision, Robot Execution 및 Folding 단계의 흐름으로 구성됩니다.

현재 실제 검증된 Runtime Source는 다음 Directory에 위치합니다.

Upper:

    SW/Jetson/preprocessing/upper/

Lower:

    SW/Jetson/preprocessing/lower/

검증된 기존 Source Dependency와 Dynamic Source Loading 구조를 유지하기 위해 Runtime Source 자체를 `runtime/`로 임의 이동하지 않습니다.

`runtime/` Directory는 전체 실행 Architecture와 상·하의 Runtime 관계를 설명하는 계층으로 사용합니다.

---

# 15. Lower GitHub Fresh-Clone 검증

하의 Runtime은 GitHub `main`에 업로드한 뒤 완전히 새로운 Directory에 Repository를 Fresh Clone하여 검증했습니다.

Fresh Clone에서 다음 검사가 완료되었습니다.

### Dependency

    PASS=19
    FAIL=0

### Python Compile

    PASS=13
    FAIL=0

### Static Dependency

    PASS=36
    FAIL=0

또한 Fresh Clone Repository 내부의 파일만 이용하여 다음 Runtime Initialization을 확인했습니다.

- Lower Source Dynamic Loading
- E49 / E62 / D25 연결
- Lower-specific Homography Loading
- ELP OV2710 Camera Open
- Camera Control 적용
- Camera Undistortion Calibration
- Segmentation TensorRT Engine Loading
- Bottom Pose TensorRT Engine Loading
- TensorRT Execution Context Warm-up
- Bottom VLA Operator Runtime 진입

이를 통해 기존 개발 Directory의 Source에 의존하지 않고 GitHub Repository 내부의 Source, Model 및 Calibration만으로 Lower Runtime을 초기화할 수 있음을 확인했습니다.

Fresh Clone에서의 실제 Physical Robot Motion Test는 Repository Dependency / Initialization 검증과 별도의 Hardware Validation 단계로 관리합니다.

---

## Clean Docker GitHub-only 추가 검증

Fresh Clone 검증 이후에는 기존 개발 Directory의 숨은 Dependency 가능성을 추가로 배제하기 위해 별도의 Clean Docker Container에서도 Lower Runtime을 검증했습니다.

검증 환경은 실제 Runtime과 동일한 Docker Image인

    roarm_dual_working_20260814:latest

를 사용했으며 다음과 같이 구성했습니다.

- NVIDIA Container Runtime 사용
- `/workspace/project_train`을 File 수 0개의 빈 Read-only Directory로 대체
- 기존 Project Source Mount 제거
- `PYTHONPATH`에 기존 Project Directory 없음
- `/dev/roarm_1` 미전달
- `/dev/roarm_2` 미전달
- `/dev/ttyACM0` 미전달
- `/dev/video0`만 전달
- GitHub Repository를 Container 내부 `/tmp`에 새롭게 Clone

해당 환경에서 다음 단계까지 정상적으로 수행되는 것을 확인했습니다.

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
    Bottom VLA Operator Runtime PASS

실제 Source, Model 및 Calibration은 모두 Fresh Clone Repository의

    /tmp/jeopsin_github_clean/SW/Jetson/...

경로에서 Load되었습니다.

따라서 Lower Runtime Initialization에 필요한 Source, Model 및 Calibration Dependency가 기존 `/workspace/project_train` 개발 Directory 없이 GitHub Repository 내부에서 완결됨을 추가 확인했습니다.

Robot Device는 Clean Container에 전달하지 않았으므로 이 검증은 Physical Motion Test가 아니라 Repository Runtime Reproducibility 및 Initialization Test입니다.

# 16. 실행 환경

현재 Jetson Runtime 검증 환경:

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

Robot Device:

    ARM1: /dev/roarm_1
    ARM2: /dev/roarm_2

Camera Device:

    /dev/video0

---

# 17. 실행 명령

## Upper Dependency 검사

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

## Upper Physical Runtime

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

---

## Lower Dependency 검사

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

## Lower Dry-run

    python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run

`--dry-run`은 실제 Camera와 TensorRT Runtime을 초기화하지만 Physical Robot Manipulation을 위한 실행 Mode는 아닙니다.

## Lower Physical Runtime

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

`--physical`은 실제 Dual RoArm M2-S Motion을 활성화하므로 Robot과 Workspace의 Safety를 확인한 후 실행해야 합니다.

---

# 18. 개발 원칙

현재 Repository는 실제 Robot에서 검증된 Runtime의 재현성을 우선합니다.

따라서 다음 작업은 전체 Runtime 재검증 없이 수행하지 않는 것을 권장합니다.

- 검증된 Source File 이름 변경
- Dynamic Source Loading 구조 변경
- Source Directory 임의 재구성
- 핵심 Python Source 자동 Formatting
- 단순 중복 제거를 위한 검증된 Module 통합
- Upper / Lower Homography 임의 통합
- TensorRT Engine 임의 교체

현재 구현된 Runtime과 향후 개발할 Learned Policy를 구분함으로써 현재 Repository의 재현성을 유지하면서 단계적으로 자율화 기능을 확장합니다.

---

# 19. 최종 목표

Jetson Software의 최종 목표는 다음 Closed-loop Automatic Garment Manipulation을 구현하는 것입니다.

    Camera
      ↓
    Perception
      ↓
    Garment State Understanding
      ↓
    Learned Action Decision
      ↓
    Dual RoArm Manipulation
      ↓
    Re-observation
      ↓
    Additional Action / Termination Decision
      ↓
    Folding-ready
      ↓
    Folding Board

현재 Upper와 Lower는 서로 다른 개발 단계에 있지만, 최종적으로는 **의류 상태 인식 → Manipulation Decision → Robot Execution → 재관찰 → 종료조건 판단**을 반복하여 사람이 각 조작 단계에 개입하지 않아도 Folding 가능한 상태까지 자동으로 만드는 것을 목표로 합니다.
