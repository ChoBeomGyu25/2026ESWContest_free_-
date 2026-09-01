# Garment Preprocessing & Manipulation Runtime

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서 사용하는
상의 및 하의의 Vision Perception, Garment State Analysis, Manipulation Planning 및 Robot Runtime을 관리합니다.

상의와 하의는 의류 구조, 주요 Landmark, 조작 방식 및 현재 개발 단계가 서로 다르기 때문에
각각 독립된 Runtime 구조를 유지합니다.

    SW/Jetson/preprocessing/
    ├── upper/
    └── lower/

현재 Repository에서는 실제 Robot에서 검증된 Source 구조와 Dynamic Dependency를 보존하는 것을 우선하며,
향후 학습 기반 자율 Policy는 기존 Main Runtime을 최대한 유지한 상태에서 후속 단계로 연결하는 방향으로 개발합니다.

---

# 1. 전체 역할

`preprocessing/` 계층은 Camera Input으로부터 Robot Manipulation에 필요한 정보를 생성하고,
실제 Upper / Lower Runtime을 실행하는 역할을 담당합니다.

주요 기능은 다음과 같습니다.

- ELP OV2710 Camera Input
- Camera Undistortion
- Garment Segmentation
- Upper / Lower Pose Estimation
- Garment Mask 분석
- Contour 및 Geometry 분석
- Keypoint / Landmark 분석
- Garment Orientation 판단
- Fold / Wrinkle 분석
- Grasp Candidate 계산
- Folding Board Coordinate 변환
- Manipulation Planning
- Dual RoArm M2-S Execution
- Manipulation 후 Re-observation
- 향후 Learned Action Decision
- 향후 Folding-ready 종료조건 판단

---

# 2. Upper / Lower 현재 개발 상태

현재 Upper와 Lower는 서로 다른 개발 단계에 있습니다.

## Upper

현재 GitHub에는 상의의 Main Manipulation Runtime이 포함되어 있습니다.

현재 Main Runtime은 다음 단계까지 수행합니다.

    Basket Grasp
        ↓
    Folding Board Transfer
        ↓
    Initial Placement
        ↓
    Reposition
        ↓
    Segmentation + Upper Pose
        ↓
    Final Grasp Selection
        ↓
    Dual-Arm Grasp
        ↓
    Aerial Lift / Alignment
        ↓
    Laydown
        ↓
    Standby Return

현재 Upper Main Runtime 이후에는 향후 학습 Model 기반의 후속 Manipulation Stage를 연결할 예정입니다.

---

## Lower

현재 GitHub에는 하의 Main Runtime이 포함되어 있습니다.

Lower Runtime은 현재 완전 자동 Action Selection 방식이 아니라
**Human-in-the-loop Semi-Automatic Manipulation Runtime**입니다.

System이 Garment Perception과 Manipulation Planning을 수행하고,
사용자가 현재 상태에 적절한 Semantic Action을 선택합니다.

현재 이 과정은 향후 VLA 기반 Automatic Action Policy 학습을 위한 Data Collection 단계입니다.

---

# 3. Upper Runtime

Upper Runtime Directory:

    SW/Jetson/preprocessing/upper/

Repository-Relative Launcher:

    SW/Jetson/preprocessing/upper/run_upper.py

현재 Upper Runtime은 다음 기능을 포함합니다.

- Basket Garment Grasp
- Board Transfer
- Garment Laydown
- Initial Reposition
- Garment Segmentation
- Upper Pose Estimation
- Keypoint 기반 Final Grasp Point Selection
- Dual-Arm Grasp
- Vertical Lift
- Aerial Alignment
- Laydown
- Garment Release
- Standby Return

Dependency 검사:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

실제 Robot Runtime:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

`--physical-auto`는 실제 Dual RoArm M2-S를 동작시키므로 Hardware 상태와 Workspace Safety를 확인한 뒤 실행해야 합니다.

자세한 내용:

    SW/Jetson/preprocessing/upper/README.md

---

# 4. Upper 향후 Learned Manipulation

현재 Upper Main Runtime은 Laydown까지 수행합니다.

향후에는 이 Main Runtime 이후 새로운 Camera Observation을 기반으로
의류 상태를 다시 판단하고 필요한 Manipulation을 선택하는 학습 기반 Module을 연결할 예정입니다.

목표 구조:

    Current Upper Main Runtime
            ↓
    Laydown
            ↓
    Camera Re-observation
            ↓
    Learned Garment-State Model
            ↓
    Additional Action Decision
            ↓
    Manipulation
            ↓
    Re-observation
            ↓
    Termination Decision

향후 자동 판단 대상으로 고려하는 Action의 예시는 다음과 같습니다.

- Wrinkle Unfold
- Fold Correction
- Position Adjustment
- Alignment
- Pull
- Reposition
- Rejudge
- Finish

최종적으로 학습 Model이

    FOLDING_READY = TRUE

를 판단하면 Upper Manipulation Loop를 종료하고 Folding Board 단계로 이동하는 것을 목표로 합니다.

현재 이 후속 Learned Module은 개발 단계이며,
현재 GitHub에 포함된 Upper Main Runtime과 구분하여 관리합니다.

---

# 5. Lower Runtime

Lower Runtime Directory:

    SW/Jetson/preprocessing/lower/

Repository-Relative Launcher:

    SW/Jetson/preprocessing/lower/run_lower.py

Main Semantic Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-16.py

Integrated Base Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/main-33.py

현재 Lower Runtime에서 사용자가 선택할 수 있는 Semantic Action은 다음과 같습니다.

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
    Segmentation / Bottom Pose
            ↓
    Garment State Analysis
            ↓
    Human Semantic Action Selection
            ↓
    Automatic Manipulation Planning
            ↓
    Frozen Plan
            ↓
    ENTER Approval
            ↓
    Robot Execution
            ↓
    Result Evaluation
            ↓
    Dataset Save

현재 Lower Runtime을 완전 자율 System으로 표현하지 않습니다.

---

# 6. Lower VLA Data Collection

현재 Human Semantic Action Selection의 목적은
향후 **VLA(Vision-Language-Action) 기반 Automatic Action Policy**를 학습하기 위한 Data를 수집하는 것입니다.

현재 수집하는 핵심 관계는 다음과 같습니다.

    Garment Observation
            ↓
    Garment State
            ↓
    Semantic Action
            ↓
    Manipulation Result
            ↓
    Next Garment State

사용자의 Action 선택은 다양한 Garment State에서

    "현재 상태에서는 어떤 Action이 적절한가?"

라는 학습 Label 역할을 합니다.

향후 충분한 Dataset이 확보되면 현재 사용자가 수행하는 `1 ~ 8` Semantic Action Selection을
학습된 VLA Model의 Action Output으로 대체하는 것을 목표로 합니다.

---

# 7. Lower 향후 VLA 자동화

현재:

    Perception
        ↓
    Human Action Selection
        ↓
    Planning
        ↓
    Robot Execution

향후:

    Perception
        ↓
    VLA State Understanding
        ↓
    Semantic Action Prediction
        ↓
    Planning
        ↓
    Robot Execution
        ↓
    Re-observation
        ↓
    VLA Re-decision

VLA Model은 어떤 Semantic Action을 수행할지 판단하고,
실제 Grasp Point, Target, Trajectory 및 Hardware Safety는 기존 검증된 Planner와 Runtime이 담당하는 구조를 유지할 예정입니다.

---

# 8. Lower 종료조건 자동 판단

Lower 역시 Action Selection 자동화만을 최종 목표로 하지 않습니다.

향후 System은 다음 상태를 종합적으로 판단하여 추가 Manipulation이 필요한지 결정하는 것을 목표로 합니다.

- Garment가 충분히 펼쳐졌는가
- Waistband 방향이 적절한가
- Crotch 구조가 안정적인가
- 양쪽 Leg가 적절히 배치되었는가
- Hem 위치가 적절한가
- 큰 Fold가 남아 있는가
- Garment Center가 적절한가
- Folding Board 기준 Orientation이 적절한가
- 추가 Position Adjustment가 필요한가
- 추가 Alignment가 필요한가

최종적으로

    FOLDING_READY = TRUE

가 결정되면 Lower Manipulation Loop를 종료하고 Folding Board 단계로 이동하는 것을 목표로 합니다.

---

# 9. Lower 주요 Source Dependency

현재 Lower Runtime은 다음 주요 Source로 구성됩니다.

    bottom_vla-16.py
        ↓
    main-33.py
        ↓
    ├── 50-1.py
    ├── 54-3.py
    ├── 55-5.py
    ├── 58-3.py
    ├── 60-13.py
    └── align-11.py

Perception Dependency:

    step_e49_bottom_perception.py
    step_e62_bottom_perception.py
    step_d25_v2.py

Camera Helper:

    camera_undistort.py

---

# 10. Lower D23 Dynamic Alias 구조

`step_d25_v2.py`는 내부적으로 `step_d23_v2` Module을 참조합니다.

하지만 최종 통합 Runtime에서는 별도의 standalone

    step_d23_v2.py

를 사용하지 않습니다.

다음 Runtime Source가 D25를 연결하기 전에 현재 Module을 `step_d23_v2` 이름으로 등록합니다.

    54-3.py
    55-5.py
    60-13.py
    align-11.py

즉 Lower의 D23 관계는 단순 File Dependency가 아니라
검증된 **Dynamic Module Alias 구조**입니다.

따라서 `step_d23_v2.py`가 Repository에 별도로 존재하지 않는 것은 누락이 아닙니다.

---

# 11. Lower Homography

Lower Runtime은 다음 Local Homography를 사용합니다.

    SW/Jetson/preprocessing/lower/dual/undistort/
    elp_ov2710_folding_board_homography_cache.json

해당 File은 다음 정보를 포함합니다.

    H
    raw_H
    camera_geometry
    schema_version

Lower에서는 Action에 따라 Corrected Camera Geometry와 RAW Camera Geometry를 모두 사용하므로
Upper/Common Homography보다 추가 정보가 필요합니다.

---

# 12. Upper/Common Homography와의 차이

다음 Common Homography:

    SW/Jetson/common/calibration/
    elp_ov2710_folding_board_homography_cache.json

와 Lower-specific Homography는 같은 File 이름을 사용하지만 동일한 Artifact가 아닙니다.

Upper/Common:

    H 중심의 검증된 Upper Calibration

Lower-specific:

    H
    raw_H
    camera_geometry
    schema_version

따라서 두 Homography를 서로 덮어쓰거나 하나로 통합하지 않습니다.

---

# 13. Lower AI Model

Lower Runtime은 다음 TensorRT Model을 사용합니다.

## Shared Garment Segmentation

    SW/Jetson/models/segmentation/
    kfashion_yolo26s_seg3_e100_best.engine

## Bottom Pose

    SW/Jetson/models/pose/lower/
    bottom_pose8_beige_finetune_v2_best.engine

Repository-Relative `run_lower.py`는 해당 Model 경로를 Main Runtime에 명시적으로 전달합니다.

---

# 14. Lower 실행 방법

Dependency 검사:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

Dry-run:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run

Physical Runtime:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

`--physical`은 실제 Dual RoArm M2-S Motion을 활성화하므로 Robot 및 Workspace Safety를 확인한 뒤 실행해야 합니다.

---

# 15. Lower GitHub Fresh-Clone 검증

Lower Runtime은 GitHub 업로드 후 별도의 Fresh Clone Directory에서 검증했습니다.

검증 결과:

    Dependency:
    PASS=19
    FAIL=0

    Python Compile:
    PASS=13
    FAIL=0

    Static Dependency:
    PASS=36
    FAIL=0

또한 Fresh Clone Repository 내부 Source를 사용하여 다음 Runtime Initialization을 확인했습니다.

- Lower Source Loading
- Dynamic Source Dependency 연결
- E49 / E62 / D25 연결
- Lower-specific Homography Loading
- Camera Open
- Camera Control 적용
- Camera Undistortion
- Segmentation TensorRT Engine Loading
- Bottom Pose TensorRT Engine Loading
- TensorRT Execution Context Warm-up
- Bottom VLA Operator Runtime 진입

---

# 16. Clean Docker GitHub-only 검증

Lower Runtime은 기존 개발 Directory가 Runtime을 우연히 보조하는지 확인하기 위해
별도의 Clean Docker 환경에서도 추가 검증했습니다.

검증 조건:

- 기존 Runtime과 동일한 Docker Image 사용
- NVIDIA Runtime 사용
- `/workspace/project_train`을 빈 Read-only Directory로 대체
- Legacy Project Directory 내부 File 수 = 0
- `PYTHONPATH`에 기존 Project 경로 없음
- `/dev/roarm_1` 전달하지 않음
- `/dev/roarm_2` 전달하지 않음
- `/dev/ttyACM0` 전달하지 않음
- `/dev/video0`만 전달
- GitHub Repository를 Container 내부 `/tmp`에 새로 Clone

이 환경에서 다음을 확인했습니다.

    GitHub Fresh Clone
        ↓
    Dependency Check 19 / 19 PASS
        ↓
    Lower Homography Validation PASS
        ↓
    Camera Open PASS
        ↓
    Camera Control PASS
        ↓
    Camera Undistortion PASS
        ↓
    Segmentation TensorRT Load PASS
        ↓
    Bottom Pose TensorRT Load PASS
        ↓
    TensorRT Warm-up PASS
        ↓
    Bottom VLA Operator Runtime PASS

실제 Runtime Source, Model 및 Calibration 경로는 모두 Fresh Clone Repository 내부의

    /tmp/jeopsin_github_clean/SW/Jetson/...

경로를 사용했습니다.

이를 통해 기존 `/workspace/project_train` 개발 Directory의 Source, Model 또는 Calibration에 의존하지 않고
GitHub Repository 내부 Artifact만으로 Lower Runtime을 초기화할 수 있음을 확인했습니다.

Robot Device는 Clean Docker에 전달하지 않았기 때문에
이 검증은 Physical Robot Motion Test가 아니라 **Repository Runtime Reproducibility 및 Initialization 검증**입니다.

---

# 17. Legacy Absolute Path와 Repository Launcher

일부 기존 Runtime Source에는 개발 당시 사용했던

    /workspace/project_train/...

형태의 Legacy Default 또는 Fallback 경로가 남아 있습니다.

현재 제출 Runtime에서는 검증된 Source 자체를 대규모로 수정하지 않고,
Repository-Relative Launcher가 필요한 Source, Model 및 Calibration 경로를 명시적으로 전달하는 구조를 사용합니다.

Upper:

    run_upper.py

Lower:

    run_lower.py

이를 통해 기존 Robot Runtime의 검증된 Source 구조를 유지하면서
GitHub Repository 내부 Artifact를 사용하도록 구성합니다.

---

# 18. Docker 실행 환경

현재 주요 Jetson Runtime은 Docker Container 내부에서 실행 및 검증했습니다.

현재 Runtime 검증 환경:

- NVIDIA Jetson Orin Nano
- Ubuntu 22.04.3 Host
- Docker 29.7.2
- Runtime Image: `roarm_dual_working_20260814:latest`
- NVIDIA Container Runtime
- Python 3.10.12
- TensorRT 10.7.0
- OpenCV 4.11.0
- PyTorch 2.10.0
- CUDA Runtime 12.6 (PyTorch)
- NumPy 1.26.4
- Ultralytics 8.4.45
- XGBoost 3.2.0

현재 Runtime은 ELP OV2710 Camera와 Dual RoArm M2-S를 Hardware Interface로 사용합니다.

---

# 19. Source 구조 유지 원칙

현재 Upper와 Lower Runtime은 실제 Robot에서 검증된 다음 구조를 포함합니다.

- Dynamic Import
- Same-directory Dependency
- Source Text Patch
- Module Alias
- Runtime Working Directory 의존 관계
- 검증된 File 이름
- Calibration Artifact
- TensorRT Engine

따라서 전체 Runtime 재검증 없이 다음 작업을 수행하지 않는 것을 권장합니다.

- 핵심 Source File 이름 변경
- Directory 임의 이동
- Import 자동 정리
- 자동 Formatter 적용
- Dynamic Source 구조 제거
- D23 Alias 구조 변경
- Upper Source-Text Patch 구조 변경
- Homography 통합
- Model 임의 교체

---

# 20. 최종 목표

Upper와 Lower 모두 최종적으로 다음 Closed-loop 구조를 지향합니다.

    Camera Observation
            ↓
    Garment Perception
            ↓
    Garment State Understanding
            ↓
    Learned Action Decision
            ↓
    Manipulation Planning
            ↓
    Safety / Geometry Validation
            ↓
    Dual RoArm Execution
            ↓
    Re-observation
            ↓
    Additional Action Decision
            ↓
    Termination Condition
            ↓
    FOLDING_READY
            ↓
    Folding Board

현재 Upper는 Main Manipulation Runtime 이후 Learned Garment-State Decision Module을 추가하는 방향으로 개발 중이며,
현재 Lower는 Human-in-the-loop VLA Data Collection을 통해 향후 Semantic Action Selection을 자동화하는 단계로 발전시키고 있습니다.

최종적으로 사람이 각 조작 단계를 직접 선택하지 않아도
System이 의류 상태를 반복적으로 관찰하면서 필요한 Manipulation을 스스로 선택하고,
**Folding Board로 접을 수 있는 상태인지까지 자동으로 판단하는 것**을 목표로 합니다.
