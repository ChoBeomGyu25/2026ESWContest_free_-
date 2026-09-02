cd /workspace/2026ESWContest_free_Otgaestra && \
cat > SW/Jetson/preprocessing/lower/README.md <<'EOF'
# 하의 의류 인식 및 조작 Runtime

본 디렉터리는 **2026 임베디드 소프트웨어 경진대회 자유공모** 출품작  
**옷개스트라 - 접신** 프로젝트에서 사용하는 Jetson 기반 **하의 의류 인식·판단·조작 Runtime**을 포함합니다.

하의 처리 시스템은 완전 자동화된 Autonomous Pipeline이 아니라, 사용자가 상위 수준의 동작을 선택하고 시스템이 해당 동작에 필요한 인식과 경로 계획을 수행하는 **Human-in-the-loop Semi-Automatic Manipulation 구조**로 구현되어 있습니다.

기본적인 실행 흐름은 다음과 같습니다.

    사용자 Action 선택
            ↓
    의류 Perception / Geometry 분석
            ↓
    동작 경로 자동 Planning
            ↓
    Frozen Plan 생성
            ↓
    ENTER를 통한 사용자 승인
            ↓
    로봇 자동 실행
            ↓
    실행 결과 Review
            ↓
    결과 저장 또는 폐기

한 번 생성된 Plan은 Frozen 상태로 유지되며, 사용자가 `ENTER`를 입력했을 때 새로 재추론하는 것이 아니라 **승인된 Frozen Plan을 그대로 실행**합니다.

---

## 1. 디렉터리 구조

    lower/
    ├── README.md
    ├── run_lower.py
    ├── outputs/
    │
    └── dual/
        ├── step_e49_bottom_perception.py
        ├── step_e62_bottom_perception.py
        ├── step_d25_v2.py
        ├── elp_ov2710_camera_controls.json
        │
        └── undistort/
            ├── bottom_vla-16.py
            ├── main-33.py
            ├── 50-1.py
            ├── 54-3.py
            ├── 55-5.py
            ├── 58-3.py
            ├── 60-13.py
            ├── align-11.py
            ├── camera_undistort.py
            ├── elp_ov2710_1280x720_calibration.npz
            └── elp_ov2710_folding_board_homography_cache.json

하의 Pose 및 공용 Segmentation 모델은 다음 경로를 사용합니다.

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_beige_finetune_v2_best.engine

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

공용 로봇 및 Folding Board Calibration 파일은 다음 위치에서 사용합니다.

    SW/Jetson/common/calibration/
    ├── dual_roarm_folding_board_config.json
    ├── basket_arm2_5point_affine.json
    └── elp_ov2710_folding_board_homography_cache.json

---

## 2. 실행 Entry Point

하의 시스템의 최종 Semantic Action Runtime은 다음 파일입니다.

    dual/undistort/bottom_vla-16.py

GitHub 저장소에서는 기존 검증된 Source Code를 직접 수정하지 않고 다음 Wrapper를 통해 실행합니다.

    run_lower.py

`run_lower.py`는 GitHub Repository의 현재 위치를 기준으로 필요한 Source, Model, Calibration 경로를 자동으로 계산한 뒤 기존 Runtime의 CLI 인자로 전달합니다.

이를 통해 개발 당시 사용한 `/workspace/project_train/...` 형태의 절대경로에 의존하지 않고 GitHub 저장소 내부 파일을 사용할 수 있습니다.

---

## 3. 주요 Dependency 구조

하의 Runtime의 핵심 의존 관계는 다음과 같습니다.

    run_lower.py
        │
        └── bottom_vla-16.py
                │
                ├── main-33.py
                ├── 50-1.py
                ├── 54-3.py
                ├── 55-5.py
                ├── 58-3.py
                ├── 60-13.py
                └── align-11.py

Perception 관련 Module:

    step_e49_bottom_perception.py
    step_e62_bottom_perception.py
    step_d25_v2.py

Camera 관련 Module:

    camera_undistort.py
    elp_ov2710_1280x720_calibration.npz
    elp_ov2710_camera_controls.json

여러 Action Module은 Runtime 중 Source Path를 통해 동적으로 Load되므로, 검증된 파일명 및 디렉터리 구조를 임의로 변경하지 않는 것을 권장합니다.

특히 단순한 코드 정리를 목적으로 파일명을 변경하거나 Import 구조를 일괄적으로 수정하면 Runtime Dependency가 깨질 수 있습니다.

---

## 4. Semantic Action

`bottom_vla-16.py`에서는 사용자가 하의 상태에 따라 수행할 Semantic Action을 선택할 수 있습니다.

| Key | 기능 |
|---|---|
| `1` | BASKET_GRASP |
| `2` | OUTER_PULL |
| `3` | PRESS_SWEEP |
| `4` | WAIST_PULL_LAYDOWN |
| `5` | ALIGN |
| `6` | FINISH |
| `7` | REJUDGE |
| `8` | POSITION_ADJUST |
| `ENTER` | 현재 Frozen Plan 실행 |
| `A / M` | Mask Accurate / Inaccurate |
| `G / B / K` | 실행 결과 분류 |
| `Y / N` | 결과 저장 / 폐기 |
| `E` | Empty-board Baseline |
| `L` | Lock |
| `Q` | 종료 |

일반적인 실행 흐름은 다음과 같습니다.

    Action 선택
        ↓
    자동 Perception
        ↓
    자동 Planning
        ↓
    Frozen Plan 생성
        ↓
    ENTER 승인
        ↓
    Physical Execution
        ↓
    결과 Review
        ↓
    Y / N

일부 동작이 성공하면 시스템이 다음 권장 Action을 자동으로 Prepare할 수 있으나, 실제 로봇 동작 실행에는 다시 사용자의 `ENTER` 승인이 필요합니다.

---

## 5. 주요 Action Module

### bottom_vla-16.py

하의 시스템의 상위 Semantic Action Controller입니다.

주요 역할:

- 사용자 Action 선택
- Frozen Plan 관리
- 실행 승인 처리
- 결과 Review
- 다음 Action 추천
- Action Module 연결
- Base Runtime 연결

### main-33.py

하의 전체 시스템의 통합 Runtime입니다.

주요 역할:

- Camera 초기화
- Camera Control 적용
- Raw / Corrected Frame 관리
- Segmentation Model Loading
- Pose Model Loading
- Calibration Loading
- Coordinate Transformation
- Action Source Dynamic Loading
- Robot Runtime 관리

다음과 같은 CLI Path Override를 지원합니다.

    --d50-source
    --d54-source
    --d55-source
    --d58-source
    --config
    --hfile
    --camera-calibration
    --camera-controls-json
    --dataset-root
    --seg-model
    --pose-model
    --empty-board-raw-path
    --empty-board-corrected-path

`run_lower.py`는 해당 인자를 이용하여 GitHub Repository 내부 파일을 Runtime에 전달합니다.

### 50-1.py

Basket 관련 하의 조작 Source입니다.

### 54-3.py

`OUTER_PULL` 동작을 담당합니다.

Corrected Camera Geometry와 하의 Perception 결과를 이용하여 의류 외곽을 정렬하기 위한 조작을 계획합니다.

### 55-5.py

`PRESS_SWEEP` 동작을 담당합니다.

하의 영역을 누르고 펼치는 조작을 수행하기 위한 Planning 및 Runtime Logic을 포함합니다.

### 58-3.py

`POSITION_ADJUST` 동작을 담당합니다.

의류의 위치와 주변 여유 공간을 분석하여 하의를 보드 위에서 재배치하기 위한 동작 경로를 생성합니다.

### 60-13.py

`WAIST_PULL_LAYDOWN` 동작을 담당합니다.

Waistband와 하의 Pose/Geometry 정보를 기반으로 허리 영역을 파지하고 Laydown하기 위한 동작을 계획합니다.

### align-11.py

`ALIGN` 동작을 담당합니다.

하의 Pose와 Geometry 정보를 이용하여 의류의 방향 및 위치를 정렬합니다.

---

## 6. 하의 Perception

### step_e49_bottom_perception.py

하의 Segmentation, Pose 및 Geometry 분석을 수행합니다.

주요 기능:

- Segmentation Mask 선택
- Glare / Specular 억제
- Wrinkle Heatmap 분석
- Local Shadow 분석
- Bottom Pose 추론
- TTA 및 Consensus
- Temporal Stabilization
- Mask Topology 분석
- PCA 및 Oriented Rectangle Geometry
- Crotch Concavity 분석
- Waistband Evidence 분석
- Landmark Reconstruction
- Pose Geometry Scoring

본 Module은 Perception 및 Geometry 결과를 생성하며 직접적인 Robot Action 선택이나 Serial Command는 수행하지 않습니다.

### step_e62_bottom_perception.py

E49 기반의 하의 상태 분석을 확장한 Module입니다.

주요 기능:

- Spread-ready 판단
- Centered-ready 판단
- Axis-parallel-ready 판단
- Termination-ready 판단
- Edge / Near-edge / Interior Wrinkle 분류
- Waistband 및 Crotch에서 자연스럽게 발생하는 Residual Pattern 억제

실제 접힘과 의류 고유 구조를 구분하여 불필요한 재조작을 줄이는 데 사용됩니다.

### step_d25_v2.py

Reference-free 방식의 하의 Finish Evaluator입니다.

주요 평가 요소:

- 하나의 일관된 Waist 영역
- 정상적인 Crotch Concavity
- 두 개의 Leg 구조
- 두 개의 Hem 영역
- Pose + Geometry 기반 Landmark
- Convexity Defect
- Contour 변화
- Macro Fold 검출

Fine Wrinkle, Elastic Waist Gather, Center-rise Seam, 일반적인 Hem Line은 가능한 한 완료 판정을 불필요하게 방해하지 않도록 하고, 실제로 조작이 필요한 큰 Fold를 중심으로 판단합니다.

본 Module 역시 Perception 전용이며 Robot Serial Command를 수행하지 않습니다.

---

## 7. step_d23_v2 Compatibility Alias

`step_d25_v2.py` 내부에는 다음 Module Dependency가 존재합니다.

    step_d23_v2

그러나 최종 Integrated Runtime에서는 별도의 `step_d23_v2.py` 파일을 사용하지 않습니다.

다음 Action Module들이 D25를 Load하기 전에 자신을 `step_d23_v2`로 등록합니다.

    sys.modules.setdefault("step_d23_v2", sys.modules[__name__])

해당 구조를 사용하는 Module:

- 54-3.py
- 55-5.py
- 60-13.py
- align-11.py

따라서 최종 GitHub Runtime에서는 별도의 `step_d23_v2.py` 파일을 Dependency로 추가하지 않습니다.

---

## 8. Camera 및 Calibration

사용 Camera:

- ELP OV2710
- Resolution: 1280 × 720
- V4L2
- Camera Index: 0

Camera Control:

    dual/elp_ov2710_camera_controls.json

Camera Intrinsic / Undistortion Calibration:

    dual/undistort/elp_ov2710_1280x720_calibration.npz

Camera Helper:

    dual/undistort/camera_undistort.py

---

## 9. Lower 전용 Homography

하의 Runtime은 다음 Homography를 사용합니다.

    dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

이 파일은 다음 Geometry 정보를 포함합니다.

- H
- raw_H
- camera_geometry
- schema_version

하의 Runtime은 Raw Frame과 Corrected Frame Geometry를 구분하여 사용하므로 이 파일이 필요합니다.

한편 공용 Calibration Directory에도 동일한 이름의 파일이 존재합니다.

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

두 파일은 이름이 같지만 내용과 용도가 서로 다릅니다.

따라서 **하의 전용 Homography와 공용 Homography를 서로 덮어쓰거나 하나의 파일로 통합하면 안 됩니다.**

---

## 10. AI Model

### Garment Segmentation

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

TensorRT 기반 Segmentation Model입니다.

### Bottom Pose

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_beige_finetune_v2_best.engine

하의 Landmark 및 Pose 추론에 사용하는 TensorRT Pose Model입니다.

---

## 11. 공용 Calibration

하의 Runtime에서 사용하는 공용 Robot / Folding Board Calibration:

    SW/Jetson/common/calibration/
    ├── dual_roarm_folding_board_config.json
    └── basket_arm2_5point_affine.json

---

## 12. Dependency 검사

실제 Robot을 동작시키기 전에 Repository 내부 Dependency를 검사할 수 있습니다.

Repository Root에서:

    cd /workspace/2026ESWContest_free_Otgaestra

다음 명령을 실행합니다.

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

현재 GitHub 로컬 제출본에서 확인된 Baseline:

    PASS=19 FAIL=0 TOTAL=19

검사 대상에는 다음 항목들이 포함됩니다.

- bottom_vla
- main-33
- Action Source
- Perception Module
- Camera Helper
- Camera Calibration
- Lower Homography
- Camera Control
- Robot / Board Config
- Basket Calibration
- Segmentation Model
- Bottom Pose Model

---

## 13. 실행 방법

Repository Root:

    cd /workspace/2026ESWContest_free_Otgaestra

### Dependency 확인

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

### 기본 Wrapper 실행

    python3 SW/Jetson/preprocessing/lower/run_lower.py

Wrapper에서는 추가적으로 다음 Runtime Mode를 지원합니다.

    --hover
    --physical

---

## 14. 실제 Robot 실행 주의

**주의: `--physical` 옵션은 실제 RoArm M2-S의 물리 동작을 활성화합니다.**

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

실행 전 반드시 다음을 확인해야 합니다.

- ARM1 / ARM2 전원 상태
- Serial Port 연결 상태
- 작업 공간 내 장애물 여부
- Camera 연결 상태
- Folding Board Calibration 상태
- 비상 전원 차단 가능 여부
- 조작 경로 내 사람이나 물체가 없는지 여부

Robot Port:

    ARM1: /dev/roarm_1
    ARM2: /dev/roarm_2

Repository Dependency 확인만을 목적으로 할 경우 `--physical`을 실행할 필요가 없습니다.

---

## 15. Generated Output

Runtime 과정에서 생성되는 파일은 다음 Directory에 저장합니다.

    SW/Jetson/preprocessing/lower/outputs/

해당 Directory에는 다음과 같은 Runtime Generated Artifact가 저장될 수 있습니다.

- Empty-board Baseline Image
- 실행 결과 Image
- Dataset
- VLA Training Record
- Debug 및 Intermediate Output

이 Directory는 `.gitignore`에 등록되어 GitHub 제출 Source에는 포함되지 않습니다.

Python Cache 역시 다음 규칙을 통해 제외합니다.

    __pycache__/
    *.py[cod]

---

## 16. Source Integrity 주의사항

하의 Runtime은 여러 Source 파일을 Runtime에서 동적으로 연결하는 구조를 사용합니다.

따라서 다음 사항에 주의해야 합니다.

- 검증된 Python Source 파일명을 임의로 변경하지 않습니다.
- Source Directory 구조를 임의로 변경하지 않습니다.
- 자동 Formatter를 이용해 전체 Source를 일괄 변경하지 않습니다.
- Dynamic Source Load를 임의로 일반 Import 구조로 변경하지 않습니다.
- Lower 전용 Homography와 Common Homography를 통합하지 않습니다.
- D25의 Import만 보고 별도의 `step_d23_v2.py`를 임의로 추가하지 않습니다.

GitHub 제출본에서는 코드 중복 최소화보다 **실제 로봇에서 검증된 Runtime의 재현성 및 Dependency 보존을 우선**합니다.

---

## 17. 검증 환경

최종 Runtime 검증 환경:

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

## 18. 제출본 검증 결과

현재 GitHub 로컬 제출본 기준으로 다음 검사를 통과했습니다.

    run_lower.py --paths-only
    PASS=19 FAIL=0

    Python py_compile
    PASS=13 FAIL=0

    Authoritative SHA-256
    PASS=19 FAIL=0

    Static Dependency Validator
    PASS=37 FAIL=0

이를 통해 제출본의 주요 Source, Model, Calibration 및 Dynamic Dependency 구조가 원본 Runtime과 일치하는지 검증했습니다.

---

## 19. 요약

하의 처리 시스템은 다음 기술을 결합합니다.

- TensorRT 기반 Garment Segmentation
- Bottom Pose Estimation
- Mask 및 Contour Geometry 분석
- Wrinkle / Fold 분석
- Camera Undistortion
- Homography 기반 좌표 변환
- Folding Board 및 Robot Calibration
- Dual RoArm M2-S Manipulation
- Semantic Action Planning
- Frozen Plan 승인 및 실행

최종적으로 본 시스템은 **사용자가 상위 Semantic Action을 선택하고, 시스템이 자동으로 의류를 인식하고 동작을 계획한 뒤 사용자의 승인에 따라 실제 로봇 동작을 수행하는 Human-in-the-loop Semi-Automatic Manipulation System**으로 구성되어 있습니다.

---

## 20. 현재 개발 단계 및 향후 VLA 기반 자동화 계획

현재 하의 Manipulation Runtime은 최종 완전 자동화 단계가 아니라, **VLA(Vision-Language-Action) 기반 자동 조작 정책을 개발하기 위한 데이터 수집 및 검증 단계**에 있습니다.

현재 시스템에서는 카메라로 하의 상태를 인식한 뒤, 사용자가 현재 의류 상태에 적절한 Semantic Action을 숫자 Key로 선택합니다.

현재 사용되는 주요 Action은 다음과 같습니다.

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

이 구조에서 사용자가 직접 Action을 선택하는 이유는 최종 시스템을 수동으로 운용하기 위한 것이 아니라, **의류의 시각적 상태와 그 상태에서 적절한 조작 Action 사이의 관계를 데이터로 수집하기 위해서입니다.**

현재 Data Collection 과정은 개념적으로 다음과 같습니다.

    Camera Image
        ↓
    Garment Segmentation / Pose / Geometry 분석
        ↓
    현재 하의 상태 관찰
        ↓
    사용자가 적절한 Semantic Action 선택
        ↓
    Frozen Manipulation Plan 생성
        ↓
    ENTER 승인
        ↓
    Robot Action 실행
        ↓
    실행 결과 평가
        ↓
    VLA 학습용 Data 저장

즉 현재 사용자의 Key 입력은 향후 VLA Model이 학습해야 할 **정답 Action Label 및 조작 의사결정 데이터**를 생성하는 역할을 합니다.

---

### 현재 단계

현재 하의 시스템은 다음 기능까지 구현되어 있습니다.

- Camera 기반 Garment Segmentation
- Bottom Pose Estimation
- Mask / Contour / Geometry 분석
- Waist / Crotch / Leg / Hem 구조 분석
- Fold / Wrinkle 및 Finish State 분석
- Semantic Action별 Robot Manipulation Planning
- Frozen Plan 기반 실행
- Dual RoArm M2-S Physical Manipulation
- Action 실행 결과 Review
- VLA 학습을 위한 Action / Result Data 수집

현재는 사용자가 Semantic Action을 직접 선택하기 때문에 **Human-in-the-loop Semi-Automatic Manipulation System**으로 동작합니다.

---

### 현재 Human-in-the-loop 구조를 사용하는 이유

비정형 의류는 동일한 하의라도 초기 배치 상태, 구김 정도, 접힘 방향, Waist와 Leg의 위치 등에 따라 다음에 수행해야 하는 조작이 달라집니다.

예를 들어 어떤 상태에서는 `OUTER_PULL`이 필요하지만, 다른 상태에서는 `POSITION_ADJUST`, `ALIGN`, `PRESS_SWEEP` 또는 `WAIST_PULL_LAYDOWN`이 먼저 필요할 수 있습니다.

따라서 현재 단계에서는 사람이 의류 상태를 확인하고 적절한 Semantic Action을 선택함으로써 다음 관계를 반복적으로 수집합니다.

    현재 Garment State
            ↓
    적절한 Semantic Action
            ↓
    실제 Robot Execution
            ↓
    Action Result

이러한 데이터를 축적하여 향후 VLA Model이 **현재 사람이 수행하는 상위 Action Selection을 학습하도록 하는 것**이 현재 Data Collection의 목적입니다.

---

### 향후 개선 방향

향후에는 충분한 VLA 학습 데이터를 확보한 뒤 현재 사용자가 수행하는 Semantic Action 선택 과정을 AI Model로 대체할 예정입니다.

목표 구조는 다음과 같습니다.

    Camera Input
        ↓
    Garment Perception
        ↓
    Garment State Representation
        ↓
    VLA-based Action Decision
        ↓
    Semantic Action 자동 선택
        ↓
    Manipulation Planning
        ↓
    Robot Execution
        ↓
    새로운 Garment State 관찰
        ↓
    다음 Action 자동 결정

현재 사용자가 입력하는 `1 ~ 8` Semantic Action Key는 향후 VLA Model의 Action Decision Output으로 대체하는 것을 목표로 합니다.

이를 통해 사람이 매 단계마다 의류 상태를 확인하고 Action Key를 입력하지 않아도 시스템이 스스로 현재 하의 상태를 판단하여 다음 조작을 선택할 수 있도록 확장할 예정입니다.

---

### 최종 목표

하의 Pipeline의 최종 목표는 현재의:

    Perception
        ↓
    사용자 Semantic Action 선택
        ↓
    Planning
        ↓
    Execution

구조를 다음과 같이 발전시키는 것입니다.

    Perception
        ↓
    VLA 기반 Garment State 판단
        ↓
    Semantic Action 자동 결정
        ↓
    Manipulation Planning
        ↓
    Robot Execution
        ↓
    State Re-observation
        ↓
    다음 Action 자동 결정

즉, 현재 Human-in-the-loop Runtime은 **최종 자동화 시스템을 구축하기 위한 VLA Data Collection 및 Robot Action 검증 단계**이며, 최종적으로는 사용자의 Semantic Action Key 입력을 제거하여 하의의 상태 판단부터 Action 선택 및 Robot Manipulation까지 연속적으로 수행하는 자동화 Pipeline을 구현하는 것을 목표로 합니다.

다만 실제 Robot Manipulation의 특성상 최종 자동화 단계에서도 Workspace Safety, Robot Reachability 및 Emergency Stop과 같은 Physical Safety Constraint는 독립적으로 유지할 예정입니다.

---

## 21. Clean Docker GitHub-only 재현성 검증

하의 제출 Runtime은 기존 개발 Directory가 보이지 않는 조건에서도 Repository Dependency가 완결되는지 추가 검증했습니다.

검증에는 실제 Runtime과 동일한 Docker Image인

    roarm_dual_working_20260814:latest

를 사용했습니다.

Clean Container 조건은 다음과 같습니다.

- `/workspace/project_train`을 빈 Read-only Directory로 대체
- 해당 Directory 내부 File Count = 0
- `PYTHONPATH`에 기존 개발 Directory 없음
- `/dev/roarm_1` 미전달
- `/dev/roarm_2` 미전달
- `/dev/ttyACM0` 미전달
- `/dev/video0`만 전달
- NVIDIA Runtime 사용
- GitHub Repository를 Container 내부에 Fresh Clone

GitHub Fresh Clone 상태에서 다음 검증을 통과했습니다.

    Dependency Check          : PASS 19 / 19
    Lower Homography          : PASS
    Camera Open               : PASS
    Camera Control            : PASS
    Camera Undistortion       : PASS
    Segmentation TensorRT     : PASS
    Bottom Pose TensorRT      : PASS
    TensorRT Warm-up          : PASS
    Bottom VLA Runtime        : PASS

실제 실행 로그에서 Runtime Source, Model 및 Calibration은 모두 Fresh Clone Repository 내부의 경로를 사용했습니다.

이를 통해 하의 Main Runtime의 Source, Model 및 Calibration Dependency가 기존 `/workspace/project_train` 개발 Directory 없이 GitHub Repository 내부에서 완결됨을 확인했습니다.

본 Clean Docker Test에서는 Robot Device 자체를 Container에 전달하지 않았으므로 실제 Physical Robot Motion은 검증 범위에 포함하지 않았습니다.
