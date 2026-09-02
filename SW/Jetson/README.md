# Jetson 소프트웨어

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서 NVIDIA Jetson Orin Nano를 기반으로 실행되는 **AI 기반 컴퓨터 비전, 의류 상태 분석, 조작 계획 및 듀얼 로봇팔 제어 소프트웨어**를 포함합니다.

Jetson은 상부 ELP OV2710 카메라 영상을 입력받아 의류의 위치와 형상을 인식하고, 카메라 픽셀 좌표를 실제 폴딩 보드 및 로봇 작업공간 좌표로 변환한 뒤 상의와 하의 상태에 맞는 조작 동작을 수행하는 핵심 연산 장치입니다.

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
    │       │       ├── bottom_vla-38_submission_full_auto.py
    │       │       ├── main-33_submission_runtime.py
    │       │       ├── 50-1.py
    │       │       ├── 54-3.py
    │       │       ├── 55-5.py
    │       │       ├── 58-3.py
    │       │       ├── 60-15.py
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
3. YOLO 기반 의류 세그멘테이션
4. 상의 / 하의 포즈 및 특징점 추론
5. 의류 마스크 및 윤곽선 분석
6. 키포인트 / 랜드마크 분석
7. 의류 방향 및 위치 분석
8. 접힘 / 주름 및 의류 형상 분석
9. 카메라 픽셀 좌표를 폴딩 보드 / 로봇 좌표로 변환
10. 로봇 파지점 계산
11. 조작 계획 생성
12. 듀얼 로봇팔 제어
13. 조작 후 새로운 의류 상태 재관찰
14. 학습 모델 기반 다음 조작 동작 결정
15. 접기 준비 완료 종료조건 판단
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

    바구니 의류 파지
            ↓
    폴딩 보드 위 이동
            ↓
    의류 내려놓기
            ↓
    YOLO 세그멘테이션 + YOLO 포즈
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

의류 영상과 세그멘테이션, 포즈, 주름 및 위치 분석 결과를 이용하여 현재 상태를 표현하고, **Board+State v2 커스텀 모델**이 다음 동작을 우선 판단합니다. Jetson에서는 TensorRT 엔진으로 추론합니다.

현재 판단 구조:

    카메라 관찰
            ↓
    세그멘테이션 / 포즈 / 상태 분석
            ↓
    Board+State v2 모델
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
    재관찰
            ↓
    다음 동작 자동 판단

현재 커스텀 모델은 7개 동작 클래스를 학습했으며, 제출용 실행 코드에서는 신뢰도와 margin 조건을 만족한 `CENTER`, `SPREAD`, `ROTATE`, `FINISH` 판단을 우선 직접 사용합니다. 그 외 경우에는 규칙 기반 상태 판단 로직으로 넘어갑니다.

즉, 현재 상의 코드는 **커스텀 모델을 우선 사용하여 동작을 판단하고, 모델 판단을 직접 채택하기 어려운 경우 규칙 기반 상태 판단 로직을 보조 경로로 사용**합니다.

실제 파지점과 이동 경로는 기존 검증된 조작 계획 및 안전 검사 로직을 통해 최종 결정됩니다.

조작이 끝나면 로봇팔이 대기 위치로 복귀한 뒤 새로운 영상을 다시 관찰하고 필요한 동작을 반복합니다. `FINISH`가 선택되면 해당 의류의 자동 조작 루프를 종료합니다.

---

# 6. 현재 하의 실행 코드

현재 하의 실행 코드는 **V38 Full-Auto 구조**로 구성되어 있으며 GitHub 저장소에 포함되어 있습니다.

실행 진입점:

    SW/Jetson/preprocessing/lower/run_lower.py

하의 Full-Auto 상위 실행 코드:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-38_submission_full_auto.py

하위 실행 연결 코드:

    SW/Jetson/preprocessing/lower/dual/undistort/bottom_vla-23_submission_runtime.py
    SW/Jetson/preprocessing/lower/dual/undistort/main-33_submission_runtime.py

주요 인식 및 조작 관련 모듈:

    SW/Jetson/preprocessing/lower/dual/undistort/50-1.py
    SW/Jetson/preprocessing/lower/dual/undistort/54-3.py
    SW/Jetson/preprocessing/lower/dual/undistort/55-5.py
    SW/Jetson/preprocessing/lower/dual/undistort/58-3.py
    SW/Jetson/preprocessing/lower/dual/undistort/60-15.py
    SW/Jetson/preprocessing/lower/dual/undistort/align-11.py
    SW/Jetson/preprocessing/lower/dual/undistort/step_e49_bottom_perception.py
    SW/Jetson/preprocessing/lower/dual/undistort/step_e62_bottom_perception.py
    SW/Jetson/preprocessing/lower/dual/undistort/step_d25_v2.py

현재 하의는 카메라와 AI 모델을 이용하여 의류 상태를 인식한 뒤, 현재 상태에 맞는 의미 동작을 자동으로 선택하고 조작 후 다시 관찰하는 **반복형 자동 조작 구조**를 사용합니다.

주요 의미 동작:

- `BASKET_GRASP`
- `POSITION_ADJUST`
- `OUTER_PULL`
- `PRESS_SWEEP`
- `WAIST_PULL_LAYDOWN`
- `ALIGN`
- `FINISH`

하의 인식에는 의류 세그멘테이션, 하의 포즈, 마스크 기하 정보, 윤곽선, 허리선, 가랑이, 다리와 밑단, 접힘 및 주름, 정렬 상태 등의 정보를 함께 사용합니다.

---

# 7. 하의 자동 동작 판단

V38에서는 기존의 사용자 수동 동작 선택을 중심으로 한 구조에서 벗어나, 현재 관찰된 의류 상태를 기반으로 다음 의미 동작을 자동으로 선택합니다.

기본 판단 흐름:

    카메라 관찰
        ↓
    의류 세그멘테이션 / 하의 포즈 추론
        ↓
    의류 형상 및 상태 분석
        ↓
    AUTO-JUDGE
        ↓
    의미 동작 자동 선택
        ↓
    조작 계획 생성 및 안전 검사
        ↓
    로봇 조작

자동 판단 결과는 기존에 검증된 조작 코드와 연결되어 실제 파지점, 이동 경로 및 로봇 동작을 생성합니다.

즉 인식 및 상태 판단 계층과 실제 로봇 조작 계층을 분리하면서, 상위 자동 판단 결과를 기존 조작 코드에 전달하는 구조입니다.

---

# 8. 하의 Full-Auto 반복 조작 구조

V38 Full-Auto는 한 번의 상태 판단만 수행하는 것이 아니라 조작 후 새로운 상태를 다시 관찰하고 다음 동작을 판단하는 반복 구조를 사용합니다.

전체 흐름:

    X 입력으로 Full-Auto 시작
        ↓
    BASKET_GRASP
        ↓
    POSITION_ADJUST
        ↓
    새로운 의류 상태 관찰
        ↓
    AUTO-JUDGE
        ↓
    의미 동작 자동 선택
        ↓
    로봇 조작
        ↓
    새로운 의류 상태 재관찰
        ↓
    상태 재평가
        ↓
    다음 동작 자동 선택
        ↓
    반복 또는 FINISH

초기 바구니 파지 이후에는 의류를 작업 영역에 배치하고 위치를 보정한 뒤, 매 조작마다 새로운 카메라 관찰 결과를 이용하여 다음 동작을 다시 판단합니다.

이를 통해 이전 조작 이전의 상태를 계속 사용하는 것이 아니라 **조작 결과가 반영된 새로운 의류 상태를 기준으로 다음 행동을 결정**합니다.

---

# 9. 하의 종료조건 판단

하의 자동화는 단순히 정해진 횟수만큼 조작한 뒤 종료하는 방식이 아니라, 현재 의류 상태를 재평가하여 추가 조작이 필요한지 판단합니다.

상태 판단에는 다음과 같은 정보를 활용합니다.

- 의류가 충분히 펼쳐졌는지 여부
- 큰 접힘 및 주름 상태
- 허리선 구조
- 가랑이 및 다리 구조
- 양쪽 밑단 상태
- 의류 중심 위치
- 폴딩 보드 기준 정렬 상태
- 추가 위치 보정 또는 펼침 동작의 필요 여부

자동 판단 결과 추가 조작이 필요하면 다음 의미 동작을 선택하여 반복하고, 접기 단계로 진행할 수 있는 상태라고 판단하면 `FINISH`로 종료합니다.

반복 구조:

    의류 관찰
        ↓
    상태 분석
        ↓
    AUTO-JUDGE
        ↓
    추가 조작 필요?
       /          \
     YES          NO
      ↓            ↓
    동작 선택      FINISH
      ↓
    로봇 조작
      ↓
    재관찰
      ↓
    반복

---

# 10. 상의 / 하의 최종 통합 방향

상의와 하의는 모두 **의류를 관찰하고, 현재 상태를 판단하고, 필요한 동작을 수행한 뒤 다시 관찰하는 폐루프(Closed-loop) 구조**를 지향합니다.

    의류 입력
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
    접기 준비 완료
        ↓
    폴딩 보드

상의는 Board+State v2 학습 모델과 규칙 기반 상태 판단을 결합한 자동 조작 모듈을 사용하며, 하의는 V38 Full-Auto 정책을 통해 의미 동작을 자동 선택하고 재관찰을 반복하는 구조를 사용합니다.

예선 제출에서는 상의와 하의의 각 실행 구조를 독립적으로 관리하며, 이후 전체 시스템에서는 의류 종류에 따라 해당 처리 흐름을 선택한 뒤 최종 폴딩 단계로 연결하는 구조를 목표로 합니다.

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
            └── bottom_pose8_yolo26m_robot_beige_retrain_all_v2.engine

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

`common/`은 카메라 좌표와 실제 폴딩 보드 / 로봇 작업공간을 연결하기 위한 카메라 및 보정 리소스를 포함합니다.

    SW/Jetson/common/
    ├── camera/
    └── calibration/

주요 리소스:

- ELP OV2710 카메라 왜곡 보정
- 카메라 내부 파라미터 보정
- 듀얼 로봇팔 / 폴딩 보드 설정
- 바구니 ARM2 Affine 보정
- 폴딩 보드 Homography

---

## Homography 주의사항

상의 공통 실행 코드와 하의 실행 코드에는 동일한 이름의 Homography 파일이 존재하지만 서로 다른 좌표계 처리 요구사항을 가집니다.

상의 / 공통:

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

하의 전용:

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

하의 버전은 원본 / 보정 프레임 기하 정보를 구분하기 위해 `H`, `raw_H`, `camera_geometry`, `schema_version` 정보를 사용합니다.

따라서 두 Homography 파일을 서로 덮어쓰거나 임의로 하나로 통합하면 안 됩니다.

자세한 내용:

    SW/Jetson/common/README.md
---

# 13. 동작 판단 정책

`policy/`는 의류 상태와 로봇 조작 동작 사이의 상위 판단 구조를 설명합니다.

### 상의

- YOLO 세그멘테이션 / 포즈 기반 의류 상태 인식
- Board+State v2 커스텀 모델 기반 동작 판단
- 학습 모델 판단을 우선 사용하고 필요한 경우 규칙 기반 상태 판단으로 보완
- 기존 조작 계획 및 안전 검사 로직을 이용하여 실제 로봇 동작 생성
- 조작 후 새로운 의류 상태를 재관찰
- 다음 동작을 다시 판단하는 반복 구조
- `FINISH` 판단 시 해당 의류의 자동 조작 종료

### 하의

- V38 Full-Auto 기반 자동 의미 동작 선택
- 바구니 파지 후 `POSITION_ADJUST`를 수행하여 작업 영역의 초기 상태 보정
- 카메라, 세그멘테이션, 하의 포즈 및 형상 분석 결과를 이용한 상태 판단
- `AUTO-JUDGE`를 통한 다음 의미 동작 자동 선택
- 선택된 동작을 기존 검증된 조작 코드와 연결
- 각 조작 이후 새로운 의류 상태를 재관찰
- 재관찰 결과를 이용하여 다음 동작을 반복 판단
- 접기 준비 상태가 충족되면 `FINISH`로 해당 의류 조작 종료

상의와 하의 모두 인식 결과를 한 번만 사용하는 방식이 아니라, **조작 → 재관찰 → 상태 재평가 → 다음 동작 판단**을 반복하는 폐루프 구조를 최종 동작 정책으로 사용합니다.

---

# 14. 실행 구조

「접신」의 실제 실행 구조는 **의류 인식 → 동작 판단 → 로봇 실행 → 재관찰 → 종료 판단**의 흐름으로 구성됩니다.

현재 실제 검증된 소스 코드는 다음 디렉터리에 위치합니다.

상의:

    SW/Jetson/preprocessing/upper/

하의:

    SW/Jetson/preprocessing/lower/

검증된 기존 소스 의존성과 동적 소스 로딩 구조를 유지하기 위해 실행 소스 자체를 `runtime/`로 임의 이동하지 않습니다.

`runtime/` 디렉터리는 전체 실행 구조와 상·하의 실행 관계를 설명하는 계층으로 사용합니다.

---

# 15. 실행 환경

현재 Jetson 실행 검증 환경:

- 주 프로세서: NVIDIA Jetson Orin Nano
- 운영체제: Ubuntu 22.04.3
- Python: 3.10.12
- TensorRT: 10.7.0
- OpenCV: 4.11.0
- NumPy: 1.26.4
- PyTorch: 2.10.0
- CUDA 런타임: 12.6 (PyTorch)
- Ultralytics: 8.4.45
- XGBoost: 3.2.0
- Docker: 29.7.2
- 로봇: Dual RoArm M2-S
- 카메라: ELP OV2710
- 카메라 해상도: 1280 × 720
- 통신: USB 시리얼

로봇 장치:

    ARM1: /dev/roarm_1
    ARM2: /dev/roarm_2

카메라 장치:

    /dev/video0

---

# 16. 최종 목표

Jetson 소프트웨어의 최종 목표는 다음과 같은 **폐루프 자동 의류 조작 시스템**을 구현하는 것입니다.

    카메라
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
    접기 준비 완료
      ↓
    폴딩 보드


