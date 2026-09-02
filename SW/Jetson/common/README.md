# 공통 리소스

이 디렉터리는 자동 의류 정리 로봇 시스템 **「접신」**의 Jetson 실행 환경에서 사용하는 공통 카메라 및 보정 리소스를 관리합니다.

카메라 영상에서 검출한 의류의 위치와 특징점을 실제 폴딩 보드 및 Dual RoArm M2-S 작업 좌표로 연결하기 위해 카메라 보정, Homography, Affine 변환 및 로봇 / 보드 설정을 사용합니다.

다만 실제 제출 실행 환경에서는 재현성과 기존 의존성 구조 보존을 위해 모든 파일을 상의와 하의가 동일한 위치에서 직접 참조하는 것은 아닙니다.

특히 하의 실행 코드는 일부 카메라 리소스와 하의 전용 Homography를 `preprocessing/lower/` 내부에 별도로 유지합니다.

---

# 1. 디렉터리 구성

    SW/Jetson/common/
    ├── README.md
    │
    ├── camera/
    │   ├── camera_undistort.py
    │   ├── elp_ov2710_1280x720_calibration.npz
    │   └── elp_ov2710_camera_controls.json
    │
    └── calibration/
        ├── dual_roarm_folding_board_config.json
        ├── basket_arm2_5point_affine.json
        └── elp_ov2710_folding_board_homography_cache.json

---

# 2. 카메라 리소스

## camera_undistort.py

경로:

    SW/Jetson/common/camera/camera_undistort.py

ELP OV2710 광각 카메라의 렌즈 왜곡을 보정하기 위한 공통 모듈입니다.

카메라 보정 정보를 이용하여 영상 왜곡을 보정하고, 이후 수행되는 세그멘테이션, 포즈 추론 및 기하 계산에서 픽셀 위치의 오차를 줄이는 데 사용합니다.

상의 제출 실행 코드에서는 해당 공통 카메라 모듈을 의존 파일로 사용합니다.

하의 실행 코드에는 동일한 카메라 보정 모듈의 검증된 로컬 복사본이 다음 위치에 존재합니다.

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── camera_undistort.py

하의 로컬 복사본은 공통 버전과 파일 내용이 동일함을 SHA-256으로 검증했지만, 기존 하의 동적 소스 로딩 구조와 실행 재현성을 보존하기 위해 의도적으로 중복 유지합니다.

따라서 단순한 중복 제거를 목적으로 하의 로컬 복사본을 삭제하거나 import 구조를 변경하지 않는 것을 권장합니다.

---

## elp_ov2710_1280x720_calibration.npz

경로:

    SW/Jetson/common/camera/
    └── elp_ov2710_1280x720_calibration.npz

ELP OV2710 카메라의 1280 × 720 해상도 보정 데이터를 저장합니다.

카메라 내부 파라미터와 렌즈 왜곡 보정에 필요한 정보를 포함하며 `camera_undistort.py`와 함께 사용합니다.

현재 제출 실행 코드는 1280 × 720 카메라 입력을 기준으로 구성되어 있습니다.

하의 실행 코드에도 동일한 카메라 보정 NPZ의 검증된 로컬 복사본이 존재합니다.

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_1280x720_calibration.npz

두 파일은 SHA-256 기준으로 동일하지만 하의 실행 코드의 검증된 소스 구조를 유지하기 위해 로컬 복사본을 보존합니다.

---

## elp_ov2710_camera_controls.json

경로:

    SW/Jetson/common/camera/
    └── elp_ov2710_camera_controls.json

ELP OV2710 카메라의 촬영 조건을 실행 환경에서 동일하게 재현하기 위한 **V4L2 카메라 제어 설정 파일**입니다.

이 파일은 카메라 내부 파라미터나 렌즈 왜곡 정보를 저장하는 보정 파일이 아니라, `/dev/video0`에 적용할 노출, 게인, 전원 주파수 및 화이트밸런스 값을 저장합니다.

현재 저장된 설정:

    auto_exposure: 1
    exposure_time_absolute: 151
    gain: 0
    power_line_frequency: 2
    white_balance_automatic: 0
    white_balance_temperature: 4600

상의 신규 자동화 실행기:

    SW/Jetson/preprocessing/upper/automation/run_upper_automation.py

는 실행 시 이 파일을 `--camera-controls-json` 인자로 전달합니다.

상의 자동화 코드에서는 카메라 초기화 과정에서 해당 설정을 `/dev/video0`에 적용한 뒤 카메라 보정, 세그멘테이션, 포즈 추론 및 의류 상태 판단을 수행합니다.

따라서 이 파일은 **카메라 영상의 밝기와 색 조건을 재현하여 비전 추론 환경을 일정하게 유지하기 위한 실행 의존 파일**입니다.

하의에도 동일한 카메라 설정의 검증된 로컬 복사본이 다음 위치에 존재합니다.

    SW/Jetson/preprocessing/lower/dual/
    └── elp_ov2710_camera_controls.json

공통 파일과 하의 로컬 파일은 SHA-256 기준으로 동일하지만, 하의 V38의 기존 실행 의존성 구조를 유지하기 위해 하의 로컬 복사본을 삭제하거나 공통 경로로 임의 통합하지 않습니다.

검증된 SHA-256:

    222e1b6826666a80918a271ea3c29dff62c77ecc94002dc4027a185e075bb206

---

# 3. 보정 리소스

## dual_roarm_folding_board_config.json

경로:

    SW/Jetson/common/calibration/
    └── dual_roarm_folding_board_config.json

Dual RoArm M2-S와 Folding Board 환경에서 사용하는 공통 Configuration입니다.

Robot Manipulation과 Board 기준 Geometry 계산에 필요한 설정 정보를 Runtime에서 참조합니다.

상의 및 하의 저장소 실행기에서 공통 보정 리소스로 사용합니다.

---

## basket_arm2_5point_affine.json

경로:

    SW/Jetson/common/calibration/
    └── basket_arm2_5point_affine.json

ARM2가 Basket 영역의 의류를 파지할 때 사용하는 Affine Calibration 데이터입니다.

Camera Image에서 얻은 Basket 영역의 Pixel Coordinate를 ARM2가 실제로 접근할 수 있는 Robot Workspace Coordinate로 변환하는 데 사용합니다.

개념적인 좌표 변환은 다음과 같습니다.

    Basket Camera Pixel
            ↓
    5-Point Affine Calibration
            ↓
    ARM2 Workspace Coordinate
            ↓
    Basket Grasp

상의 및 하의 실행 코드에서 저장소 상대경로 기반 공통 보정 리소스로 사용합니다.

---

# 4. 공통 Homography

경로:

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

이 파일은 Folding Board 영역의 Camera Pixel Coordinate와 실제 Board Coordinate 사이의 관계를 나타내는 Homography Calibration입니다.

현재 Common Directory의 Homography는 실제 상의 통합 Runtime에서 검증된 **H-only Calibration**입니다.

파일 특성:

    Size: 282 bytes
    JSON Key: H

검증된 SHA-256:

    282ebbcb635068031f0c238b7ab1b7c715819771ced86d614311ff875a13f397

상의 Runtime에서는 Segmentation 및 Pose Estimation으로 얻은 Pixel 위치를 실제 Folding Board 좌표로 변환하여 Robot Grasp Point 및 이동 Target을 계산하는 데 사용합니다.

---

# 5. 매우 중요: 하의 전용 Homography와의 차이

하의 Runtime에는 Common Homography와 **동일한 파일명을 가진 별도의 Homography**가 존재합니다.

하의 전용 경로:

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

이 파일은 Common Directory의 H-only Homography와 동일한 파일이 아닙니다.

---

## 공통 / 상의 Homography

경로:

    SW/Jetson/common/calibration/
    └── elp_ov2710_folding_board_homography_cache.json

특성:

    Size: 282 bytes
    Keys:
        H

SHA-256:

    282ebbcb635068031f0c238b7ab1b7c715819771ced86d614311ff875a13f397

---

## 하의 전용 Homography

경로:

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

특성:

    Size: 1040 bytes

    Keys:
        H
        raw_H
        camera_geometry
        schema_version

SHA-256:

    0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45

하의 `main-33_submission_runtime.py` Runtime은 Raw Frame과 Corrected Frame의 Geometry를 구분하여 처리하므로 `raw_H`와 `camera_geometry` 정보를 포함한 Lower 전용 Homography가 필요합니다.

---

## 절대 통합하지 않는 이유

두 Homography 파일은 파일명이 같지만 다음과 같이 Runtime 요구사항이 다릅니다.

    Common / Upper
        ↓
    H-only Geometry
        ↓
    상의 실행 코드

    Lower
        ↓
    H + raw_H + camera_geometry
        ↓
    Raw / Corrected Frame Geometry 분리
        ↓
    하의 실행 코드

따라서 다음 작업을 수행하면 안 됩니다.

- Lower Homography를 Common Homography 위에 덮어쓰기
- Common Homography를 Lower Homography 위에 덮어쓰기
- 파일명이 같다는 이유로 하나의 파일로 통합
- 하의 실행 코드가 공통 Homography 하나만 사용하도록 임의 수정
- 검증 없이 Homography JSON 구조 변경

**동일한 파일명은 동일한 Runtime Artifact라는 의미가 아닙니다.**

GitHub 제출본에서는 두 Calibration을 각각의 검증된 위치에 그대로 유지합니다.

---

# 6. 기본 좌표 변환 흐름

Folding Board 위 의류의 기본 좌표 변환은 다음과 같습니다.

    ELP OV2710 Camera
            ↓
    Camera Calibration
            ↓
    Lens Undistortion
            ↓
    Segmentation / Pose Estimation
            ↓
    Pixel Coordinate
            ↓
    Homography
            ↓
    Folding Board Coordinate
            ↓
    Robot Manipulation Target

Basket 영역에서는 별도의 Affine Calibration을 사용합니다.

    ELP OV2710 Camera
            ↓
    Basket Pixel Coordinate
            ↓
    basket_arm2_5point_affine.json
            ↓
    ARM2 Workspace Coordinate
            ↓
    Basket Grasp

---

# 7. Homography란?

Homography는 Camera Image Plane과 Folding Board와 같은 실제 평면 사이의 Projective Coordinate Relationship을 표현합니다.

Camera 영상에서 검출한 특정 Pixel을 Homography Matrix로 변환하여 Board 위 실제 위치에 대응시킴으로써 Vision Perception 결과를 Robot Manipulation 좌표와 연결합니다.

본 프로젝트에서는 Homography를 다음 작업에 활용합니다.

- Garment Grasp Point 좌표 변환
- Folding Board 기준 의류 위치 계산
- Robot 이동 Target 계산
- Garment Alignment
- Manipulation Planning
- Board Geometry 기준 Position Evaluation

---

# 8. Affine 보정

Basket 영역은 Folding Board와 다른 작업 공간에 존재하므로 별도의 ARM2 Affine Calibration을 사용합니다.

`basket_arm2_5point_affine.json`을 이용하여 Basket Camera Pixel Coordinate를 ARM2 Workspace Coordinate로 변환합니다.

이를 통해 Camera에서 인식한 Basket 내 의류 위치와 실제 ARM2 Grasp 위치를 연결합니다.

---

# 9. 실행 코드별 리소스 사용 구조

## 상의 실행 코드

주요 공통 의존 파일:

    SW/Jetson/common/camera/camera_undistort.py
    SW/Jetson/common/camera/elp_ov2710_1280x720_calibration.npz
    SW/Jetson/common/camera/elp_ov2710_camera_controls.json

    SW/Jetson/common/calibration/
    ├── dual_roarm_folding_board_config.json
    ├── basket_arm2_5point_affine.json
    └── elp_ov2710_folding_board_homography_cache.json

상의 기존 실행기:

    SW/Jetson/preprocessing/upper/run_upper.py

상의 신규 자동화 실행기:

    SW/Jetson/preprocessing/upper/automation/run_upper_automation.py

---

## 하의 실행 코드

하의 실행 코드는 일부 공통 보정 파일을 직접 사용합니다.

    SW/Jetson/common/calibration/
    ├── dual_roarm_folding_board_config.json
    └── basket_arm2_5point_affine.json

그러나 카메라 보정 모듈과 카메라 보정 데이터는 기존 하의 실행 의존성 구조를 보존하기 위해 로컬 복사본을 사용합니다.

    SW/Jetson/preprocessing/lower/dual/
    ├── elp_ov2710_camera_controls.json
    └── undistort/
        ├── camera_undistort.py
        └── elp_ov2710_1280x720_calibration.npz

Homography는 하의 전용 버전을 사용합니다.

    SW/Jetson/preprocessing/lower/dual/undistort/
    └── elp_ov2710_folding_board_homography_cache.json

하의 저장소 실행기:

    SW/Jetson/preprocessing/lower/run_lower.py

---

# 10. 보정 및 카메라 설정 파일 무결성 검증

GitHub 제출 과정에서는 실제 개발 및 로봇 실행 환경에서 사용한 보정 파일과 저장소 내부 파일이 동일한지 SHA-256으로 검증했습니다.

## camera_undistort.py

    4dcf2b0f74e2dff518184fca5a6910c2ec1813c109491b46502b6c06304cc348

## 카메라 보정 NPZ

    343cc5b96b2417603510938ae49ca29aed9265618b23fc6c57392d12439befa6

## ELP OV2710 카메라 제어 설정

    222e1b6826666a80918a271ea3c29dff62c77ecc94002dc4027a185e075bb206

## Dual RoArm / Folding Board Config

    807cc17db34cf48ba1e0eb7c770670a27e3370beee4c3d237659bfb6455c2373

## Basket ARM2 Affine

    546dc9c74cc629e407bad4967b9c94d267012e85bd0ef0d86ac5fe73a536d8d8

## 공통 / 상의 Homography

    282ebbcb635068031f0c238b7ab1b7c715819771ced86d614311ff875a13f397

## 하의 전용 Homography

    0a59a7a25f09af2edd235f5ee881ec48c9c52736200f7e91ed69ab1726b26a45

---

# 11. 공통 파일 관리 원칙

`common/`은 여러 실행 코드에서 직접 또는 저장소 실행기를 통해 재사용할 수 있는 보정 리소스를 관리합니다.

하지만 본 프로젝트에서는 **중복 제거보다 검증된 실행 환경의 재현성을 우선**합니다.

따라서 파일 내용이 동일하더라도 기존 하의 소스가 동일한 디렉터리 구조를 요구하는 경우에는 하의 로컬 복사본을 유지할 수 있습니다.

즉 다음 두 원칙을 동시에 적용합니다.

1. 안전하게 공유 가능한 보정 리소스는 `common/`에서 관리
2. 기존 실행 의존성 보존이 필요한 리소스는 검증된 로컬 복사본 유지

---

# 12. 보정 및 카메라 설정 변경 시 주의사항

보정 파일을 새로 생성하거나 교체하면 비전 좌표와 로봇 작업공간 좌표 사이의 관계가 달라질 수 있습니다.

따라서 다음 변경 후에는 전체 실행 환경을 다시 검증해야 합니다.

- 카메라 위치 변경
- 카메라 각도 변경
- 해상도 변경
- 폴딩 보드 위치 변경
- 로봇 베이스 위치 변경
- Homography 재생성
- 바구니 Affine 재생성
- 카메라 내부 파라미터 보정 변경
- `elp_ov2710_camera_controls.json`의 노출 / 게인 / 화이트밸런스 설정 변경

보정 파일은 실제 로봇 좌표 계산에 직접 연결되며, 카메라 제어 설정은 세그멘테이션과 포즈 추론에 입력되는 영상 조건에 영향을 줍니다.

따라서 단순한 파일 정리 목적으로 값을 변경하면 안 되며, 변경 시 카메라 영상과 비전 추론 결과를 다시 검증해야 합니다.

---

# 13. 요약

`common/` 디렉터리는 **「접신」**의 비전 인식 결과를 로봇 좌표로 연결하는 데 필요한 핵심 카메라 및 보정 리소스를 관리합니다.

주요 리소스:

- 카메라 왜곡 보정 모듈
- ELP OV2710 내부 파라미터 보정 파일
- ELP OV2710 카메라 제어 설정 파일
- Dual RoArm / 폴딩 보드 설정
- 바구니 ARM2 Affine 보정
- 공통 / 상의 폴딩 보드 Homography

하의 실행 코드는 일부 공용 보정 리소스를 재사용하면서도 검증된 동적 의존성 구조를 보존하기 위해 카메라 리소스와 하의 전용 Homography를 로컬 디렉터리에 유지합니다.

특히 **공통 / 상의 Homography와 하의 전용 Homography는 이름만 같고 내용과 실행 용도가 다르므로 절대로 서로 덮어쓰거나 통합해서는 안 됩니다.**
