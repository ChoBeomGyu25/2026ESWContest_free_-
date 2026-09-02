# Software

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**을 구성하는 전체 Software를 관리합니다.

본 시스템은 NVIDIA Jetson Orin Nano 기반의 Vision AI 및 Dual Robot Manipulation, Folding Board 제어, 사용자 Interface를 결합하여 비정형 의류를 인식하고 펼치고 정렬한 뒤 최종적으로 Folding Board를 이용해 접는 것을 목표로 합니다.

의류는 동일한 종류라도 초기 위치, 회전, 구김, 접힘 형태가 매번 달라지기 때문에 단순한 고정 Sequence만으로 전체 작업을 안정적으로 수행하기 어렵습니다.

따라서 「접신」은 다음과 같은 반복적인 구조를 지향합니다.

    Camera Observation
            ↓
    Garment Perception
            ↓
    Garment State Analysis
            ↓
    Action Decision
            ↓
    Dual Robotic Arms Manipulation
            ↓
    New Camera Observation
            ↓
    State Re-evaluation
            ↓
    Folding-ready 판단
            ↓
    Folding Board

---

# 1. 디렉터리 구성

    SW/
    ├── README.md
    │
    ├── Jetson/
    │   ├── README.md
    │   ├── preprocessing/
    │   │   ├── upper/
    │   │   └── lower/
    │   ├── common/
    │   ├── models/
    │   ├── policy/
    │   └── runtime/
    │
    ├── Arduino/
    │
    └── App/

---

# 2. Jetson Software

`Jetson/`은 「접신」의 핵심 연산 및 Robot Manipulation Software를 관리합니다.

NVIDIA Jetson Orin Nano에서 다음 기능을 수행합니다.

- ELP OV2710 Camera 영상 입력
- Camera Undistortion
- Garment Segmentation
- Upper / Lower Pose Estimation
- Garment Mask 및 Contour 분석
- Keypoint / Landmark 분석
- Garment Geometry 계산
- Folding Board 기준 좌표 변환
- Robot Grasp Point 계산
- Manipulation Planning
- Dual Robotic Arms 제어
- 조작 후 Garment State 재관찰
- 향후 학습 기반 Action Decision 및 종료조건 판단

상의와 하의는 의류 구조와 조작 방식이 서로 다르기 때문에 각각 별도의 Runtime 구조를 유지합니다.

---

# 3. 현재 구현 상태

현재 GitHub 제출본은 **상의와 하의의 개발 단계가 서로 다릅니다.**

따라서 현재 구현된 기능과 향후 자동화 목표를 구분하여 설명합니다.

---

## 3.1 상의 현재 Runtime

상의는 현재 다음 Main Manipulation Pipeline이 구현되어 있습니다.

    Basket Grasp
        ↓
    Folding Board 위 이동 및 배치
        ↓
    Garment Reposition
        ↓
    Segmentation + Upper Pose Estimation
        ↓
    Grasp Point 결정
        ↓
    Dual Robotic Arms Grasp
        ↓
    Aerial Lift / Alignment
        ↓
    Laydown
        ↓
    Standby Return

현재 검증된 상의 Repository Runtime은 다음 위치에 있습니다.

    SW/Jetson/preprocessing/upper/

Repository-Relative Entry Point:

    SW/Jetson/preprocessing/upper/run_upper.py

Dependency 확인:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --paths-only

실제 Robot Sequence:

    python3 SW/Jetson/preprocessing/upper/run_upper.py --physical-auto

현재 GitHub에는 위 Main Runtime과 이를 실행하는 데 필요한 Model, Calibration 및 Dependency가 포함되어 있습니다.

---

## 3.2 상의 향후 자동화 계획

현재 상의 Main Runtime 이후에는 **학습 모델 기반의 의류 상태 판단 및 추가 조작 단계**를 연결할 예정입니다.

이 후속 단계의 목표는 의류가 보드 위에 Laydown된 이후 현재 상태를 다시 관찰하고 다음과 같은 조작의 필요 여부를 AI가 스스로 판단하는 것입니다.

예시:

- 주름 펼침
- 의류의 접힘 제거
- 의류 위치 수정
- 의류 중심 정렬
- 방향 보정
- 추가 Pull / Reposition
- 추가 의류 조작 필요 여부 판단
- 작업 종료조건 판단

향후 상의 Pipeline은 다음과 같은 Closed-loop 구조로 확장할 예정입니다.

    Current Upper Main Runtime
            ↓
    Laydown 완료
            ↓
    New Camera Observation
            ↓
    Learned Garment-State Model
            ↓
    필요한 추가 Action 판단
            ↓
    Wrinkle Unfold / Position Adjust / Alignment
            ↓
    Re-observation
            ↓
    추가 조작 필요 여부 판단
            ↓
    Folding-ready 종료조건 판단

최종적으로 학습 기반 Policy가 **“현재 상의 상태가 충분히 펴지고 정렬되어 더 이상의 Robot Manipulation이 필요하지 않으며 Folding Board로 접는 단계에 진입해도 된다”**는 종료조건까지 판단하도록 구현하는 것이 목표입니다.

현재 이 후속 학습 기반 Module은 개발 중이며, 현재 GitHub의 Upper Main Runtime과 구분하여 향후 추가할 예정입니다.

---

# 4. 하의 현재 Runtime

하의는 현재 **VLA(Vision-Language-Action) 기반 자동 Action Policy 개발을 위한 Human-in-the-loop Data Collection 단계**입니다.

현재 하의 Runtime에서는 Camera와 AI Model이 의류를 인식하고 Manipulation Plan을 생성하지만, 다음에 수행할 상위 Semantic Action은 사용자가 Key를 통해 선택합니다.

현재 Semantic Action:

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

현재 하의 기본 흐름:

    Camera Observation
            ↓
    Segmentation / Bottom Pose
            ↓
    Garment State Analysis
            ↓
    사용자 Semantic Action 선택
            ↓
    Automatic Manipulation Planning
            ↓
    Frozen Plan
            ↓
    ENTER 승인
            ↓
    Robot Execution
            ↓
    Result Review
            ↓
    VLA Data 저장

따라서 현재 하의 Runtime은 완전 자율 System이 아니라 **Human-in-the-loop Semi-Automatic Manipulation Runtime**입니다.

Repository Runtime:

    SW/Jetson/preprocessing/lower/

Entry Point:

    SW/Jetson/preprocessing/lower/run_lower.py

Dependency 검사:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --paths-only

실제 Robot Runtime:

    python3 SW/Jetson/preprocessing/lower/run_lower.py --physical

현재 GitHub 제출본의 하의 Runtime은 GitHub에서 새롭게 Fresh Clone한 Repository의 파일만 사용하여 다음 단계까지 검증했습니다.

- Runtime Dependency 확인
- Python Source Compile
- Dynamic Dependency 확인
- Lower-specific Homography 확인
- Camera Open
- Camera Calibration 적용
- Garment Segmentation TensorRT Engine Loading
- Bottom Pose TensorRT Engine Loading
- TensorRT Warm-up
- Bottom VLA Operator Runtime 진입

즉 기존 개발 Directory의 숨겨진 Dependency 없이 GitHub Repository 내부의 Source, Model 및 Calibration을 이용하여 하의 Runtime이 초기화되는 것을 확인했습니다.

---

### Clean Docker 재현성 검증

하의 Runtime은 기존 개발 Directory가 실행을 우연히 보조하는 가능성을 배제하기 위해 별도의 Clean Docker 환경에서도 검증했습니다.

검증 시 `/workspace/project_train`은 File 수가 0인 빈 Read-only Directory로 대체했으며, `/dev/roarm_1`, `/dev/roarm_2`, `/dev/ttyACM0`은 Container에 전달하지 않고 `/dev/video0`과 NVIDIA Runtime만 사용했습니다.

이 상태에서 GitHub Repository를 새로 Clone한 뒤 Dependency 19/19 확인, Camera Open, Camera Calibration, Segmentation / Bottom Pose TensorRT Engine Loading, TensorRT Warm-up 및 Bottom VLA Operator Runtime 진입까지 정상적으로 수행되는 것을 확인했습니다.

따라서 현재 Lower Main Runtime의 Source, Model 및 Calibration Dependency는 기존 개발 Directory가 아닌 GitHub Repository 내부 Artifact를 기준으로 구성되어 있음을 확인했습니다.

# 5. 하의 VLA Data Collection 목적

현재 하의에서 사용자가 Semantic Action을 직접 선택하는 이유는 최종 System을 수동으로 운용하기 위한 것이 아닙니다.

현재 단계의 목적은 다음 관계를 Data로 축적하는 것입니다.

    Current Garment State
            ↓
    Appropriate Semantic Action
            ↓
    Manipulation Execution
            ↓
    Action Result
            ↓
    Next Garment State

사용자가 선택하는 Semantic Action은 향후 VLA Model이 학습해야 할 Action Decision 정보를 제공합니다.

이를 통해 다양한 초기 배치, 구김, Fold, Waist 방향, Leg 위치 및 Garment Geometry에서 어떤 조작을 수행해야 하는지를 학습하기 위한 Dataset을 구축합니다.

---

# 6. 하의 향후 VLA 기반 자동화 계획

충분한 VLA Data를 확보한 이후에는 현재 사람이 수행하는 Semantic Action 선택을 학습 Model로 대체하는 것을 목표로 합니다.

현재 구조:

    Perception
        ↓
    사용자 Action 선택
        ↓
    Planning
        ↓
    Robot Execution

향후 구조:

    Perception
        ↓
    VLA-based State Understanding
        ↓
    Semantic Action 자동 선택
        ↓
    Manipulation Planning
        ↓
    Robot Execution
        ↓
    New Observation
        ↓
    다음 Action 자동 선택

즉 현재 사람이 누르는 `1 ~ 8` Key 입력을 VLA Policy의 Action Output으로 대체할 예정입니다.

VLA Model은 Robot Manipulation 후 새롭게 관찰된 하의 상태를 다시 분석하여 다음 Action을 선택하는 Closed-loop 구조로 확장됩니다.

---

# 7. 하의 최종 종료조건 목표

하의 역시 단순히 Action을 자동 선택하는 것에서 끝나는 것이 아니라 **언제 Robot Manipulation을 종료해야 하는지 판단하는 것**까지 자동화하는 것이 목표입니다.

최종적으로 다음과 같은 상태를 AI가 판단합니다.

- 하의가 충분히 펼쳐졌는가
- 큰 Fold가 제거되었는가
- Waist 및 Leg 구조가 정상적으로 배치되었는가
- Garment Center가 적절한 위치에 있는가
- Folding Board 기준 방향이 충분히 정렬되었는가
- 추가 Manipulation이 실제로 필요한가
- 현재 상태에서 Folding Board를 동작시켜도 되는가

최종 Lower Pipeline:

    Camera Observation
            ↓
    Garment State Analysis
            ↓
    VLA Action Decision
            ↓
    Manipulation
            ↓
    Re-observation
            ↓
    VLA Re-decision
            ↓
        ┌───────────────┐
        │ 추가 조작 필요 │
        └───────┬───────┘
                │ YES
                └────→ Manipulation 반복

                │ NO
                ↓
        Folding-ready
                ↓
        Folding Board

---

# 8. 상의와 하의의 최종 통합 목표

현재 상의와 하의는 서로 다른 개발 단계에 있지만 최종적으로 동일한 상위 구조를 지향합니다.

    Garment Input
        ↓
    Upper / Lower Perception
        ↓
    Garment State Understanding
        ↓
    Learned Action Policy
        ↓
    Dual RoArm Manipulation
        ↓
    Re-observation
        ↓
    Additional Action Decision
        ↓
    Termination Condition
        ↓
    Folding Board
        ↓
    Folded Garment

즉 최종 목표는 사람이 각 Manipulation 단계를 직접 지정하지 않아도 System이 의류의 현재 상태를 반복적으로 관찰하면서 필요한 조작을 선택하고 수행한 뒤 **의류가 Folding 가능한 상태가 되었는지를 스스로 판단하는 End-to-End Closed-loop Garment Manipulation System**을 구현하는 것입니다.

---

# 9. Preprocessing

`Jetson/preprocessing/`은 상의와 하의의 실제 Vision 및 Manipulation Runtime을 포함합니다.

    SW/Jetson/preprocessing/
    ├── upper/
    └── lower/

주요 기능:

- Garment Segmentation
- Upper / Lower Pose Estimation
- Mask / Contour Geometry
- Landmark Analysis
- Grasp Point 계산
- Garment Manipulation Planning
- Robot Action Runtime

자세한 내용:

    SW/Jetson/preprocessing/README.md
    SW/Jetson/preprocessing/upper/README.md
    SW/Jetson/preprocessing/lower/README.md

---

# 10. Models

`Jetson/models/`은 Jetson Runtime에서 사용하는 TensorRT AI Model을 관리합니다.

현재 제출 Model:

    SW/Jetson/models/
    ├── segmentation/
    │   └── kfashion_yolo26s_seg3_e100_best.engine
    │
    └── pose/
        ├── upper/
        │   └── tshirt_pose_yolo26m_synth_artf_board_v1_best.engine
        │
        └── lower/
            └── bottom_pose8_beige_finetune_v2_best.engine

현재 Repository에는 실제 Runtime에서 사용하는 Segmentation 및 Pose Model을 포함합니다.

향후 Upper Learned Manipulation Policy 및 Lower VLA Policy에 사용되는 학습 Model은 개발 및 검증 완료 후 추가할 예정입니다.

---

# 11. Common

`Jetson/common/`은 Camera와 Robot Workspace 사이의 Coordinate Transformation에 필요한 공통 Resource를 관리합니다.

주요 Resource:

- Camera Undistortion
- Camera Intrinsic Calibration
- Folding Board / Dual RoArm Configuration
- Basket ARM2 Affine Calibration
- Folding Board Homography

주의:

상의/Common Homography와 하의 전용 Homography는 이름은 같지만 Runtime Geometry 요구사항이 서로 다르므로 각각의 검증된 위치에 유지합니다.

자세한 내용:

    SW/Jetson/common/README.md

---

# 12. Policy

`Jetson/policy/`는 Garment State에서 다음 Manipulation Action을 결정하는 상위 Decision Layer를 설명합니다.

현재 상의의 일부 Action Logic은 검증된 Main Runtime 내부에 포함되어 있으며, 향후 학습 기반 Upper Policy를 추가할 예정입니다.

하의는 현재 Human-in-the-loop 방식으로 VLA 학습 Data를 수집하고 있으며, 향후 VLA Model이 Semantic Action Selection과 Termination Condition 판단을 담당하도록 확장할 예정입니다.

자세한 내용:

    SW/Jetson/policy/README.md

---

# 13. Runtime

`Jetson/runtime/`은 Perception, Policy 및 Hardware Execution을 연결하는 전체 Runtime Architecture를 설명합니다.

실제 검증된 실행 Source는 현재 `preprocessing/upper/` 및 `preprocessing/lower/` 내부의 기존 Runtime 구조를 유지하고 있습니다.

이는 실제 Robot에서 검증된 Dynamic Dependency와 Source Loading 구조를 보존하기 위한 것입니다.

자세한 내용:

    SW/Jetson/runtime/README.md

---

# 14. Arduino

`Arduino/`는 Folding Board의 Servo Motor 구동 및 Folding Mechanism 제어와 관련된 Software를 관리합니다.

Jetson에서 Garment Manipulation이 완료되고 Folding-ready 상태가 결정되면 Folding Board 제어 단계와 연동하는 구조를 목표로 합니다.

실제 Source와 세부 실행 방법은 해당 Directory의 파일을 기준으로 확인하십시오.

---

# 15. App

`App/`은 「접신」 시스템과 연동되는 사용자 Application 관련 Software를 관리합니다.

실제 제공 기능과 실행 방법은 해당 Directory의 Source 및 문서를 기준으로 확인하십시오.

---

# 16. 전체 Software 목표

「접신」의 최종 Software 목표는 다음과 같습니다.

1. Camera를 이용하여 비정형 의류 상태를 인식
2. Upper / Lower Garment 종류에 맞는 Perception 수행
3. 현재 Garment State에 적절한 Manipulation Action 판단
4. Dual RoArm M2-S를 이용해 실제 조작 수행
5. 조작 후 Garment State 재관찰
6. 필요한 경우 추가 펼침·정렬·위치 보정 수행
7. AI 기반으로 추가 조작 필요 여부 판단
8. Folding-ready 종료조건 자동 판단
9. Folding Board를 이용하여 의류 접기
10. 다음 Garment Processing 준비

현재 Repository는 이 최종 구조를 향해 단계적으로 개발되고 있으며, **이미 검증된 Runtime과 아직 학습·개발 중인 Future Policy를 명확하게 구분하여 관리합니다.**
