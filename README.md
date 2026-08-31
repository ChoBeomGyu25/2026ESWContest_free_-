# 2026 ESWContest_free_옷개스트라

---

## 🏷️ Project Introduction

**옷개스트라**는 비전 AI와 듀얼 로봇팔을 활용하여 비정형 의류를 자동으로 인식하고 정리하는 **의류 자동 정리 로봇 시스템 「접신」**을 개발하고 있습니다.

일정한 형태를 유지하지 않는 의류의 특성을 고려하여 카메라 기반의 의류 인식과 상태 판단을 수행하고, 두 대의 로봇팔이 협업하여 의류를 파지하고 펼친 뒤 정렬 및 접기까지 수행하도록 시스템을 구성하였습니다.  
이를 통해 사람이 직접 수행하던 반복적인 의류 정리 작업을 로봇과 인공지능을 이용하여 자동화하는 것을 목표로 합니다.

---

## 💡 Motivation
세탁은 **세탁기**, 건조는 **건조기**를 통해 자동화되고 있지만, 세탁이 끝난 의류를 **펼치고 정렬하여 접는 과정은 여전히 사람이 직접 수행해야 하는 대표적인 반복 가사 노동**으로 남아 있습니다. 특히 고령 인구와 맞벌이·1인 가구가 증가하면서 가사 노동에 대한 부담 역시 커지고 있으며, 반복적인 의류 정리는 시간적·신체적 부담과 일상생활의 비효율을 발생시킵니다.

기존에도 FoldiMate, Laundroid, Speedy-T 등 의류 정리를 위한 장치가 개발되었지만, **높은 가격, 긴 처리 시간, 반자동 방식, 제한적인 의류 대응 범위** 등의 한계가 존재합니다. 특히 사용자가 의류를 특정 형태로 투입하거나 사전에 정렬해야 하는 경우가 많아, 무작위로 놓이거나 구겨진 다양한 형태의 의류를 처음부터 끝까지 자동으로 처리하는 데에는 한계가 있습니다.

이에 저희는 비정형 상태로 놓인 의류를 비전 AI로 인식하고, 두 대의 로봇팔이 의류의 상태에 따라 직접 조작하여 **펼침·정렬·주름 및 접힘 보정·접기까지 전 과정을 수행하는 자동 의류 정리 로봇 시스템**을 제안합니다. 이를 통해 사용자의 의류 정리 부담을 줄이고, 기존 가전제품이 자동화하지 못했던 **세탁 이후의 의류 정리 과정까지 자동화**하는 것을 목표로 합니다.


---

## 🎯 Project Goal

본 프로젝트의 목표는 **무작위로 놓여 있거나 구겨진 의류의 상태를 로봇이 스스로 인식하고, 최종적으로 정돈된 형태까지 만드는 전 과정을 자동화하는 것**입니다.

의류의 형태와 위치를 비전 AI를 통해 판단한 뒤, 두 대의 로봇팔이 협업하여 **의류 파지 → 배치 → 펼침 → 정렬 → 주름 및 접힘 보정 → 접기 → 완료 상태 판단**의 과정을 순차적으로 수행합니다.

특히 형태 변화가 큰 비정형 의류를 안정적으로 조작하기 위해 다양한 시각 인식 기술과 의류 상태에 따른 로봇 동작 판단 알고리즘을 결합하여, 여러 의류 상태에서도 유연하게 대응할 수 있는 자동 정리 시스템을 구현하는 것을 최종 목표로 합니다.

---

## 🤖 System Overview
<img width="1080" alt="스크린샷 2026-08-31 120610" src="https://github.com/user-attachments/assets/0d9b9705-7e4e-422b-a4ec-e412d4897461" />
<img width="1080" alt="스크린샷 2026-08-31 145607" src="https://github.com/user-attachments/assets/07279e27-13f9-4464-943a-0d79fe5baa2a" />


본 시스템은 카메라 기반 비전 AI와 두 대의 RoArm M2-S를 활용하여, 바구니에 무작위로 놓인 의류를 인식하고 펼침·정렬·보정·접기까지의 전 과정을 자동으로 수행합니다.

1. **RoArm이 바구니에서 의류를 파지**하여 폴딩 플레이트 위로 이동
2. **카메라 영상과 ArUco Marker / Checkerboard**를 이용하여 영상 좌표를 실제 로봇 작업 좌표계로 변환
3. **Segmentation 및 Pose 모델**을 통해 의류의 영역과 주요 특징점을 인식
4. 두 대의 RoArm을 이용하여 **공중 Spread 및 초기 정렬 동작**을 수행
5. **Fallback Mask, Wrinkle Heatmap, UniDepth** 등을 이용하여 의류의 구김·접힘 및 현재 상태를 분석
6. 분석된 의류 상태를 기반으로 **펼침·당기기·회전 등 필요한 보정 동작**을 선택하여 반복 수행
7. 의류가 충분히 평활화되고 정렬되면 **Finish 상태로 판단**하고 폴딩 플레이트를 구동하여 의류를 접음
8. 접힌 의류를 배출한 뒤 로봇이 초기 위치로 복귀하여 **다음 의류 정리 작업을 준비**

---

## ⚙️ Hardware
<img width="1080" alt="스크린샷 2026-08-31 145738" src="https://github.com/user-attachments/assets/7cec9cb2-e7f6-46d7-a2e9-a0eda6d81ed2" />
<img width="1080" alt="스크린샷 2026-08-31 145753" src="https://github.com/user-attachments/assets/8b196932-feca-442a-aa73-7a94ab580ad2" />
<img width="1080" alt="스크린샷 2026-08-31 145722" src="https://github.com/user-attachments/assets/61f56ebb-16c4-437d-9a95-5c233de636ad" />



---

## 🧠 Software / AI



---

## 👕 Clothing Manipulation Process



---

## 📂 Repository Structure



---

## ⚙️ Environment

| Category | Environment |
|---|---|
| 💻 **Main Processor** | ![Jetson Orin Nano](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-76B900?style=for-the-badge&logo=nvidia&logoColor=white) |
| 🔧 **Sub Controller** | ![Arduino](https://img.shields.io/badge/Arduino-Controller-00878F?style=for-the-badge&logo=arduino&logoColor=white) |
| 🐧 **OS** | ![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04.3-E95420?style=for-the-badge&logo=ubuntu&logoColor=white) |
| 📦 **Container** | ![Docker](https://img.shields.io/badge/Docker-29.7.2-2496ED?style=for-the-badge&logo=docker&logoColor=white) |
| 💻 **Programming Language** | ![Python](https://img.shields.io/badge/Python-3.10.12-3776AB?style=for-the-badge&logo=python&logoColor=white) |
| 🤖 **Robot Platform** | ![RoArm M2-S](https://img.shields.io/badge/RoArm-M2--S-4A90E2?style=for-the-badge) ![Dual Robot Arm](https://img.shields.io/badge/Dual-Robot%20Arm-6C63FF?style=for-the-badge) |
| 🔌 **Communication** | ![USB Serial](https://img.shields.io/badge/USB-Serial%20Communication-555555?style=for-the-badge&logo=usb&logoColor=white) |
| 📷 **Camera** | ![ELP Camera](https://img.shields.io/badge/ELP-Wide%20Angle%20Camera-2E8B57?style=for-the-badge) |
| 📐 **Vision Calibration** | ![ArUco](https://img.shields.io/badge/ArUco-Marker-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white) |
| 🧠 **AI Framework** | ![PyTorch](https://img.shields.io/badge/PyTorch-2.10.0-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white) ![Ultralytics](https://img.shields.io/badge/Ultralytics-8.4.45-111F68?style=for-the-badge) |
| 👕 **Garment Perception** | ![YOLO26](https://img.shields.io/badge/YOLO26-Segmentation-00A98F?style=for-the-badge) ![Pose Estimation](https://img.shields.io/badge/YOLO26-Pose%20Estimation-7B61FF?style=for-the-badge) |
| ⚡ **Inference Engine** | ![TensorRT](https://img.shields.io/badge/TensorRT-10.7.0-76B900?style=for-the-badge&logo=nvidia&logoColor=white) |
| 🎮 **GPU Runtime** | ![CUDA](https://img.shields.io/badge/CUDA-12.6%20(PyTorch)-76B900?style=for-the-badge&logo=nvidia&logoColor=white) |
| 📏 **Depth Estimation** | ![UniDepth](https://img.shields.io/badge/UniDepth-V2-1E88E5?style=for-the-badge) |
| 📊 **Learning / Prediction** | ![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-EB5B2A?style=for-the-badge) |
| 🛠️ **Libraries & Tools** | ![OpenCV](https://img.shields.io/badge/OpenCV-4.11.0-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-1.26.4-013243?style=for-the-badge&logo=numpy&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white) |

## ▶️ How to Run



---

## 👥 Team Members

- 조범규
- 유채린
- 임혜강
- 정유환
- 조승진
