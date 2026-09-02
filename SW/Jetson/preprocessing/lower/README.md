# 하의 의류 인식 및 Full-Auto Manipulation Runtime

본 디렉터리는 **2026 임베디드 소프트웨어 경진대회 자유공모** 출품작
**옷개스트라 - 접신** 프로젝트의 Jetson 기반 **하의 인식·판단·조작 Runtime**을 포함합니다.

현재 제출 Runtime의 최종 Entry Point는 `bottom_vla-38_submission_full_auto.py`이며, 카메라 영상으로부터 하의의 상태를 반복적으로 관찰하고 현재 상태에 적합한 Semantic Action을 자동으로 선택하여 Folding 가능한 상태가 될 때까지 Closed-loop Manipulation을 수행하도록 구성되어 있습니다.

기존 Human-in-the-loop Runtime에서 사용하던 사용자의 수동 Semantic Action 선택 단계는 현재 제출용 V38 Full-Auto Runtime에서 자동화되었습니다.

---

## 1. 전체 실행 구조

현재 하의 Runtime의 핵심 흐름은 다음과 같습니다.

```text
Camera Input
    ↓
Garment Segmentation
    ↓
Bottom Pose / Geometry / Wrinkle / Fold 분석
    ↓
현재 Garment State 판단
    ↓
Semantic Action 자동 결정
    ↓
Frozen Manipulation Plan 생성
    ↓
Robot Action 실행
    ↓
Fresh Camera Observation
    ↓
다음 Action 자동 결정
    ↓
FINISH
```

V38은 한 번의 Action만 수행하고 종료되는 구조가 아닙니다.

각 Manipulation 이후 새로운 Camera Observation을 획득하고, 변경된 하의 상태를 다시 분석하여 다음 Action을 자동으로 결정합니다.

이 과정을 반복하여 하의가 Folding 가능한 상태에 도달했다고 판단되면 `FINISH` 상태로 종료합니다.

---

## 2. 실행 Entry Point

GitHub Repository에서는 다음 Wrapper를 통해 하의 Runtime을 실행합니다.

```text
SW/Jetson/preprocessing/lower/run_lower.py
```

실제 Full-Auto Runtime Entry는 다음 파일입니다.

```text
SW/Jetson/preprocessing/lower/dual/undistort/
└── bottom_vla-38_submission_full_auto.py
```

전체 Runtime Entry 구조는 다음과 같습니다.

```text
run_lower.py
    ↓
bottom_vla-38_submission_full_auto.py
    ↓
bottom_vla-23_submission_runtime.py
    ↓
main-33_submission_runtime.py
```

`run_lower.py`는 현재 GitHub Repository의 위치를 기준으로 필요한 Source, Model, Camera Calibration 및 Robot Calibration 파일의 경로를 계산하여 Runtime에 전달합니다.

이를 통해 개발 과정에서 사용했던 `/workspace/project_train/...` 형태의 절대경로에 직접 의존하지 않고 GitHub Repository 내부의 제출 Artifact를 사용할 수 있도록 구성했습니다.

---

## 3. 하의 Runtime 디렉터리 구조

현재 Full-Auto Lower Runtime의 주요 구조는 다음과 같습니다.

```text
lower/
├── README.md
├── run_lower.py
├── outputs/
│
└── dual/
    ├── elp_ov2710_camera_controls.json
    │
    └── undistort/
        ├── bottom_vla-38_submission_full_auto.py
        ├── bottom_vla-23_submission_runtime.py
        ├── main-33_submission_runtime.py
        │
        ├── 50-1.py
        ├── 54-3.py
        ├── 55-5.py
        ├── 58-3.py
        ├── 60-15.py
        ├── align-11.py
        │
        ├── step_e49_bottom_perception.py
        ├── step_e62_bottom_perception.py
        ├── step_d25_v2.py
        │
        ├── camera_undistort.py
        └── elp_ov2710_folding_board_homography_cache.json
```

하의 Pose Model은 다음 경로를 사용합니다.

```text
SW/Jetson/models/pose/lower/
└── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine
```

상의와 하의에서 공통으로 사용하는 Garment Segmentation Model은 다음 경로를 사용합니다.

```text
SW/Jetson/models/segmentation/
└── kfashion_yolo26s_seg3_e100_best.engine
```

---

## 4. Full-Auto Controller

### bottom_vla-38_submission_full_auto.py

V38은 현재 제출용 하의 Pipeline의 최상위 Full-Auto Controller입니다.

주요 역할은 다음과 같습니다.

* Full-Auto Cycle 시작 및 종료 관리
* Fresh Observation 획득
* 현재 Garment State 재판단
* Semantic Action 자동 선택
* Frozen Manipulation Plan 실행 관리
* Action 완료 후 다음 Observation 요청
* FINISH 상태 관리
* Source Integrity 유지
* Runtime Safety Gate 유지

개념적인 실행 흐름은 다음과 같습니다.

```text
BASKET_GRASP
    ↓
POSITION_ADJUST
    ↓
Fresh Observation
    ↓
AUTO-JUDGE
    ↓
필요한 Manipulation Action 실행
    ↓
Fresh Observation
    ↓
AUTO-JUDGE
    ↓
...
    ↓
FINISH
```

초기 Basket에서 의류를 가져온 이후에는 하의의 상태를 반복적으로 관찰하면서 필요한 Manipulation을 자동으로 결정합니다.

---

## 5. Submission Runtime Base

### bottom_vla-23_submission_runtime.py

V38이 사용하는 Submission Runtime Base입니다.

주요 역할은 다음과 같습니다.

* Main Runtime Source Resolution
* Action Source Resolution
* Basket Calibration Resolution
* Semantic Action Mapping
* Frozen Plan 관리
* 개별 Action Runtime 연결
* Action 실행 결과 처리
* Auto Prepare 및 Auto Dispatch 구조 제공

현재 주요 Semantic Action Mapping은 다음과 같습니다.

| Semantic Action      | Runtime              |
| -------------------- | -------------------- |
| `BASKET_GRASP`       | Basket Grasp Runtime |
| `POSITION_ADJUST`    | `58-3.py`            |
| `OUTER_PULL`         | `54-3.py`            |
| `PRESS_SWEEP`        | `55-5.py`            |
| `WAIST_PULL_LAYDOWN` | `60-15.py`           |
| `ALIGN`              | `align-11.py`        |
| `FINISH`             | Finish State         |

---

## 6. Main Runtime

### main-33_submission_runtime.py

하의 Full-Auto 시스템의 Main Runtime입니다.

주요 역할은 다음과 같습니다.

* Camera 초기화
* Camera Control 적용
* Raw Frame 관리
* Corrected Frame 관리
* TensorRT Segmentation Model Loading
* TensorRT Bottom Pose Model Loading
* Camera Calibration Loading
* Homography Loading
* Robot / Folding Board Configuration Loading
* Dynamic Action Source Loading
* Source SHA Integrity 관리
* Dual RoArm Runtime 관리

V38 / V23 Runtime에서는 다음 Action Source를 사용합니다.

```text
D50 → 50-1.py
D54 → 54-3.py
D55 → 55-5.py
D58 → 58-3.py
D56 Slot → 60-15.py
ALIGN → align-11.py
```

특히 `60-15.py`는 Main Runtime의 D56 Source Slot에 연결되어 `WAIST_PULL_LAYDOWN` 계열 Manipulation을 담당합니다.

---

## 7. 주요 Action Module

### 50-1.py

Basket 관련 Robot Runtime Source입니다.

Main Runtime 초기화 과정에서 Source Dependency 및 Integrity 검사 대상으로 사용됩니다.

---

### 54-3.py

`OUTER_PULL` Manipulation Runtime입니다.

Garment Mask, Bottom Pose 및 Corrected Camera Geometry를 기반으로 하의 외곽을 조정하기 위한 Manipulation Plan을 생성하고 실행합니다.

---

### 55-5.py

`PRESS_SWEEP` Manipulation Runtime입니다.

Wrinkle 및 Garment Geometry를 이용하여 하의 영역을 누르고 펼치는 동작을 계획합니다.

---

### 58-3.py

`POSITION_ADJUST` Manipulation Runtime입니다.

하의의 현재 위치와 Folding Board Workspace를 분석하여 다음 조작을 수행하기 좋은 위치로 의류를 재배치합니다.

V38 Full-Auto Cycle에서는 초기 Basket Grasp 이후 Position Adjust를 수행하고 이후 Fresh Observation 기반 자동 판단 단계로 진입합니다.

---

### 60-15.py

`WAIST_PULL_LAYDOWN` Manipulation Runtime입니다.

Waistband와 Bottom Pose / Geometry 정보를 이용하여 Waist 영역을 파지하고 이동 및 Laydown하기 위한 동작을 계획합니다.

---

### align-11.py

`ALIGN` Manipulation Runtime입니다.

Bottom Pose와 Garment Geometry를 기반으로 하의의 위치와 방향을 정렬합니다.

---

## 8. Full-Auto Perception Module

현재 Full-Auto Runtime에서는 다음 세 Perception Module을 Action Source와 동일한 `dual/undistort/` 디렉터리에 유지합니다.

```text
step_e49_bottom_perception.py
step_e62_bottom_perception.py
step_d25_v2.py
```

이 배치는 다음 Action Module의 검증된 Runtime Import 구조를 그대로 보존하기 위한 것입니다.

```text
54-3.py
55-5.py
60-15.py
align-11.py
```

해당 Action Module에서는 Runtime 중 다음과 같은 일반 Python Import 구조를 사용합니다.

```python
import step_e49_bottom_perception
import step_e62_bottom_perception
import step_d25_v2
```

따라서 Full-Auto용 Perception Source를 Action Module과 동일한 디렉터리에 유지합니다.

---

## 9. step_e49_bottom_perception.py

하의 Segmentation 및 기본 Perception / Geometry 분석을 담당합니다.

주요 기능은 다음과 같습니다.

* Garment Segmentation
* Garment Mask 선택
* Bottom Observation 생성
* Pose 및 Geometry 분석을 위한 기본 Observation 제공
* Mask 및 하의 구조 분석

대표 Runtime API는 다음과 같습니다.

```text
BottomObservation
infer_bottoms_mask()
parse_class_names()
```

본 Module은 Perception 계층이며 직접 Robot Serial Manipulation을 실행하는 Controller가 아닙니다.

---

## 10. step_e62_bottom_perception.py

하의 Pose, Wrinkle, Geometry 및 Waist 관련 분석을 확장한 Perception Module입니다.

주요 기능은 다음과 같습니다.

* Specular / Glare 억제
* Wrinkle Heatmap 분석
* Bottom Pose 추론
* Pose-guided Segmentation Retry
* Waist 관련 Semantic Evidence
* Manipulation 판단용 Geometry Evidence
* Finish 판단 보조

대표 Runtime API는 다음과 같습니다.

```text
suppress_specular_reflections()
build_wrinkle_heatmap()
infer_bottom_pose()
_e52_pose_guided_segmentation_retry()
evaluate_waist_lift_semantics()
```

---

## 11. step_d25_v2.py

Reference-free 방식의 하의 Geometry 및 Finish Evaluation에 사용되는 Perception Module입니다.

주요 분석 요소는 다음과 같습니다.

* Waist 구조
* Crotch Concavity
* Leg 구조
* Hem 구조
* Pose Landmark
* Contour Geometry
* Convexity 변화
* Macro Fold
* Manipulation 필요 여부

Fine Wrinkle이나 의류 구조 자체에서 자연스럽게 발생하는 Pattern보다 실제로 추가 Manipulation이 필요한 큰 Fold 및 구조적 이상 상태를 중심으로 판단하도록 사용됩니다.

본 Module 역시 Robot Serial Command를 직접 실행하는 Action Controller가 아니라 Perception / Geometry 계층에 해당합니다.

---

## 12. step_d23_v2 Compatibility Alias

`step_d25_v2.py`는 Runtime 중 `step_d23_v2` 이름을 참조할 수 있습니다.

하지만 최종 제출 Runtime에서는 별도의 `step_d23_v2.py` 파일을 사용하지 않습니다.

Action Module이 D25를 Load하기 전에 현재 Module을 다음과 같이 `step_d23_v2` 이름으로 등록합니다.

```python
sys.modules.setdefault("step_d23_v2", sys.modules[__name__])
```

해당 Compatibility 구조를 사용하는 주요 Module은 다음과 같습니다.

```text
54-3.py
55-5.py
60-15.py
align-11.py
```

따라서 단순한 Import 이름만 보고 별도의 `step_d23_v2.py` 파일을 추가하지 않습니다.

---

## 13. AI Model

### Garment Segmentation Model

```text
SW/Jetson/models/segmentation/
└── kfashion_yolo26s_seg3_e100_best.engine
```

TensorRT 기반 Garment Segmentation Model입니다.

상의와 하의 Runtime에서 공통으로 사용합니다.

검증된 SHA-256:

```text
ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725
```

---

### Bottom Pose Model

```text
SW/Jetson/models/pose/lower/
└── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine
```

V38 Full-Auto Lower Runtime에서 사용하는 Bottom Pose TensorRT Engine입니다.

검증된 SHA-256:

```text
d40861c7db06b59bda50016fe2041b8d566d18060ff5f1ab1199d06a1ee7646f
```

기존 Lower Runtime에서 사용하던 이전 Pose Engine 대신 현재 V38 Runtime에서는 위 모델을 사용합니다.

---

## 14. Camera

사용 Camera:

```text
ELP OV2710
Resolution: 1280 × 720
Camera Device: /dev/video0
```

Camera Control 파일:

```text
SW/Jetson/preprocessing/lower/dual/
└── elp_ov2710_camera_controls.json
```

현재 제출 Runtime Camera Control 설정에는 다음 값이 포함됩니다.

```text
auto_exposure = 1
exposure_time_absolute = 151
gain = 0
power_line_frequency = 2
white_balance_automatic = 0
white_balance_temperature = 4600
```

Camera Undistortion Helper:

```text
SW/Jetson/preprocessing/lower/dual/undistort/
└── camera_undistort.py
```

현재 `run_lower.py`에서 사용하는 Camera Intrinsic Calibration은 다음 Common Camera Resource입니다.

```text
SW/Jetson/common/camera/
└── elp_ov2710_1280x720_calibration.npz
```

검증된 SHA-256:

```text
343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6
```

---

## 15. Lower 전용 Homography

Full-Auto Lower Runtime은 다음 Lower 전용 Homography를 사용합니다.

```text
SW/Jetson/preprocessing/lower/dual/undistort/
└── elp_ov2710_folding_board_homography_cache.json
```

해당 파일은 다음 정보를 포함합니다.

```text
H
raw_H
camera_geometry
schema_version
```

Lower Runtime은 Raw Frame과 Corrected Frame Geometry를 구분하여 사용하므로 `raw_H`와 `camera_geometry`가 포함된 Lower 전용 Homography가 필요합니다.

검증된 SHA-256:

```text
0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45
```

Common Calibration Directory에도 비슷한 이름의 Folding Board Homography가 존재하지만 두 파일은 내용과 Runtime 용도가 다릅니다.

따라서 다음 작업을 수행하면 안 됩니다.

```text
Lower Homography를 Common Homography 위에 덮어쓰기
Common Homography를 Lower Homography 위에 덮어쓰기
두 Homography를 하나로 통합
JSON Key 구조를 임의 변경
```

---

## 16. 공용 Robot / Folding Board Calibration

현재 Lower Runtime에서 사용하는 공용 Calibration은 다음과 같습니다.

```text
SW/Jetson/common/calibration/
├── dual_roarm_folding_board_config.json
└── basket_arm2_5point_affine.json
```

Board / Robot Configuration SHA-256:

```text
dual_roarm_folding_board_config.json
807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373
```

Basket Calibration SHA-256:

```text
basket_arm2_5point_affine.json
546dc9c74cc629e407bad4967b9c94d267012e85bd0ef0d86ac5fe73a536d8d8
```

---

## 17. V38 주요 실행 Key

현재 V38 Full-Auto UI의 주요 Key는 다음과 같습니다.

| Key         | 기능                      |
| ----------- | ----------------------- |
| `E`         | Empty-board Baseline 획득 |
| `L`         | Homography Lock         |
| `X`         | Full-Auto Cycle 시작      |
| `Q` / `ESC` | 정상 종료                   |

기존 Human-in-the-loop Runtime에서 사용했던 숫자 Semantic Action Key와 `ENTER` 기반 Action 승인 절차는 현재 V38 제출 Runtime의 기본 운용 방식이 아닙니다.

V38에서는 `X` 입력 이후 Full-Auto Cycle이 시작되며, 시스템이 Fresh Observation을 기반으로 다음 Semantic Action을 자동으로 결정합니다.

---

## 18. Dependency 검사

Repository Root에서 다음 명령을 사용합니다.

```bash
cd /workspace/2026ESWContest_free_Otgaestra
```

Robot 또는 Camera Runtime을 시작하지 않고 제출 Artifact의 존재 여부 및 SHA-256을 검사합니다.

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only
```

현재 V38 로컬 제출본에서 확인된 결과는 다음과 같습니다.

```text
PASS=20
FAIL=0
TOTAL=20
```

검사 대상에는 다음 항목이 포함됩니다.

```text
V38 Full-Auto Entry
V23 Submission Runtime
Main33 Submission Runtime
50-1.py
54-3.py
55-5.py
58-3.py
60-15.py
align-11.py
Full-Auto E49
Full-Auto E62
Full-Auto D25
Camera Undistort Helper
Camera Calibration
Lower Homography
Camera Control
Robot / Board Configuration
Basket Calibration
Segmentation TensorRT Engine
Bottom Pose TensorRT Engine
```

---

## 19. Python Source 검증

현재 Full-Auto Runtime Stack에 대해 Python `py_compile` 검사를 수행했습니다.

검증 대상은 다음과 같습니다.

```text
bottom_vla-38_submission_full_auto.py
bottom_vla-23_submission_runtime.py
main-33_submission_runtime.py
50-1.py
54-3.py
55-5.py
58-3.py
60-15.py
align-11.py
step_e49_bottom_perception.py
step_e62_bottom_perception.py
step_d25_v2.py
camera_undistort.py
run_lower.py
```

검증 결과:

```text
PASS=14
FAIL=0
TOTAL=14
```

Full-Auto E49 / E62의 일반 Python Import도 별도로 검증했습니다.

실제 Import 결과는 다음 `dual/undistort/` Source로 Resolve되었습니다.

```text
SW/Jetson/preprocessing/lower/dual/undistort/
├── step_e49_bottom_perception.py
└── step_e62_bottom_perception.py
```

필수 Perception Runtime API 검사 결과:

```text
NORMAL IMPORT/API SUMMARY: FAIL=0
```

---

## 20. 실행 방법

Repository Root:

```bash
cd /workspace/2026ESWContest_free_Otgaestra
```

### Dependency 검사

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only
```

이 Mode에서는 실제 Runtime을 시작하지 않습니다.

---

### Dry-run

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run
```

Wrapper의 기본 Mode 역시 `dry-run`입니다.

---

### Physical Runtime

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --physical
```

`--physical`은 실제 Dual RoArm M2-S Manipulation을 활성화합니다.

---

## 21. Physical Runtime 주의

`--physical` Mode를 실행하기 전 반드시 다음을 확인해야 합니다.

```text
ARM1 전원 및 연결
ARM2 전원 및 연결
/dev/roarm_1
/dev/roarm_2
Camera /dev/video0
Folding Board Workspace
Robot 이동 경로 내 장애물
사람이 Robot Workspace 내부에 없는지 여부
Emergency Power-off 가능 여부
Camera Calibration 상태
Homography 상태
Basket Calibration 상태
```

Robot Port:

```text
ARM1: /dev/roarm_1
ARM2: /dev/roarm_2
```

또한 `--hover` Mode는 완전한 No-motion Mode로 간주하지 않습니다.

Underlying Lower Runtime 구조에서는 `hover` Mode 역시 Robot Command와 연결될 가능성이 있으므로, Powered Robot 환경에서 단순 Dependency 검증을 목적으로 사용하지 않습니다.

정적 Artifact 검사에는 반드시 다음 Mode를 권장합니다.

```bash
--paths-only
```

---

## 22. Generated Output

Runtime 과정에서 생성되는 Artifact는 다음 위치를 사용합니다.

```text
SW/Jetson/preprocessing/lower/outputs/
```

예:

```text
Empty-board Baseline Image
Runtime Image
Intermediate Output
Debug Output
```

Generated Artifact 및 Python Cache는 GitHub 제출 Source에서 제외합니다.

```text
outputs/
__pycache__/
*.py[cod]
```

---

## 23. Source Integrity 주의사항

하의 Runtime은 여러 Source를 Runtime에서 동적으로 연결합니다.

따라서 다음 사항을 유지해야 합니다.

* 검증된 Python Runtime 파일명을 임의로 변경하지 않습니다.
* Runtime Source Directory 구조를 임의 변경하지 않습니다.
* 전체 Source를 자동 Formatter로 일괄 수정하지 않습니다.
* Dynamic Source Loading 구조를 임의로 일반 Import 구조로 변경하지 않습니다.
* Lower 전용 Homography와 Common Homography를 통합하지 않습니다.
* 별도의 `step_d23_v2.py`를 임의로 추가하지 않습니다.
* Full-Auto E49 / E62 / D25를 `dual/undistort/`에 유지합니다.
* TensorRT Engine 파일을 다른 Pose Model과 임의 교체하지 않습니다.
* 검증 없이 Action Source 파일을 새로운 이름으로 변경하지 않습니다.

Main Runtime은 일부 Source에 대해 실행 Session 동안 Source Integrity를 검사하며, Source가 변경되었다고 판단되면 안전을 위해 실행을 차단할 수 있습니다.

GitHub 제출본에서는 단순한 코드 중복 최소화보다 **실제 Robot Runtime의 재현성 및 검증된 Dependency 구조 보존을 우선**합니다.

---

## 24. 검증 환경

현재 제출 Runtime의 개발 및 검증 환경은 다음과 같습니다.

```text
NVIDIA Jetson Orin Nano
Ubuntu 22.04.3
Python 3.10.12
TensorRT 10.7.0
OpenCV 4.11.0
PyTorch 2.10.0
PyTorch CUDA 12.6
NumPy 1.26.4
Ultralytics 8.4.45
XGBoost 3.2.0
Docker 29.7.2
```

---

## 25. 현재 V38 제출본 검증 상태

현재 V38 Full-Auto 로컬 제출본에서 완료한 검증은 다음과 같습니다.

```text
V38 Dependency SHA / Path Check
PASS=20 FAIL=0

Lower Homography Semantic Check
PASS

Python py_compile
PASS=14 FAIL=0

Full-Auto E49 Normal Import
PASS

Full-Auto E62 Normal Import
PASS

Required Perception API Check
FAIL=0
```

구버전 Human-in-the-loop Lower Runtime에서 수행했던 Fresh Clone / Clean Docker 결과는 현재 V38 Full-Auto Runtime의 검증 결과로 간주하지 않습니다.

V38 Repository-only Fresh Clone 및 Clean Docker 재현성 검증은 최종 GitHub 제출 파일을 기준으로 별도로 수행합니다.

---

## 26. 이전 Runtime과의 차이

이전 Lower Runtime은 사용자가 현재 하의 상태를 보고 다음 Semantic Action을 직접 선택하는 Human-in-the-loop 구조였습니다.

이전 개념:

```text
Perception
    ↓
사용자 Semantic Action 선택
    ↓
Planning
    ↓
사용자 승인
    ↓
Execution
```

현재 V38 Full-Auto Runtime은 Semantic Action Decision을 자동화했습니다.

현재 구조:

```text
Perception
    ↓
Garment State 판단
    ↓
Semantic Action 자동 결정
    ↓
Manipulation Planning
    ↓
Robot Execution
    ↓
Fresh Observation
    ↓
다음 Semantic Action 자동 결정
```

따라서 사용자가 Manipulation 단계마다 다음 Action을 직접 선택하지 않아도 Runtime이 현재 의류 상태를 분석하여 다음 동작을 결정할 수 있도록 확장되었습니다.

---

## 27. 최종 목표 및 현재 구현 범위

현재 V38 Runtime은 다음 Closed-loop 구조를 구현합니다.

```text
Camera Observation
    ↓
Perception
    ↓
Garment State Representation
    ↓
Semantic Action Decision
    ↓
Manipulation Planning
    ↓
Dual RoArm Execution
    ↓
Fresh Observation
    ↓
State Re-evaluation
    ↓
다음 Action
    ↓
FINISH
```

각 Action의 세부 Manipulation Planning은 기존에 실제 Robot에서 검증한 Action Runtime을 그대로 활용하면서, 상위 Semantic Action Decision을 Full-Auto Controller에서 수행합니다.

이를 통해 기존 Action Module의 물리 조작 로직을 보존하면서도 하의 전체 작업 흐름을 Closed-loop 방식으로 자동화했습니다.

---

## 28. 요약

현재 Lower Full-Auto Pipeline은 다음 기술을 결합합니다.

* TensorRT 기반 Garment Segmentation
* Bottom Pose Estimation
* Mask / Contour Geometry 분석
* Wrinkle / Fold 분석
* Reference-free Finish Evaluation
* Camera Undistortion
* Homography 기반 Coordinate Transformation
* Folding Board Calibration
* Basket Calibration
* Dual RoArm M2-S Manipulation
* Frozen Manipulation Plan
* Semantic Action Auto Decision
* Fresh State Re-observation
* Closed-loop Manipulation
* Automatic FINISH Decision

최종 구조는 다음과 같습니다.

```text
Perception
    ↓
Garment State 판단
    ↓
Semantic Action 자동 결정
    ↓
Manipulation Planning
    ↓
Robot Execution
    ↓
Fresh Observation
    ↓
다음 Action 자동 결정
    ↓
FINISH
```

즉 현재 V38 제출 Runtime은 기존의 수동 Semantic Action 선택 구조에서 확장되어, **하의 상태 판단부터 다음 조작 선택, Robot Manipulation, 재관찰 및 종료조건 판단까지 반복적으로 수행하는 Full-Auto Closed-loop Lower Manipulation Pipeline**으로 구성되어 있습니다.
