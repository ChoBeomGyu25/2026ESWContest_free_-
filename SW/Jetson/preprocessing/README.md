# Preprocessing

이 디렉터리는 자동 의류 정리 로봇 시스템 **「접신」**의 카메라 기반 의류 인식, 상태 분석 및 로봇 조작 전처리 소프트웨어를 관리합니다.

카메라로부터 획득한 영상에서 의류 영역과 주요 특징점을 검출하고, 의류의 형상과 현재 상태를 분석하여 Dual RoArm M2-S가 실제 조작에 사용할 수 있는 기하 정보와 동작 계획의 기반 정보를 생성합니다.

현재 GitHub 제출본은 상의와 하의 Pipeline을 각각 독립적인 Runtime 구조로 유지합니다.

---

## 주요 역할

Preprocessing 계층의 주요 역할은 다음과 같습니다.

1. 카메라 영상 입력
2. 의류 Segmentation
3. 의류 Pose Estimation
4. Garment Mask 생성 및 분석
5. 의류 외곽 형상 및 기하 구조 분석
6. 주요 Keypoint 및 Landmark 검출
7. 파지점 후보 생성
8. 의류 정렬 및 변형 상태 분석
9. 영상 좌표와 Calibration 정보를 이용한 Robot Workspace 좌표 계산
10. 의류 상태에 따른 Manipulation Planning 지원
11. 후속 Dual RoArm Manipulation Runtime에 인식 및 기하 정보 전달

---

## 디렉터리 구성

    SW/Jetson/preprocessing/
    ├── README.md
    ├── upper/
    │   ├── README.md
    │   ├── run_upper.py
    │   └── ...
    │
    └── lower/
        ├── README.md
        ├── run_lower.py
        ├── dual/
        │   ├── step_e49_bottom_perception.py
        │   ├── step_e62_bottom_perception.py
        │   ├── step_d25_v2.py
        │   ├── elp_ov2710_camera_controls.json
        │   └── undistort/
        │       ├── bottom_vla-16.py
        │       ├── main-33.py
        │       ├── 50-1.py
        │       ├── 54-3.py
        │       ├── 55-5.py
        │       ├── 58-3.py
        │       ├── 60-13.py
        │       ├── align-11.py
        │       ├── camera_undistort.py
        │       ├── elp_ov2710_1280x720_calibration.npz
        │       └── elp_ov2710_folding_board_homography_cache.json
        │
        └── outputs/

`upper/`와 `lower/`는 실제 로봇에서 검증된 기존 Source Dependency를 보존하기 위해 각각 독립적인 구조를 유지합니다.

단순한 코드 중복 제거를 위해 검증된 파일 구조나 Dynamic Source Loading 구조를 임의로 변경하지 않는 것을 권장합니다.

---

# 1. 공통 Perception 구조

## Segmentation

Segmentation은 영상에서 의류가 차지하는 영역을 Pixel 단위의 Mask로 검출하는 과정입니다.

검출된 Mask는 다음과 같은 정보 계산에 사용됩니다.

- 의류 전체 영역
- Garment Center
- 외곽 Contour
- Bounding Geometry
- 파지 가능한 내부 영역
- 의류 정렬 상태
- Pose 결과와의 기하 관계
- Fold / Wrinkle 분석을 위한 의류 유효 영역

상의와 하의 Runtime은 공용 Garment Segmentation TensorRT Engine을 사용합니다.

    SW/Jetson/models/segmentation/
    └── kfashion_yolo26s_seg3_e100_best.engine

---

## Pose Estimation

Pose Estimation은 의류의 형태를 구성하는 주요 Keypoint를 검출합니다.

상의와 하의는 서로 다른 의류 구조를 가지기 때문에 각각 별도의 Pose TensorRT Engine을 사용합니다.

상의 Pose Model:

    SW/Jetson/models/pose/upper/
    └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine

하의 Pose Model:

    SW/Jetson/models/pose/lower/
    └── bottom_pose8_beige_finetune_v2_best.engine

Pose 결과는 Segmentation Mask 및 Geometry 분석 결과와 결합되어 실제 Robot Grasp 및 Manipulation Planning에 사용됩니다.

---

## Garment Geometry

Segmentation Mask와 Pose Keypoint를 결합하여 의류의 기하 정보를 분석합니다.

주요 분석 정보는 다음과 같습니다.

- Garment Center
- Mask Contour
- 주요 Keypoint 위치
- 의류의 방향
- 외곽과 파지점 사이의 거리
- Garment Principal Axis
- Robot Grasp Candidate
- 두 로봇팔의 파지 간격
- Folding Board 기준 의류 위치
- 의류 정렬 상태
- Fold / Wrinkle 및 변형 상태

이 정보는 단순한 영상 인식 결과에 머무르지 않고 실제 Dual RoArm M2-S의 파지, 이동, 펼침 및 정렬 동작으로 연결됩니다.

---

# 2. 상의 Preprocessing

`upper/` 디렉터리는 상의 의류의 인식, 파지점 결정 및 Dual-Arm 조작에 필요한 최종 Runtime과 Dependency를 포함합니다.

상의 Pipeline의 주요 처리 과정은 다음과 같습니다.

1. 카메라에서 새로운 Frame 획득
2. Segmentation Model을 이용한 Garment Mask 검출
3. Upper Pose Model을 이용한 주요 Keypoint 추론
4. Mask와 Pose 결과를 이용한 의류 형상 분석
5. 의류 중심 및 외곽 구조를 기반으로 파지 후보 계산
6. Keypoint 기반 최종 파지점 결정
7. Calibration 정보를 이용하여 영상 좌표를 Robot Workspace 좌표로 변환
8. Dual RoArm Manipulation 수행

상의는 GitHub Repository 내부 Dependency를 사용하기 위해 다음 Wrapper를 제공합니다.

    SW/Jetson/preprocessing/upper/run_upper.py

Repository Root에서 Dependency 경로 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

실제 자동 Sequence 실행:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

`--physical-auto`는 실제 RoArm M2-S를 동작시키므로 Robot 상태와 주변 작업 공간을 확인한 후 실행해야 합니다.

상의 Runtime의 세부 구조와 실행 방법은 다음 문서를 참고하십시오.

    SW/Jetson/preprocessing/upper/README.md

---

# 3. 하의 Preprocessing

`lower/` 디렉터리는 하의 의류의 Segmentation, Pose, Geometry 분석과 Semantic Action 기반 Manipulation Runtime을 포함합니다.

하의 Pipeline은 완전 자동 Autonomous Pipeline이 아니라 **Human-in-the-loop Semi-Automatic Manipulation 구조**로 구성되어 있습니다.

사용자는 의류 상태에 따라 상위 Semantic Action을 선택하고, 시스템은 해당 Action에 필요한 Perception 및 Planning을 자동으로 수행합니다.

기본 흐름:

    사용자 Action 선택
            ↓
    Perception / Geometry 분석
            ↓
    자동 Manipulation Planning
            ↓
    Frozen Plan 생성
            ↓
    ENTER 사용자 승인
            ↓
    Robot Execution
            ↓
    Result Review

한 번 생성된 Plan은 Frozen 상태로 유지되며, `ENTER` 입력 시 새롭게 재추론하지 않고 승인된 Plan을 실행합니다.

---

## 하의 주요 Runtime

최종 Semantic Action Entry Point:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-16.py

통합 Base Runtime:

    SW/Jetson/preprocessing/lower/dual/undistort/main-33.py

Repository-Relative Wrapper:

    SW/Jetson/preprocessing/lower/run_lower.py

하의 주요 Action Source:

    50-1.py
    54-3.py
    55-5.py
    58-3.py
    60-13.py
    align-11.py

하의 Perception Source:

    step_e49_bottom_perception.py
    step_e62_bottom_perception.py
    step_d25_v2.py

---

## 하의 Semantic Action

`bottom_vla-16.py`에서는 다음 Semantic Action을 선택할 수 있습니다.

| Key | Action |
|---|---|
| `1` | BASKET_GRASP |
| `2` | OUTER_PULL |
| `3` | PRESS_SWEEP |
| `4` | WAIST_PULL_LAYDOWN |
| `5` | ALIGN |
| `6` | FINISH |
| `7` | REJUDGE |
| `8` | POSITION_ADJUST |
| `ENTER` | Frozen Plan 실행 |
| `A / M` | Mask Accurate / Inaccurate |
| `G / B / K` | 실행 결과 분류 |
| `Y / N` | 결과 저장 / 폐기 |
| `E` | Empty-board Baseline |
| `L` | Lock |
| `Q` | 종료 |

---

## 하의 Perception Module

### step_e49_bottom_perception.py

하의의 기본 Perception 및 Geometry 분석을 담당합니다.

주요 기능:

- Garment Segmentation
- Mask Selection
- Glare / Specular Suppression
- Wrinkle Heatmap
- Local Shadow 분석
- Bottom Pose 추론
- TTA / Consensus
- Temporal Stabilization
- Mask Topology
- PCA / Oriented Rectangle
- Crotch Concavity
- Waistband Evidence
- Landmark Reconstruction

---

### step_e62_bottom_perception.py

E49 기반의 하의 상태 판단을 확장합니다.

주요 기능:

- Spread-ready 판단
- Centered-ready 판단
- Axis-parallel-ready 판단
- Termination-ready 판단
- Edge / Near-edge / Interior Wrinkle 분류
- 자연적인 Waistband / Crotch Residual 억제

---

### step_d25_v2.py

Reference-free 방식의 Bottom Finish Evaluator입니다.

주요 평가 요소:

- Waist 구조
- Crotch Concavity
- Two-leg 구조
- Hem 영역
- Pose + Geometry Landmark
- Convexity Defect
- Contour 변화
- Macro Fold

Fine Wrinkle이나 의류 고유 Seam 구조가 불필요하게 FINISH 판정을 방해하지 않도록 하면서 실제 조작이 필요한 큰 Fold를 중심으로 평가합니다.

---

## step_d23_v2 Compatibility

`step_d25_v2.py`에는 `step_d23_v2` Import가 존재하지만 최종 Integrated Runtime에서는 별도의 `step_d23_v2.py`를 제출하지 않습니다.

다음 Action Module들이 D25를 Load하기 전에 자기 자신을 `step_d23_v2`로 등록합니다.

    sys.modules.setdefault("step_d23_v2", sys.modules[__name__])

해당 구조를 사용하는 Module:

- 54-3.py
- 55-5.py
- 60-13.py
- align-11.py

이 Caller Alias 구조는 최종 하의 Static Dependency Validation에서 확인되었습니다.

---

# 4. Camera 및 Calibration 연동

영상에서 얻은 Pixel 좌표를 Folding Board 및 Robot Workspace 좌표로 연결하기 위해 Camera Calibration과 Homography를 사용합니다.

공용 Dependency:

    SW/Jetson/common/camera/camera_undistort.py
    SW/Jetson/common/camera/elp_ov2710_1280x720_calibration.npz

    SW/Jetson/common/calibration/dual_roarm_folding_board_config.json
    SW/Jetson/common/calibration/basket_arm2_5point_affine.json
    SW/Jetson/common/calibration/elp_ov2710_folding_board_homography_cache.json

---

## 하의 전용 Camera Geometry

하의 Runtime은 추가적으로 다음 Camera Resource를 로컬 Dependency로 사용합니다.

    SW/Jetson/preprocessing/lower/dual/elp_ov2710_camera_controls.json

    SW/Jetson/preprocessing/lower/dual/undistort/
    ├── camera_undistort.py
    ├── elp_ov2710_1280x720_calibration.npz
    └── elp_ov2710_folding_board_homography_cache.json

하의 Runtime은 Raw Frame과 Corrected Frame Geometry를 구분하여 사용합니다.

따라서 하의 전용:

    SW/Jetson/preprocessing/lower/dual/undistort/
    elp_ov2710_folding_board_homography_cache.json

과 공용:

    SW/Jetson/common/calibration/
    elp_ov2710_folding_board_homography_cache.json

은 파일명이 같더라도 내용과 역할이 다릅니다.

**두 Homography 파일은 서로 덮어쓰거나 하나로 통합하면 안 됩니다.**

---

# 5. 하의 Runtime 실행

Repository Root:

    cd /workspace/2026ESWContest_free_-

Dependency 검사:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

현재 GitHub 로컬 제출본의 Dependency Validation 결과:

    PASS=19 FAIL=0 TOTAL=19

기본 Wrapper 실행:

    python3 SW/Jetson/preprocessing/lower/run_lower.py

실제 Physical Runtime:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

**주의: `--physical`은 실제 Dual RoArm M2-S 동작을 활성화합니다.**

실제 실행 전에는 Robot 전원, Serial Port, Camera, Folding Board Calibration 및 작업 공간의 안전 상태를 반드시 확인해야 합니다.

하의 Runtime의 자세한 Dependency와 실행 방법은 다음 문서를 참고하십시오.

    SW/Jetson/preprocessing/lower/README.md

---

# 6. Generated Runtime Artifact

하의 Runtime에서 생성되는 Baseline Image, Dataset, Debug Output 및 기타 Generated Artifact는 다음 위치에 저장합니다.

    SW/Jetson/preprocessing/lower/outputs/

이 Directory는 `.gitignore`를 통해 Git 제출 대상에서 제외합니다.

Python Cache 역시 다음 규칙으로 제외됩니다.

    __pycache__/
    *.py[cod]

---

# 7. 제출본 검증

하의 GitHub 로컬 제출본은 다음 검사를 통과했습니다.

    run_lower.py --paths-only
    PASS=19 FAIL=0

    Python py_compile
    PASS=13 FAIL=0

    Authoritative SHA-256
    PASS=19 FAIL=0

    Static Dependency Validator
    PASS=37 FAIL=0

이를 통해 하의 제출본의 주요 Source, Model, Calibration 및 Dynamic Dependency 구조가 원본 Runtime과 일치하는지 확인했습니다.

---

# 8. Source Integrity 주의사항

일부 Runtime 및 보조 Module은 개발 과정에서 사용된 기존 파일명과 Source Loading 구조를 유지하고 있습니다.

이는 실제 Robot 동작 검증이 완료된 Dependency와 Dynamic Import 구조의 호환성을 보존하기 위한 것입니다.

따라서 다음 작업은 전체 Runtime 재검증 없이 수행하지 않는 것을 권장합니다.

- 검증된 Python 파일명 변경
- Source Directory 재구성
- 핵심 Source 자동 Formatting
- Dynamic Source Loading 구조 변경
- 단순 중복 제거 목적의 Module 통합
- Lower 전용 Homography와 Common Homography 통합
- D25 Import만을 근거로 한 별도 `step_d23_v2.py` 추가

본 GitHub 제출 구조에서는 Source Code 중복 최소화보다 **실제 Robot에서 검증된 Runtime의 재현성과 Dependency 보존을 우선합니다.**

---

# 9. 요약

Preprocessing 계층은 카메라 영상으로부터 다음 정보를 생성합니다.

- Garment Segmentation Mask
- Pose Keypoint
- Garment Geometry
- Contour 및 Landmark
- Grasp Candidate
- Fold / Wrinkle 상태
- Robot Manipulation을 위한 좌표 정보
- 의류 상태 기반 Manipulation Planning 정보

상의와 하의는 동일한 Dual RoArm M2-S 및 Folding Board System에서 동작하지만, 각 의류의 형태와 조작 정책이 서로 다르기 때문에 검증된 Runtime 및 Dependency 구조를 각각 유지합니다.

상의는 자동 의류 인식 및 Dual-Arm 조작 Runtime을 제공하며, 하의는 사용자의 Semantic Action 선택과 Frozen Plan 승인을 결합한 **Human-in-the-loop Semi-Automatic Manipulation Runtime**을 제공합니다.
