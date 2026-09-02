# 하의 의류 인식 및 완전 자동 조작 Runtime

본 디렉터리는 **2026 임베디드 소프트웨어 경진대회 자유공모** 출품작  
**옷개스트라 - 접신** 프로젝트의 Jetson 기반 **하의 인식·판단·조작 Runtime**을 포함합니다.

현재 제출 Runtime의 최종 실행 파일은 `bottom_vla-38_submission_full_auto.py`입니다.

카메라 영상으로부터 하의 상태를 반복적으로 관찰하고, 현재 상태에 적합한 동작을 자동으로 선택하여 하의가 접을 수 있는 상태가 될 때까지 로봇 조작을 반복합니다.

기존 사용자 개입 방식(Human-in-the-loop)에서 사용자가 직접 다음 동작을 선택하고 승인하던 과정은 현재 제출용 V38 완전 자동 Runtime에서 자동화되었습니다.

---

## 1. 전체 실행 구조

현재 하의 Runtime의 핵심 흐름은 다음과 같습니다.

```text
카메라 영상 입력
    ↓
의류 영역 분할
    ↓
하의 특징점 / 형태 / 주름 / 접힘 분석
    ↓
현재 의류 상태 판단
    ↓
다음 동작 자동 결정
    ↓
고정 동작 계획(Frozen Plan) 생성
    ↓
로봇 동작 실행
    ↓
새 영상 재관찰
    ↓
다음 action 자동 결정
    ↓
FINISH
```

V38은 한 번의 동작만 수행하고 종료되는 구조가 아닙니다.

각 로봇 동작이 끝난 뒤 카메라 영상을 새로 획득하고, 변화된 하의 상태를 다시 분석하여 다음에 필요한 동작을 자동으로 결정합니다.

이 과정을 반복하여 하의가 접을 수 있는 상태에 도달했다고 판단되면 `FINISH` 상태로 종료합니다.

---

## 2. Runtime 실행 파일

GitHub Repository에서는 다음 파일을 통해 하의 Runtime을 실행합니다.

```text
SW/Jetson/preprocessing/lower/run_lower.py
```

실제 완전 자동 Runtime 실행 파일은 다음과 같습니다.

```text
SW/Jetson/preprocessing/lower/dual/undistort/
└── bottom_vla-38_submission_full_auto.py
```

전체 Runtime 연결 구조는 다음과 같습니다.

```text
run_lower.py
    ↓
bottom_vla-38_submission_full_auto.py
    ↓
bottom_vla-23_submission_runtime.py
    ↓
main-33_submission_runtime.py
```

`run_lower.py`는 현재 GitHub Repository의 위치를 기준으로 필요한 Runtime 소스, AI 모델, 카메라 보정 파일 및 로봇 보정 파일의 경로를 계산하여 하위 Runtime에 전달합니다.

이를 통해 개발 과정에서 사용했던 `/workspace/project_train/...` 형태의 절대경로에 직접 의존하지 않고, GitHub Repository 내부의 제출 파일을 이용하여 실행할 수 있도록 구성했습니다.

---

## 3. 하의 Runtime 디렉터리 구조

현재 완전 자동 하의 Runtime의 주요 구조는 다음과 같습니다.

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

하의 Pose 모델은 다음 경로를 사용합니다.

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

V38은 현재 제출용 하의 Runtime의 최상위 Full-Auto Controller입니다.

주요 역할은 다음과 같습니다.

* 완전 자동 작업 시작 및 종료 관리
* 새로운 카메라 영상 획득
* 현재 의류 상태 재판단
* 다음 동작 자동 선택
* 고정 동작 계획(Frozen Plan) 생성 및 실행 관리
* action 완료 후 다음 영상 재관찰
* `FINISH` 상태 관리
* Runtime Source Integrity 유지 확인
* 실제 실행 전 안전 조건 확인

개념적인 실행 흐름은 다음과 같습니다.

```text
BASKET_GRASP
    ↓
POSITION_ADJUST
    ↓
새 영상 획득
    ↓
자동 상태 판단
    ↓
필요한 조작 동작 실행
    ↓
새 영상 획득
    ↓
자동 상태 판단
    ↓
...
    ↓
FINISH
```

초기 `BASKET_GRASP`로 바구니에서 의류를 가져온 뒤에는 `POSITION_ADJUST`를 한 번 수행합니다.

이후부터는 카메라로 하의 상태를 반복적으로 관찰하면서 현재 상태에 필요한 동작을 자동으로 선택합니다.

---

## 5. 제출용 Runtime 기반 코드

### bottom_vla-23_submission_runtime.py

V38이 사용하는 제출용 Runtime 기반 코드입니다.

주요 역할은 다음과 같습니다.

* Main Runtime 소스 탐색
* 각 동작 소스 탐색
* 바구니 보정 파일 탐색
* 동작 종류와 실제 조작 Runtime 연결
* 고정 동작 계획 관리
* 각 동작 Runtime 연결
* 동작 실행 결과 처리
* 자동 동작 준비 및 실행 구조 제공

현재 주요 동작 연결 관계는 다음과 같습니다.

| 동작 종류 | Runtime |
| --- | --- |
| `BASKET_GRASP` | 바구니 파지 Runtime |
| `POSITION_ADJUST` | `58-3.py` |
| `OUTER_PULL` | `54-3.py` |
| `PRESS_SWEEP` | `55-5.py` |
| `WAIST_PULL_LAYDOWN` | `60-15.py` |
| `ALIGN` | `align-11.py` |
| `FINISH` | 작업 종료 상태 |

---

## 6. Main Runtime

### main-33_submission_runtime.py

하의 완전 자동 시스템의 공통 Runtime 기능을 담당합니다.

주요 역할은 다음과 같습니다.

* 카메라 초기화
* 카메라 설정 적용
* 원본 영상 관리
* 왜곡 보정 영상 관리
* TensorRT 의류 영역 분할 모델 불러오기
* TensorRT 하의 Pose 모델 불러오기
* 카메라 보정값 불러오기
* Homography 불러오기
* 로봇 및 폴딩보드 설정 불러오기
* 각 동작 Runtime 소스 동적 연결
* 소스 SHA-256 무결성 확인
* 두 대의 robot arms Runtime 관리

V38 / V23 Runtime에서는 다음 동작 소스를 사용합니다.

```text
D50 → 50-1.py
D54 → 54-3.py
D55 → 55-5.py
D58 → 58-3.py
D56 Slot → 60-15.py
ALIGN → align-11.py
```

특히 `60-15.py`는 Main Runtime의 D56 연결 위치에 적용되어 `WAIST_PULL_LAYDOWN` 동작을 담당합니다.

---

## 7. 주요 동작 모듈

### 50-1.py

`BASKET_GRASP` 동작의 기준 소스입니다.

바구니에서 의류를 가져오는 동작에 필요한 기존 로봇 제어 구조와 보정 정보를 제공합니다.

현재 제출용 완전 자동 Runtime에서는 바구니 파지 동작이 제출용 Runtime 구조에 통합되어 있으며, 본 파일은 소스 의존성 및 무결성 검사 대상으로 함께 유지됩니다.

---

### 54-3.py

`OUTER_PULL` 동작 모듈입니다.

의류 영역과 하의 특징점을 이용하여 의류 외곽의 파지 위치를 계산합니다.

계산된 위치를 두 로봇팔이 파지한 뒤 바깥 방향으로 당겨 하의를 펼치는 동작을 계획하고 실행합니다.

---

### 55-5.py

`PRESS_SWEEP` 동작 모듈입니다.

주름 정보와 의류 형태를 이용하여 주름 또는 접힘 영역을 찾습니다.

검출된 영역을 로봇팔로 누른 상태에서 바깥 방향으로 쓸어 주름이나 접힘을 완화하는 동작을 계획하고 실행합니다.

---

### 58-3.py

`POSITION_ADJUST` 동작 모듈입니다.

하의의 현재 위치와 폴딩보드 작업영역을 분석하여 이후 조작을 수행하기 좋은 위치로 의류를 재배치합니다.

완전 자동 Runtime에서는 `BASKET_GRASP` 이후 `POSITION_ADJUST`를 먼저 수행한 뒤, 새로 촬영한 영상을 이용한 자동 상태 판단 단계로 진입합니다.

---

### 60-15.py

`WAIST_PULL_LAYDOWN` 동작 모듈입니다.

하의 Pose를 이용하여 허리 영역과 두 로봇팔의 파지 위치를 계산합니다.

두 로봇팔로 허리 부분을 파지하여 의류를 펼친 뒤 다시 폴딩보드 위에 내려놓는 동작을 계획하고 실행합니다.

---

### align-11.py

`ALIGN` 동작 모듈입니다.

하의 Pose와 의류 형태를 이용하여 바지 중심축과 기준선 사이의 위치 및 방향 오차를 계산합니다.

계산된 오차를 기준으로 의류를 이동하거나 회전시켜 폴딩보드의 목표 위치에 맞게 정렬합니다.

---

## 8. 하의 인식 모듈

현재 Full-Auto Runtime에서는 다음 세 개의 하의 인식 모듈을 사용합니다.

```text
step_e49_bottom_perception.py
step_e62_bottom_perception.py
step_d25_v2.py
```

이 파일들은 기존에 실제 로봇에서 검증한 동작 Runtime의 연결 구조를 유지하기 위해 함께 사용됩니다.

주요 연결 대상은 다음과 같습니다.

```text
54-3.py
55-5.py
60-15.py
align-11.py
```

각 동작 모듈은 Runtime 실행 중 하의 영역, Pose, 주름 및 형태 분석 결과를 이용하여 실제 파지점과 이동 경로를 계산합니다.

---

## 9. step_e49_bottom_perception.py

하의 영역 분할과 기본적인 형태 분석을 담당하는 인식 모듈입니다.

주요 기능은 다음과 같습니다.

* 의류 영역 분할
* 하의 Mask 선택
* 하의 관찰 정보 생성
* Pose 및 형태 분석을 위한 기본 정보 제공
* Mask 및 하의 구조 분석

대표 Runtime API는 다음과 같습니다.

```text
BottomObservation
infer_bottoms_mask()
parse_class_names()
```

본 모듈은 카메라 영상에서 하의 상태를 분석하는 역할을 담당하며, 로봇에 직접 이동 명령을 보내는 제어 Runtime은 아닙니다.

---

## 10. step_e62_bottom_perception.py

하의 Pose, 주름, 형태 및 허리 영역 분석을 확장한 인식 모듈입니다.

주요 기능은 다음과 같습니다.

* 빛 반사 및 눈부심 영향 완화
* 주름 Heatmap 분석
* 하의 Pose 추론
* Pose 기반 의류 영역 재검출
* 허리 영역 상태 분석
* 동작 판단에 필요한 형태 정보 생성
* 작업 완료 여부 판단 보조

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

기준 영상 없이 현재 하의의 형태와 작업 완료 가능성을 평가하는 인식 모듈입니다.

주요 분석 요소는 다음과 같습니다.

* 허리 구조
* 가랑이의 오목한 형태
* 양쪽 다리 구조
* 밑단 구조
* Pose 특징점
* 외곽선 형태
* 볼록도 변화
* 큰 접힘
* 추가 조작 필요 여부

미세한 주름이나 의류 자체에서 자연스럽게 발생하는 무늬보다 실제로 추가 조작이 필요한 큰 접힘과 구조적인 이상 상태를 중심으로 판단하도록 사용됩니다.

본 모듈 역시 로봇에 직접 이동 명령을 보내는 동작 Runtime이 아니라 의류 상태를 분석하는 역할을 담당합니다.

---

## 12. step_d23_v2 호환 구조

`step_d25_v2.py`는 Runtime 실행 과정에서 `step_d23_v2`라는 이름으로 참조될 수 있습니다.

하지만 최종 제출 Runtime에서는 별도의 `step_d23_v2.py` 파일을 사용하지 않습니다.

동작 모듈이 D25를 불러오기 전에 현재 모듈을 다음과 같이 `step_d23_v2` 이름으로 등록합니다.

```python
sys.modules.setdefault("step_d23_v2", sys.modules[__name__])
```

해당 호환 구조를 사용하는 주요 모듈은 다음과 같습니다.

```text
54-3.py
55-5.py
60-15.py
align-11.py
```

따라서 Import 이름만 보고 별도의 `step_d23_v2.py` 파일을 추가하지 않습니다.

---

## 13. AI 모델

### 의류 영역 분할 모델

```text
SW/Jetson/models/segmentation/
└── kfashion_yolo26s_seg3_e100_best.engine
```

TensorRT 기반 의류 영역 분할 모델입니다.

상의와 하의 Runtime에서 공통으로 사용합니다.

검증된 SHA-256:

```text
ec4b0bcfd6812a0723ad79d00fdc56faef3cd25d1476beee9de4fc9062071725
```

---

### 하의 Pose 모델

```text
SW/Jetson/models/pose/lower/
└── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine
```

V38 완전 자동 하의 Runtime에서 사용하는 Bottom Pose TensorRT Engine입니다.

허리, 가랑이, 양쪽 밑단 등 하의 조작에 필요한 주요 특징점을 검출합니다.

검증된 SHA-256:

```text
d40861c7db06b59bda50016fe2041b8d566d18060ff5f1ab1199d06a1ee7646f
```

기존 하의 Runtime에서 사용하던 이전 Pose Engine 대신 현재 V38 Runtime에서는 위 모델을 사용합니다.

---

## 14. 카메라

사용 카메라:

```text
ELP OV2710
해상도: 1280 × 720
카메라 장치: /dev/video0
```

카메라 설정 파일:

```text
SW/Jetson/preprocessing/lower/dual/
└── elp_ov2710_camera_controls.json
```

현재 제출 Runtime의 카메라 설정에는 다음 값이 포함됩니다.

```text
auto_exposure = 1
exposure_time_absolute = 151
gain = 0
power_line_frequency = 2
white_balance_automatic = 0
white_balance_temperature = 4600
```

카메라 왜곡 보정 코드:

```text
SW/Jetson/preprocessing/lower/dual/undistort/
└── camera_undistort.py
```

현재 `run_lower.py`에서 사용하는 카메라 내부 보정값은 다음 공용 카메라 파일입니다.

```text
SW/Jetson/common/camera/
└── elp_ov2710_1280x720_calibration.npz
```

검증된 SHA-256:

```text
343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6
```

---

## 15. 하의 전용 Homography

완전 자동 하의 Runtime은 다음 하의 전용 Homography 파일을 사용합니다.

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

하의 Runtime은 원본 영상과 왜곡 보정 영상의 좌표계를 구분하여 사용하므로 `raw_H`와 `camera_geometry`가 포함된 하의 전용 Homography가 필요합니다.

검증된 SHA-256:

```text
0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45
```

공용 보정 디렉터리에도 비슷한 이름의 폴딩보드 Homography가 존재하지만 두 파일은 내용과 Runtime 용도가 다릅니다.

따라서 다음과 같은 변경을 수행하면 안 됩니다.

```text
하의 전용 Homography를 공용 Homography 위에 덮어쓰기
공용 Homography를 하의 전용 Homography 위에 덮어쓰기
두 Homography 파일을 하나로 통합
JSON Key 구조를 임의 변경
```

---

## 16. 공용 로봇 / 폴딩보드 보정 파일

현재 하의 Runtime에서 사용하는 공용 보정 파일은 다음과 같습니다.

```text
SW/Jetson/common/calibration/
├── dual_roarm_folding_board_config.json
└── basket_arm2_5point_affine.json
```

로봇 / 폴딩보드 설정 파일 SHA-256:

```text
dual_roarm_folding_board_config.json
807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373
```

바구니 보정 파일 SHA-256:

```text
basket_arm2_5point_affine.json
546dc9c74cc629e407bad4967b9c94d267012e85bd0ef0d86ac5fe73a536d8d8
```

---

## 17. V38 주요 실행 키

현재 V38 완전 자동 Runtime의 주요 키는 다음과 같습니다.

| 키 | 기능 |
| --- | --- |
| `E` | 빈 폴딩보드 기준 영상 획득 |
| `L` | Homography 고정 |
| `X` | 완전 자동 작업 시작 |
| `Q` / `ESC` | 프로그램 종료 / 긴급 중단 |

기존 사용자 개입 Runtime에서 사용했던 숫자 동작 선택 키와 `ENTER` 기반 동작 승인 과정은 현재 V38 제출 Runtime의 기본 운용 방식이 아닙니다.

V38에서는 `X` 입력 이후 완전 자동 작업이 시작되며, 시스템이 새로 획득한 영상을 바탕으로 다음 동작을 자동으로 결정합니다.

---

## 18. 의존성 검사

저장소 최상위 디렉터리에서 다음 명령을 사용합니다.

```bash
cd /workspace/2026ESWContest_free_Otgaestra
```

실제 로봇 또는 카메라 Runtime을 시작하지 않고 제출 파일의 존재 여부 및 SHA-256을 검사합니다.

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
V38 완전 자동 Runtime
V23 제출용 Runtime 기반 코드
Main33 Runtime
50-1.py
54-3.py
55-5.py
58-3.py
60-15.py
align-11.py
E49 하의 인식 모듈
E62 하의 인식 모듈
D25 하의 인식 모듈
카메라 왜곡 보정 코드
카메라 보정값
하의 전용 Homography
카메라 설정
로봇 / 폴딩보드 설정
바구니 보정값
Segmentation TensorRT Engine
Bottom Pose TensorRT Engine
```

---

## 19. Python 소스 검증

현재 완전 자동 Runtime 전체에 대해 Python `py_compile` 검사를 수행했습니다.

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

E49 / E62 인식 모듈의 일반 Python Import도 별도로 검증했습니다.

실제 Import 결과는 다음 `dual/undistort/` 소스로 연결되었습니다.

```text
SW/Jetson/preprocessing/lower/dual/undistort/
├── step_e49_bottom_perception.py
└── step_e62_bottom_perception.py
```

필수 Runtime API 검사 결과:

```text
NORMAL IMPORT/API SUMMARY: FAIL=0
```

---

## 20. 실행 방법

저장소 최상위 디렉터리:

```bash
cd /workspace/2026ESWContest_free_Otgaestra
```

### 의존성 검사

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only
```

이 방식에서는 실제 Runtime을 시작하지 않습니다.

---

### 모의 실행

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --dry-run
```

`run_lower.py`의 기본 실행 방식도 `dry-run`입니다.

---

### 실제 로봇 Runtime

```bash
python3 SW/Jetson/preprocessing/lower/run_lower.py --physical
```

`--physical` 옵션을 사용하면 실제 두 대의 RoArm M2-S를 이용한 의류 조작 Runtime이 활성화됩니다.

---

## 21. 실제 로봇 Runtime 실행 시 주의사항

`--physical` 옵션을 실행하기 전 반드시 다음 항목을 확인해야 합니다.

```text
ARM1 전원 및 연결 상태
ARM2 전원 및 연결 상태
/dev/roarm_1
/dev/roarm_2
카메라 /dev/video0
폴딩보드 작업영역 상태
로봇 이동 경로 내 장애물 여부
사람이 로봇 작업영역 내부에 없는지 여부
비상 전원 차단 가능 여부
카메라 보정 상태
Homography 상태
바구니 보정 상태
```

로봇 포트:

```text
ARM1: /dev/roarm_1
ARM2: /dev/roarm_2
```

또한 `--hover` 방식은 완전히 로봇 명령이 발생하지 않는 Runtime으로 간주하지 않습니다.

하위 Runtime 구조에 따라 `hover` 방식에서도 로봇 명령과 연결될 가능성이 있으므로, 전원이 켜진 로봇 환경에서 단순한 의존성 검증을 위해 사용하지 않습니다.

정적 파일 검증에는 반드시 다음 방식을 권장합니다.

```bash
--paths-only
```

---

## 22. 생성 파일

Runtime 실행 과정에서 사용하는 임시 결과 및 디버그 출력은 가능한 경우 다음 디렉터리에서 관리합니다.

```text
SW/Jetson/preprocessing/lower/outputs/
```

예:

```text
빈 폴딩보드 기준 영상
Runtime 실행 중 생성되는 영상
중간 분석 결과
디버그 출력
```

GitHub 제출본에서는 Runtime 실행 과정에서 생성되는 임시 이미지 및 Python 캐시를 제외합니다.

```text
outputs/
__pycache__/
*.py[cod]
```

---

## 23. Runtime 소스 무결성 주의사항

하의 Runtime은 여러 소스 파일을 실행 중 동적으로 연결합니다.

따라서 다음 사항을 유지해야 합니다.

* 검증된 Python Runtime 파일명을 임의로 변경하지 않습니다.
* Runtime 소스 디렉터리 구조를 임의로 변경하지 않습니다.
* 전체 소스 파일을 자동 정리 도구로 일괄 수정하지 않습니다.
* 동적 소스 연결 구조를 임의로 일반적인 Import 구조로 변경하지 않습니다.
* 하의 전용 Homography와 공용 Homography를 통합하지 않습니다.
* 별도의 `step_d23_v2.py` 파일을 임의로 추가하지 않습니다.
* E49 / E62 / D25 인식 모듈을 지정된 위치에 유지합니다.
* TensorRT Engine 파일을 다른 Pose 모델과 임의 교체하지 않습니다.
* 검증 없이 동작 Runtime 소스 파일의 이름을 변경하지 않습니다.

Main Runtime은 일부 소스 파일에 대해 Runtime 실행 중 소스 무결성을 검사합니다.

소스가 검증된 상태와 다르다고 판단되면 안전을 위해 로봇 동작을 차단할 수 있습니다.

GitHub 제출본에서는 단순히 코드 중복을 줄이는 것보다 **실제 로봇 Runtime의 재현성과 검증된 의존성 구조를 유지하는 것을 우선합니다.**

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

현재 V38 완전 자동 로컬 제출본에서 완료한 검증은 다음과 같습니다.

```text
V38 의존성 SHA / 경로 검사
PASS=20 FAIL=0

하의 전용 Homography 구조 검사
PASS

Python py_compile
PASS=14 FAIL=0

E49 일반 Import
PASS

E62 일반 Import
PASS

필수 Runtime API 검사
FAIL=0
```

이전 사용자 개입 방식의 하의 Runtime에서 수행했던 새 저장소 복제 및 초기 실행 환경 검증 결과는 현재 V38 완전 자동 Runtime의 검증 결과로 간주하지 않습니다.

V38 저장소 기준 재현성 검증은 최종 GitHub 제출 파일을 기준으로 별도로 수행합니다.

---

## 26. 이전 Runtime과의 차이

이전 하의 Runtime은 사용자가 현재 하의 상태를 보고 다음 동작을 직접 선택하는 사용자 개입 방식이었습니다.

기존 방식:

```text
의류 상태 인식
    ↓
사용자가 다음 동작 선택
    ↓
동작 계획 생성
    ↓
사용자 실행 승인
    ↓
로봇 동작 실행
```

현재 V38 완전 자동 Runtime에서는 다음 동작을 선택하는 과정까지 자동화했습니다.

현재 방식:

```text
의류 상태 인식
    ↓
현재 상태 판단
    ↓
다음 동작 자동 결정
    ↓
동작 계획 생성
    ↓
로봇 동작 실행
    ↓
새 영상 재관찰
    ↓
다음 동작 자동 결정
```

따라서 사용자가 각 조작 단계마다 다음 동작을 직접 선택하지 않아도 Runtime이 현재 의류 상태를 분석하여 필요한 동작을 스스로 결정할 수 있습니다.

---

## 27. 최종 구현 범위 및 요약

현재 V38 하의 Runtime은 다음과 같은 폐루프(Closed-loop) 구조를 구현합니다.

```text
카메라 영상 획득
    ↓
의류 상태 인식
    ↓
현재 하의 상태 판단
    ↓
다음 동작 자동 결정
    ↓
동작 계획 생성
    ↓
두 로봇팔을 이용한 조작
    ↓
새 영상 재관찰
    ↓
상태 재평가
    ↓
다음 동작 결정
    ↓
FINISH
```

각 동작의 세부 조작 계획은 기존에 실제 로봇에서 검증한 동작 Runtime을 그대로 활용하면서, 상위 단계에서 현재 의류 상태를 분석하고 다음 동작을 자동으로 선택하도록 구성했습니다.

현재 하의 완전 자동 Runtime은 다음 기술을 결합합니다.

* TensorRT 기반 의류 영역 분할
* Bottom Pose 추론
* Mask 및 외곽선 형태 분석
* 주름 및 접힘 분석
* 기준 영상 없이 수행하는 작업 완료 여부 판단
* 카메라 왜곡 보정
* Homography 기반 좌표 변환
* 폴딩보드 보정
* 바구니 위치 보정
* 두 대의 RoArm M2-S 제어
* 고정 동작 계획(Frozen Plan)
* 다음 동작 자동 결정
* 동작 후 새 영상 재관찰
* 반복적인 상태 재평가
* 자동 `FINISH` 판단

최종 Runtime 실행 흐름은 다음과 같습니다.

```text
의류 상태 인식
    ↓
현재 상태 판단
    ↓
다음 동작 자동 결정
    ↓
동작 계획 생성
    ↓
로봇 동작 실행
    ↓
새 영상 재관찰
    ↓
다음 동작 자동 결정
    ↓
FINISH
```

즉 현재 V38 제출 Runtime은 기존의 수동 동작 선택 방식에서 확장되어, **하의 상태 인식부터 다음 조작 선택, 두 로봇팔을 이용한 실제 의류 조작, 재관찰 및 종료 조건 판단까지 반복적으로 수행하는 완전 자동 하의 정리 Runtime**으로 구성되어 있습니다.
