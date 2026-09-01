# Runtime Architecture

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서
Perception, Action Decision, Manipulation Planning 및 Hardware Execution이 어떻게 연결되는지를 설명합니다.

현재 실제 실행 가능한 Upper / Lower Runtime Source는 각각 다음 위치에 있습니다.

    SW/Jetson/preprocessing/upper/
    SW/Jetson/preprocessing/lower/

`runtime/` 디렉터리는 검증된 Source를 별도로 복사하거나 강제로 이동하지 않고,
전체 실행 구조와 각 Runtime의 역할을 설명하기 위한 Architecture 계층으로 사용합니다.

---

# 1. 전체 Runtime 구조

「접신」의 전체 Runtime은 다음과 같은 Closed-loop 구조를 지향합니다.

    Camera Input
        ↓
    Perception
        ↓
    Garment State Analysis
        ↓
    Action Decision
        ↓
    Manipulation Planning
        ↓
    Safety / Geometry Validation
        ↓
    Dual RoArm Execution
        ↓
    New Camera Observation
        ↓
    Garment State Re-evaluation
        ↓
    Additional Action / Termination Decision
        ↓
    Folding-ready
        ↓
    Folding Board

의류는 Robot Manipulation 후 형태가 계속 변하기 때문에,
한 번 계산한 초기 상태만으로 전체 Sequence를 끝까지 수행하는 것이 아니라
새로운 Camera Observation을 통해 상태를 다시 평가하는 구조를 사용합니다.

---

# 2. 현재 Runtime 구성

현재 Upper와 Lower의 구현 단계는 서로 다릅니다.

## Upper

현재 Upper Main Runtime은 실제 Robot Manipulation Sequence까지 구현되어 있으며,
GitHub Repository 내부 Source와 Model, Calibration을 기준으로 실행할 수 있도록 구성되어 있습니다.

경로:

    SW/Jetson/preprocessing/upper/

Entry Point:

    SW/Jetson/preprocessing/upper/run_upper.py

## Lower

현재 Lower Runtime은 Human-in-the-loop 기반의 Semi-Automatic Manipulation System입니다.

Perception과 Action-specific Planning은 System이 수행하지만,
현재 단계에서는 사용자가 Semantic Action을 선택합니다.

경로:

    SW/Jetson/preprocessing/lower/

Entry Point:

    SW/Jetson/preprocessing/lower/run_lower.py

Main Semantic Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-16.py

Integrated Base Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/main-33.py

---

# 3. Upper Runtime

현재 Upper Runtime은 다음 Manipulation Sequence를 수행합니다.

    Basket
      ↓
    ARM2 Garment Grasp
      ↓
    Folding Board Transfer
      ↓
    Initial Laydown
      ↓
    Reposition
      ↓
    Segmentation + Upper Pose
      ↓
    Final Grasp Point Selection
      ↓
    Dual-Arm Grasp
      ↓
    Vertical Lift
      ↓
    Aerial Alignment
      ↓
    Laydown
      ↓
    Release
      ↓
    Standby Return

현재 Upper Runtime은 실제 Robot Motion에서 검증된 Source와
Dynamic Source Dependency를 유지합니다.

---

# 4. Upper 실행 방법

Repository Root에서 Dependency 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

Upper Runtime Directory에서 실행할 경우:

    cd SW/Jetson/preprocessing/upper
    python3 run_upper.py --paths-only

실제 Robot Motion:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

`--physical-auto`는 실제 Dual RoArm M2-S를 동작시키므로
Robot, Garment, Folding Board 및 Workspace 상태를 확인한 뒤 실행해야 합니다.

---

# 5. Upper Runtime Dependency 구조

Upper Runtime은 다음 유형의 Resource를 사용합니다.

### Runtime Source

- Upper Main Runtime
- Base Runtime Source
- Perception Module
- Geometry / Action Helper

### AI Model

- Garment Segmentation TensorRT Engine
- Upper Pose TensorRT Engine

### Calibration

- Camera Intrinsic Calibration
- Folding Board Homography
- Dual RoArm Configuration
- Basket ARM2 Affine Calibration

### Hardware

- ELP OV2710 Camera
- Dual RoArm M2-S

검증 완료된 Upper Runtime은 일부 Source-Text Patch 및 Dynamic Source Loading 구조를 포함하므로
Source 이름이나 Directory 구조를 임의로 변경하지 않는 것을 원칙으로 합니다.

---

# 6. Upper 향후 Runtime 확장

현재 Upper Main Runtime은 Laydown까지 수행합니다.

향후에는 이 Main Runtime 이후에
학습 Model 기반의 추가 Garment Manipulation Runtime을 연결할 예정입니다.

목표 구조:

    Current Upper Main Runtime
            ↓
    Laydown
            ↓
    Camera Re-observation
            ↓
    Learned Garment-State Model
            ↓
    Action Decision
            ↓
    Wrinkle Unfold
        or
    Position Adjust
        or
    Alignment
        or
    Reposition
            ↓
    Re-observation
            ↓
    Additional Action Decision
            ↓
    Folding-ready

향후 학습 기반 Module은 다음을 스스로 판단하는 것을 목표로 합니다.

- Wrinkle 제거 필요 여부
- Fold 제거 필요 여부
- 위치 보정 필요 여부
- 추가 Alignment 필요 여부
- 추가 Manipulation 필요 여부
- Folding-ready 종료조건

현재 이 후속 Module은 개발 단계이며,
현재 GitHub에 포함된 Upper Main Runtime과 구분하여 관리합니다.

---

# 7. Lower Runtime

현재 Lower Runtime은 VLA 학습용 Data를 수집하기 위한
Human-in-the-loop Semi-Automatic Runtime입니다.

현재 Operator가 선택할 수 있는 Semantic Action은 다음과 같습니다.

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

현재 Lower Runtime의 기본 흐름은 다음과 같습니다.

    Camera Observation
            ↓
    Garment Segmentation
            ↓
    Bottom Pose Estimation
            ↓
    Garment State Analysis
            ↓
    Human Semantic Action Selection
            ↓
    Action-specific Planning
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

---

# 8. Lower Frozen Plan 구조

Lower Runtime에서는 한 번 Action Preparation을 수행하면
해당 Action에 대한 Manipulation Plan을 고정합니다.

    Semantic Action
        ↓
    Perception
        ↓
    Planning
        ↓
    Frozen Plan
        ↓
    ENTER
        ↓
    Exact Frozen Plan Execution

`ENTER`는 새로운 Perception이나 새로운 Planning을 수행하는 명령이 아니라
화면에 표시되고 이미 계산된 Plan을 실행하는 승인 단계입니다.

이를 통해 사용자가 확인한 Plan과 실제 Robot이 수행하는 Plan의 일관성을 유지합니다.

---

# 9. Lower 실행 방법

Dependency 및 Repository Path 확인:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

Dry-run:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run

`--dry-run`은 Camera와 TensorRT Runtime을 초기화하여
Repository 내부 Source, Model 및 Calibration이 실제 Runtime까지 연결되는지를 확인하는 데 사용할 수 있습니다.

실제 Robot Runtime:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

`--physical`은 실제 Dual RoArm M2-S Motion을 활성화합니다.

Physical Mode 실행 전에는 반드시 다음을 확인해야 합니다.

- ARM1 / ARM2 Serial Device
- Robot Standby Pose
- Folding Board Workspace
- Garment 위치
- Camera 상태
- Calibration File
- Homography
- Robot 주변 장애물

---

# 10. Lower GitHub Fresh-Clone 검증

Lower Runtime은 GitHub 업로드 후 기존 개발 Directory를 사용하지 않고
새로운 Temporary Directory에 Repository를 Fresh Clone하여 검증했습니다.

Fresh Clone 기준 Dependency Check:

    PASS=19
    FAIL=0

Python Compile:

    PASS=13
    FAIL=0

Static Dependency:

    PASS=36
    FAIL=0

또한 Fresh Clone Repository 내부 File만 사용하여 다음 Runtime Initialization까지 확인했습니다.

- `run_lower.py` 실행
- `bottom_vla-16.py` Loading
- `main-33.py` Loading
- Action Source Loading
- E49 / E62 / D25 Perception Dependency 연결
- Lower-specific Homography Loading
- Camera Open
- Camera Control 적용
- Camera Undistortion Calibration
- Segmentation TensorRT Engine Loading
- Lower Pose TensorRT Engine Loading
- TensorRT Execution Context Warm-up
- Bottom VLA Operator Runtime 진입

이를 통해 기존 `/workspace/project_train/...` 개발 Directory에 의존하지 않고
GitHub Repository 내부 File만으로 Lower Runtime을 초기화할 수 있음을 확인했습니다.

---

## 10.1 Clean Docker GitHub-only 재현성 검증

Fresh Clone 검증 이후 기존 `/workspace/project_train` 개발 Directory의 존재가 Runtime을 우연히 보조할 가능성을 배제하기 위해 별도의 Clean Docker Test를 수행했습니다.

Clean Container 조건:

- Runtime Image: `roarm_dual_working_20260814:latest`
- NVIDIA Runtime 사용
- `/workspace/project_train` = 빈 Read-only Directory
- Legacy Directory File Count = 0
- `/dev/roarm_1` 없음
- `/dev/roarm_2` 없음
- `/dev/ttyACM0` 없음
- `/dev/video0`만 사용
- GitHub Repository 신규 Clone

이 환경에서 Lower Runtime은 다음 단계까지 정상적으로 초기화되었습니다.

- Dependency 19 / 19 PASS
- Lower-specific Homography Validation PASS
- Camera Open
- Camera Control 적용
- Camera Undistortion
- Segmentation TensorRT Engine Loading
- Bottom Pose TensorRT Engine Loading
- TensorRT Execution Context Warm-up
- Bottom VLA Operator Runtime 진입

모든 Runtime Source, Model 및 Calibration 경로는 Fresh Clone Repository 내부를 사용했습니다.

따라서 Lower Main Runtime의 Repository Dependency가 기존 개발 Directory 없이도 재현됨을 확인했습니다.

Clean Docker에는 Robot Device를 전달하지 않았으므로 Physical Robot Motion은 이 Test의 검증 범위에 포함하지 않습니다.

# 11. Lower 향후 VLA Runtime

현재 Lower Runtime에서는 사람이 Semantic Action을 선택합니다.

현재:

    Camera
      ↓
    Perception
      ↓
    Garment State
      ↓
    Human Action Selection
      ↓
    Planner
      ↓
    Robot Execution

향후:

    Camera
      ↓
    Perception
      ↓
    Garment State
      ↓
    VLA Action Decision
      ↓
    Planner
      ↓
    Robot Execution
      ↓
    Re-observation
      ↓
    VLA Re-decision

즉 현재 `1 ~ 8` Key 입력으로 수행되는 Semantic Action Selection을
학습된 VLA Model의 Output으로 대체할 예정입니다.

---

# 12. Lower 종료조건 Runtime

향후 Lower VLA Runtime은 단순히 다음 Action을 선택하는 것뿐 아니라
현재 의류가 Folding 단계에 진입할 수 있는지를 판단하는 기능까지 포함하는 것을 목표로 합니다.

예상 판단 요소:

- Garment가 충분히 펼쳐졌는가
- Waistband 방향이 적절한가
- Crotch 구조가 안정적인가
- 양 Leg가 충분히 정리되었는가
- Hem 위치가 정상적인가
- 큰 Fold가 남아 있는가
- Garment Position이 적절한가
- Folding Board 기준 Orientation이 적절한가
- 추가 Manipulation이 필요한가

종료조건:

    FOLDING_READY = TRUE

가 결정되면 Manipulation Loop를 종료하고 Folding Board 단계로 이동합니다.

---

# 13. Perception / Policy / Planning / Runtime 구분

각 Software Layer의 역할은 다음과 같습니다.

## Perception

현재 Garment State를 관찰합니다.

예:

- Mask
- Pose
- Contour
- Landmark
- Fold
- Wrinkle
- Orientation

---

## Policy

현재 상태에서 어떤 Semantic Action을 수행할지를 결정합니다.

예:

    ALIGN
    POSITION_ADJUST
    OUTER_PULL
    FINISH

---

## Planning

선택된 Semantic Action을 실제 Robot Motion으로 구체화합니다.

예:

    grasp point
    target point
    trajectory
    pull distance
    speed
    gripper state

---

## Runtime

Perception, Policy, Planning 및 Hardware Execution을 연결합니다.

    Perception
        ↓
    Policy
        ↓
    Planning
        ↓
    Safety Check
        ↓
    Hardware Execution

---

# 14. Safety Layer

Learned Policy가 향후 추가되더라도
Robot Safety는 Learned Model에 완전히 의존하지 않습니다.

기존 Runtime의 다음 Hard Safety Logic을 유지합니다.

- Robot Reachability
- Workspace Limit
- Grasp Validity
- Motion Geometry
- Calibration Validity
- Dual-Arm Coordination
- Path Constraint
- Serial Execution Gate
- Physical Mode Gate

즉 Learned Model이

    "어떤 Action을 수행할지"

결정하더라도,

    "그 Action을 실제로 어떻게 안전하게 수행할지"

는 검증된 Robot Runtime과 Planner가 담당합니다.

---

# 15. Hardware Interface

현재 Runtime Hardware:

### Main Processor

    NVIDIA Jetson Orin Nano

### Camera

    ELP OV2710
    /dev/video0
    1280 x 720

### Robot

    Dual RoArm M2-S

### Serial

    ARM1 : /dev/roarm_1
    ARM2 : /dev/roarm_2

Runtime에서는 Camera Coordinate와 Robot Workspace Coordinate를 연결하기 위해
Calibration 및 Homography 정보를 사용합니다.

---

# 16. Calibration Interface

Runtime에서 사용하는 주요 Calibration Resource는 다음 위치에 있습니다.

    SW/Jetson/common/calibration/

주요 File:

    dual_roarm_folding_board_config.json
    basket_arm2_5point_affine.json
    elp_ov2710_folding_board_homography_cache.json

Lower Runtime은 추가로 다음 Local Homography를 사용합니다.

    SW/Jetson/preprocessing/lower/dual/undistort/
    elp_ov2710_folding_board_homography_cache.json

Lower-specific Homography는 다음 정보를 포함합니다.

    H
    raw_H
    camera_geometry
    schema_version

Upper/Common Homography와 Lower-specific Homography는
같은 이름을 사용하지만 서로 다른 Runtime Geometry를 위한 File이므로
서로 덮어쓰거나 통합하지 않습니다.

---

# 17. Model Interface

현재 Runtime에서 사용하는 TensorRT Model은 다음 위치에 있습니다.

    SW/Jetson/models/

### Shared Segmentation

    models/segmentation/
    kfashion_yolo26s_seg3_e100_best.engine

### Upper Pose

    models/pose/upper/
    tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

### Lower Pose

    models/pose/lower/
    bottom_pose8_beige_finetune_v2_best.engine

향후 Upper Learned Policy 및 Lower VLA Policy용 Model은
학습과 Runtime 검증이 완료된 이후 추가할 예정입니다.

---

# 18. 현재 Runtime Source를 preprocessing 내부에 유지하는 이유

일반적인 Software Architecture 관점에서는
모든 Runtime Source를 `runtime/` 아래로 이동하여 정리할 수도 있습니다.

하지만 현재 제출본에서는 그렇게 하지 않습니다.

현재 Upper와 Lower Source는 실제 Robot에서 장기간 검증된

- Relative Source Loading
- Dynamic Import
- Source Text Patch
- Module Alias
- Same-directory Dependency
- Runtime Working Directory

구조를 포함합니다.

따라서 제출 과정에서 Source를 임의 이동하거나 Refactoring하면
기존 Robot Validation 결과와 다른 Runtime이 될 가능성이 있습니다.

현재 Repository에서는

**가독성보다 실행 재현성과 검증된 Dependency 보존을 우선합니다.**

---

# 19. Runtime 개발 원칙

다음 항목은 전체 Runtime 재검증 없이 변경하지 않는 것을 권장합니다.

- 검증된 Python Source 이름
- Dynamic Dependency 구조
- Source Loading 순서
- Same-directory Source 관계
- Upper Source-Text Patch 대상 이름
- Lower D23 Module Alias 구조
- Calibration File
- Homography 위치
- TensorRT Engine
- Robot Port
- Runtime Working Directory

기능 추가가 필요한 경우 기존 검증된 Runtime을 최대한 보존한 상태에서
새로운 기능을 외부 Module 또는 후속 Stage로 연결하는 방식을 우선합니다.

---

# 20. 최종 Runtime 목표

「접신」의 최종 Runtime은 상의와 하의 모두에서 다음 과정을 자동으로 반복하는 것을 목표로 합니다.

    Camera Observation
            ↓
    Garment Perception
            ↓
    State Understanding
            ↓
    Learned Action Decision
            ↓
    Safe Manipulation Planning
            ↓
    Dual RoArm Execution
            ↓
    Re-observation
            ↓
    Additional Action Decision
            ↓
    Termination Condition
            ↓
    Folding-ready
            ↓
    Folding Board

최종적으로 사람의 Action 선택 없이
System이 비정형 의류의 상태를 반복적으로 관찰하고,
필요한 펼침·정렬·위치 보정 Manipulation을 선택하여 수행한 뒤
**Folding Board로 접어도 되는 상태인지 스스로 판단하는 Closed-loop Automatic Garment Manipulation Runtime**을 구현하는 것이 목표입니다.
