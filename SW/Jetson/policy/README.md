# Garment Manipulation Policy

이 디렉터리는 팀 **옷개스트라**의 자동 의류 정리 로봇 시스템 **「접신」**에서
현재 관찰된 의류 상태를 바탕으로 **다음 Manipulation Action과 작업 종료 여부를 결정하는 Policy 계층**을 설명합니다.

비정형 의류는 강체 물체와 달리 Robot이 한 번 파지하거나 이동할 때마다 형태가 달라집니다.

따라서 미리 정해진 고정 Sequence만 반복하는 방식보다,

    Observation
        ↓
    Garment State Understanding
        ↓
    Action Decision
        ↓
    Robot Manipulation
        ↓
    Re-observation

과 같은 Closed-loop 구조가 필요합니다.

「접신」의 최종 Policy 목표는 단순히 다음 Robot Action 하나를 선택하는 데 그치지 않고,

**현재 의류가 충분히 펼쳐지고 정렬되어 Folding Board를 사용해도 되는 상태인지까지 판단하는 것**입니다.

---

# 1. Policy 계층의 역할

Policy는 Perception 결과와 현재 작업 상태를 입력으로 받아 다음 행동을 결정합니다.

입력으로 활용할 수 있는 정보의 예시는 다음과 같습니다.

- Garment Segmentation Mask
- Garment Pose Keypoint
- Garment Contour
- Garment Center
- Garment Orientation
- Wrinkle / Fold 상태
- Waistband / Hem / Crotch 등의 구조 정보
- 현재 Grasp Candidate
- Folding Board 기준 위치
- Robot Reachability
- 이전 Manipulation Action
- 이전 Action Result
- 현재 작업 단계

Policy가 결정할 수 있는 Action의 예시는 다음과 같습니다.

- Basket Grasp
- Pull
- Press / Sweep
- Wrinkle Unfold
- Position Adjustment
- Alignment
- Rotation
- Re-grasp
- Laydown
- Re-observation
- Rejudge
- Finish
- Folding-ready 판단

---

# 2. 전체 시스템에서의 위치

전체 Software Pipeline에서 Policy는 다음 위치에 있습니다.

    Camera Input
        ↓
    Perception / Preprocessing
        ↓
    Garment State Representation
        ↓
    Policy / Action Decision
        ↓
    Manipulation Planning
        ↓
    Robot Runtime
        ↓
    Dual RoArm M2-S
        ↓
    New Camera Observation

즉 각 계층의 역할은 다음과 같이 구분합니다.

### Perception

현재 의류가 **어떤 상태인지 파악**합니다.

예:

- Garment Mask
- Pose Keypoint
- Orientation
- Fold / Wrinkle
- Landmark
- Geometry

### Policy

현재 상태에서 **무엇을 해야 하는지 결정**합니다.

예:

- Pull
- Reposition
- Unfold
- Align
- Finish

### Planning / Runtime

선택된 Action을 실제 Robot이 수행할 수 있는

- Grasp Point
- Target Position
- Path
- Speed
- Gripper State
- Dual-Arm Motion

등으로 변환하여 실행합니다.

---

# 3. 현재 Upper Policy 상태

현재 GitHub에 포함된 Upper Main Runtime은 다음 위치에 있습니다.

    SW/Jetson/preprocessing/upper/

실행 진입점:

    SW/Jetson/preprocessing/upper/run_upper.py

현재 Upper Main Runtime은 다음과 같은 주요 Manipulation Sequence를 수행합니다.

    Basket Grasp
        ↓
    Board Placement
        ↓
    Reposition
        ↓
    Segmentation + Upper Pose
        ↓
    Final Grasp Selection
        ↓
    Dual-Arm Grasp
        ↓
    Aerial Alignment
        ↓
    Laydown
        ↓
    Standby Return

현재 이 과정에 필요한 일부 Action Decision은
실제 Robot에서 검증된 기존 Runtime Source 내부에 포함되어 있습니다.

따라서 현재 제출본에서는 검증된 Runtime을 단순히 구조적으로 보기 좋게 만들기 위해
Policy Logic만 별도 Source로 강제로 분리하지 않습니다.

이는 Source Text Patch, Dynamic Dependency 및 실제 Robot Motion Sequence의 재현성을 보존하기 위한 것입니다.

---

# 4. 향후 Upper Learned Policy

Upper Main Runtime 이후에는 **학습 Model 기반 Garment State Policy**를 추가할 예정입니다.

Main Runtime이 의류를 Folding Board 위에 배치한 뒤 새로운 Camera Frame을 관찰하고,
현재 상태에서 어떤 추가 Manipulation이 필요한지 학습 Model이 판단하도록 확장합니다.

예상되는 Upper Action은 다음과 같습니다.

- WRINKLE_UNFOLD
- FOLD_CORRECTION
- POSITION_ADJUST
- ALIGN
- PULL
- REPOSITION
- REJUDGE
- FINISH

목표 구조:

    Current Upper Main Runtime
            ↓
    Garment Laydown
            ↓
    Camera Re-observation
            ↓
    Learned Upper State Model
            ↓
    Action Decision
            ↓
    Manipulation
            ↓
    Re-observation
            ↓
    Additional Action Decision

이 과정을 반복하여 의류 상태를 점진적으로 개선합니다.

---

# 5. Upper 종료조건 판단

향후 Upper Policy가 판단해야 할 중요한 Output 중 하나는
단순한 Manipulation Action뿐 아니라 **Termination Condition**입니다.

예를 들어 다음과 같은 상태를 종합적으로 판단할 수 있습니다.

- 상의가 충분히 펼쳐졌는가
- 큰 Fold가 제거되었는가
- 주요 Wrinkle이 추가 Manipulation을 필요로 하는가
- Garment Center가 Folding Board에 적절히 위치하는가
- 의류 Orientation이 적절한가
- Sleeve / Hem 영역이 Folding에 방해되지 않는가
- 추가 Pull 또는 Reposition이 필요한가
- 현재 상태를 더 조작하는 것이 실제로 유효한가

최종적으로 Policy가

    FOLDING_READY = TRUE

를 판단하면 Upper Manipulation 단계를 종료하고 Folding Board 단계로 이동하는 구조를 목표로 합니다.

---

# 6. 현재 Lower Policy 상태

현재 Lower Runtime은 다음 위치에 있습니다.

    SW/Jetson/preprocessing/lower/

Repository-Relative Entry Point:

    SW/Jetson/preprocessing/lower/run_lower.py

현재 Lower Runtime은 **Human-in-the-loop Semi-Automatic Manipulation 방식**입니다.

Perception과 Manipulation Planning은 System이 수행하지만,
상위 Semantic Action은 현재 사용자가 Key 입력으로 결정합니다.

Semantic Action:

    1 : BASKET_GRASP
    2 : OUTER_PULL
    3 : PRESS_SWEEP
    4 : WAIST_PULL_LAYDOWN
    5 : ALIGN
    6 : FINISH
    7 : REJUDGE
    8 : POSITION_ADJUST

현재 구조:

    Camera Observation
        ↓
    Segmentation / Bottom Pose
        ↓
    Garment State Analysis
        ↓
    Human Semantic Action Selection
        ↓
    Manipulation Planning
        ↓
    Frozen Plan
        ↓
    ENTER Approval
        ↓
    Robot Execution
        ↓
    Result Evaluation

따라서 현재 GitHub 제출본의 Lower Runtime을
완전 자율 Action Policy로 표현하지 않습니다.

---

# 7. 현재 Lower VLA Data Collection

현재 Human Action Selection 과정은 최종 System 구조가 아니라
**VLA(Vision-Language-Action) 기반 자동 Action Policy를 학습하기 위한 중간 단계**입니다.

현재 수집하고자 하는 핵심 Mapping은 다음과 같습니다.

    Garment Observation
            +
    Garment State
            ↓
    Semantic Action
            ↓
    Manipulation Result
            ↓
    Next Garment State

즉 사용자가 `1 ~ 8` 중 적절한 Action을 선택하는 과정은
다양한 하의 상태에 대해

**“이 상태에서는 어떤 Action을 수행해야 하는가?”**

라는 Training Label을 생성하는 역할을 합니다.

---

# 8. Lower VLA Policy의 목표

충분한 Dataset을 확보한 뒤에는 현재 사람의 Semantic Action 입력을
학습된 VLA Model의 Action Prediction으로 대체할 예정입니다.

현재:

    Observation
        ↓
    Human Action Selection
        ↓
    Planning
        ↓
    Robot Execution

향후:

    Observation
        ↓
    VLA State Understanding
        ↓
    VLA Semantic Action Prediction
        ↓
    Planning
        ↓
    Robot Execution
        ↓
    New Observation
        ↓
    VLA Re-decision

즉 현재 사람이 수행하는 `1 ~ 8` Key 입력을 제거하고
VLA Model이 동일한 Semantic Action Space에서 Action을 자동으로 선택하는 것을 목표로 합니다.

---

# 9. Lower Semantic Action Space

현재 수집 Data와 향후 VLA Policy가 연결될 주요 Semantic Action은 다음과 같습니다.

## BASKET_GRASP

Basket에 있는 Garment를 파지하여 Folding Board 작업 영역으로 가져오기 위한 Action입니다.

## OUTER_PULL

Garment의 외곽 또는 특정 영역을 당겨 Fold 및 비정상적인 형상을 개선합니다.

## PRESS_SWEEP

Garment 표면 또는 특정 방향으로 Sweep Manipulation을 수행하여 형태를 보정합니다.

## WAIST_PULL_LAYDOWN

Waist 영역을 기준으로 Garment를 파지하고 이동하여 하의의 전체 형상을 안정적으로 Laydown합니다.

## ALIGN

Waist, Leg 및 Garment Orientation을 Folding Board 기준으로 정렬합니다.

## FINISH

현재 Garment State가 목표 상태에 충분히 근접했는지 평가하는 Action입니다.

## REJUDGE

현재 인식 결과 또는 State를 다시 평가합니다.

## POSITION_ADJUST

Garment의 전체 위치가 Folding Board 기준에서 벗어난 경우 위치를 보정합니다.

---

# 10. Lower 종료조건 자동화 목표

향후 VLA Policy는 단순히 Action Selection만 수행하지 않습니다.

다음 상태를 종합적으로 평가하여
추가 Manipulation이 필요한지 판단하는 것을 목표로 합니다.

- Garment가 충분히 펼쳐졌는가
- Waistband가 정상적인 위치와 방향인가
- Crotch 구조가 충분히 안정적으로 보이는가
- 양쪽 Leg가 Folding에 적절한 상태인가
- Hem 위치가 적절한가
- 큰 Fold가 남아 있는가
- Garment Center가 적절한가
- Board Orientation이 적절한가
- 추가 Position Adjustment가 필요한가
- 추가 Alignment가 실제로 필요한가

Policy가 더 이상의 Manipulation이 필요하지 않다고 판단하면

    FOLDING_READY = TRUE

상태로 전환하여 Folding Board 단계로 이동하는 것을 목표로 합니다.

---

# 11. Closed-loop Action Decision

Upper와 Lower 모두 최종적으로 동일한 Closed-loop 구조를 지향합니다.

    Observation
        ↓
    State Understanding
        ↓
    Action Decision
        ↓
    Manipulation
        ↓
    New Observation
        ↓
    State Re-evaluation
        ↓
    Additional Action?
       /             \
     YES             NO
      ↓               ↓
    Repeat       FOLDING_READY
                      ↓
                 Folding Board

이 구조에서는 Robot Manipulation이 한 번 수행될 때마다
의류 상태를 다시 관찰합니다.

따라서 초기 Garment Position이나 구김 형태가 일정하지 않아도
현재 상태를 기준으로 다음 Manipulation을 다시 결정할 수 있습니다.

---

# 12. Rule-based Logic과 Learned Policy

현재 Runtime에는 실제 Robot Safety와 Manipulation Geometry를 담당하는
Rule-based Logic이 다수 포함되어 있습니다.

향후 Learned Policy가 추가되더라도 모든 Rule-based Logic을 제거하는 것이 목표는 아닙니다.

Learned Policy는 주로

**“어떤 Action을 선택할 것인가”**

를 담당하고,

기존 Runtime은

**“선택한 Action을 어떻게 안전하게 수행할 것인가”**

를 담당하는 구조를 유지할 예정입니다.

예:

    Learned Policy
        ↓
    POSITION_ADJUST 선택
        ↓
    Existing Geometry Planner
        ↓
    Reachability / Safety Check
        ↓
    Grasp / Motion Planning
        ↓
    Robot Execution

이와 같이 학습 기반 Decision과 검증된 Robot Geometry / Safety Logic을 분리함으로써
Model의 Action Decision과 실제 Hardware Safety를 독립적으로 관리하는 것을 목표로 합니다.

---

# 13. Safety Layer와 Policy의 분리

Policy가 특정 Action을 선택했다고 해서
Robot이 해당 Action을 무조건 실행하는 구조를 목표로 하지 않습니다.

실제 Hardware Execution 전에는 기존 Runtime의 다음 검사를 유지합니다.

- Robot Reachability
- Workspace Boundary
- Grasp Validity
- Path Geometry
- Dual-Arm Interference
- Motion Limit
- Calibration Validity
- Camera / Coordinate Validity
- Physical Execution Approval

따라서 향후 VLA 또는 Learned Policy가 추가되더라도
Physical Safety Constraint는 Policy와 독립적인 Runtime Layer에서 유지합니다.

---

# 14. Policy와 Planning의 분리

Policy와 Planning은 다음처럼 구분합니다.

### Policy

    현재 State에서 어떤 Semantic Action을 수행할 것인가?

예:

    OUTER_PULL

### Planning

    OUTER_PULL을 실제로 어디를 잡고,
    어느 방향으로,
    얼마만큼 이동할 것인가?

예:

    grasp = (...)
    target = (...)
    pull_distance = (...)
    trajectory = (...)

따라서 향후 학습 Model을 추가하더라도
검증된 기존 Manipulation Planner를 최대한 재사용하는 구조를 목표로 합니다.

---

# 15. 현재 Repository에서의 Policy Source 위치

현재 제출본에서는 Policy Logic 전체가
`SW/Jetson/policy/`에 독립 Python Module 형태로 분리되어 있지 않습니다.

현재 검증된 Action Logic 및 State Transition은 실제 Runtime Source 내부에도 포함되어 있습니다.

Upper Runtime:

    SW/Jetson/preprocessing/upper/

Lower Runtime:

    SW/Jetson/preprocessing/lower/

이는 실제 Robot에서 검증된 Source 및 Dynamic Dependency 구조를
제출 과정에서 임의로 Refactoring하지 않기 위한 선택입니다.

`policy/`는 현재 전체 Decision Architecture와 향후 Learned Policy 확장 방향을 설명하는 역할을 합니다.

---

# 16. 향후 Policy 확장 방향

향후 개발 방향은 다음과 같습니다.

### Upper

1. 현재 Upper Main Runtime 유지
2. Laydown 후 Garment State Dataset 및 학습 Model 활용
3. Wrinkle / Fold / Position 상태 분석
4. Learned Action Selection
5. 필요한 Manipulation 반복
6. Folding-ready 종료조건 자동 판단

### Lower

1. 현재 Human-in-the-loop VLA Data 수집
2. Garment State / Semantic Action / Result Dataset 구축
3. VLA Model 학습
4. Human `1 ~ 8` Action Selection 대체
5. Closed-loop VLA Action Decision
6. Folding-ready 종료조건 자동 판단

---

# 17. 최종 Policy 목표

「접신」의 최종 Policy는 상의와 하의 모두에서 다음 질문에 답할 수 있어야 합니다.

### 1. 지금 옷은 어떤 상태인가?

    STATE

### 2. 지금 어떤 조작이 필요한가?

    ACTION

### 3. 조작 후 상태가 개선되었는가?

    RESULT / NEXT STATE

### 4. 추가 조작이 필요한가?

    CONTINUE / REJUDGE

### 5. 이제 Folding Board로 접어도 되는가?

    FOLDING_READY

최종적으로 다음 구조를 구현하는 것이 목표입니다.

    Perception
        ↓
    State Understanding
        ↓
    Learned Policy
        ↓
    Action
        ↓
    Safe Robot Manipulation
        ↓
    Re-observation
        ↓
    Termination Decision
        ↓
    Folding-ready
        ↓
    Folding Board
