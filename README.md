# 2026 ESWContest_free_옷개스트라

---

## 🏷️ Project Introduction

**옷개스트라**는 AI 기반 컴퓨터 비전과 듀얼 로봇팔을 활용하여 비정형 의류를 자동으로 인식하고 정리하는 **의류 자동 정리 로봇 시스템 「접신」**을 개발하고 있습니다.

일정한 형태를 유지하지 않는 의류의 특성을 고려하여 카메라 기반의 의류 인식과 상태 판단을 수행하고, 두 대의 로봇팔이 협업하여 의류를 파지하고 펼친 뒤 정렬 및 접기까지 수행하도록 시스템을 구성하였습니다.
이를 통해 사람이 직접 수행하던 반복적인 의류 정리 작업을 로봇과 인공지능을 이용하여 자동화하는 것을 목표로 합니다.

---

## 💡 Motivation
세탁은 **세탁기**, 건조는 **건조기**를 통해 자동화되고 있지만, 세탁이 끝난 의류를 **펼치고 정렬하여 접는 과정은 여전히 사람이 직접 수행해야 하는 대표적인 반복 가사 노동**으로 남아 있습니다. 특히 고령 인구와 맞벌이·1인 가구가 증가하면서 가사 노동에 대한 부담 역시 커지고 있으며, 반복적인 의류 정리는 시간적·신체적 부담과 일상생활의 비효율을 발생시킵니다.

기존에도 FoldiMate, Laundroid, Speedy-T 등 의류 정리를 위한 장치가 개발되었지만, **높은 가격, 긴 처리 시간, 반자동 방식, 제한적인 의류 대응 범위** 등의 한계가 존재합니다. 특히 사용자가 의류를 특정 형태로 투입하거나 사전에 정렬해야 하는 경우가 많아, 무작위로 놓이거나 구겨진 다양한 형태의 의류를 처음부터 끝까지 자동으로 처리하는 데에는 한계가 있습니다.

이에 저희는 비정형 상태로 놓인 의류를 AI기반 컴퓨터 비전으로 인식하고, 두 대의 로봇팔이 의류의 상태에 따라 직접 조작하여 **펼침·정렬·주름 및 접힘 보정·접기까지 전 과정을 수행하는 자동 의류 정리 로봇 시스템**을 제안합니다. 이를 통해 사용자의 의류 정리 부담을 줄이고, 기존 가전제품이 자동화하지 못했던 **세탁 이후의 의류 정리 과정까지 자동화**하는 것을 목표로 합니다.


---

## 🎯 Project Goal

본 프로젝트의 목표는 **무작위로 놓여 있거나 구겨진 의류의 상태를 로봇이 스스로 인식하고, 최종적으로 정돈된 형태까지 만드는 전 과정을 자동화하는 것**입니다.

의류의 형태와 위치를 AI 기반 컴퓨터 비전 통해 판단한 뒤, 두 대의 로봇팔이 협업하여 **의류 파지 → 배치 → 펼침 → 정렬 → 주름 및 접힘 보정 → 접기 → 완료 상태 판단**의 과정을 순차적으로 수행합니다.

특히 형태 변화가 큰 비정형 의류를 안정적으로 조작하기 위해 다양한 시각 인식 기술과 의류 상태에 따른 로봇 동작 판단 알고리즘을 결합하여, 여러 의류 상태에서도 유연하게 대응할 수 있는 자동 정리 시스템을 구현하는 것을 최종 목표로 합니다.

---

## 🤖 System Overview
<img width="1080" alt="스크린샷 2026-08-31 120610" src="https://github.com/user-attachments/assets/0d9b9705-7e4e-422b-a4ec-e412d4897461" />
<img width="1080" alt="스크린샷 2026-08-31 145607" src="https://github.com/user-attachments/assets/07279e27-13f9-4464-943a-0d79fe5baa2a" />


본 시스템은 카메라 기반 비전 AI와 두 대의 로봇팔을 활용하여, 바구니에 무작위로 놓인 의류를 인식하고 펼침·정렬·보정·접기까지의 전 과정을 자동으로 수행합니다.

1. **RoArm이 바구니에서 의류를 파지**하여 폴딩 플레이트 위로 이동
2. **카메라 영상과 ArUco Marker / Checkerboard**를 이용하여 영상 좌표를 실제 로봇 작업 좌표계로 변환
3. **Segmentation 및 Pose 모델**을 통해 의류의 영역과 주요 특징점을 인식
4. 두 대의 로봇팔을 이용하여 **공중 Spread 및 초기 정렬 동작**을 수행
5. **Fallback Mask, Wrinkle Heatmap, UniDepth** 등을 이용하여 의류의 구김·접힘 및 현재 상태를 분석
6. 분석된 의류 상태를 기반으로 **펼침·당기기·회전 등 필요한 보정 동작**을 선택하여 반복 수행
7. 의류가 충분히 평활화되고 정렬되면 **Finish 상태로 판단**하고 폴딩 플레이트를 구동하여 의류를 접음
8. 접힌 의류를 배출한 뒤 로봇이 초기 위치로 복귀하여 **다음 의류 정리 작업을 준비**

---

## ⚙️ Hardware
<img width="1080" alt="스크린샷 2026-08-31 145738" src="https://github.com/user-attachments/assets/7cec9cb2-e7f6-46d7-a2e9-a0eda6d81ed2" />
<img width="1080" alt="Hardware 구성 및 기능" src="https://github.com/user-attachments/assets/156bbb4a-37d6-4239-809e-7aa6ed1985d5" />
<img width="1080" alt="스크린샷 2026-08-31 145722" src="https://github.com/user-attachments/assets/61f56ebb-16c4-437d-9a95-5c233de636ad" />



---

## 🧠 Software / AI
<img width="1080" alt="상의 주요 함수별 기능" src="https://github.com/user-attachments/assets/19c07bf8-7822-41cc-9dd1-3c4e1b438ee9" />
<img width="1080" alt="하의 주요 함수별 기능" src="https://github.com/user-attachments/assets/08c7a5fe-d60a-4c8f-90a5-914da7dde6bc" />
<img width="1080" alt="Jerber" src="https://github.com/user-attachments/assets/79be02ae-2a05-4532-8dc1-dceecf5347e2" />
<img width="1080" alt="Application" src="https://github.com/user-attachments/assets/0f889cd8-b204-419d-b98e-84a0a1747b08" />




---

## 👕 Clothing Manipulation Process
<img width="1080" alt="스크린샷 2026-08-31 161525" src="https://github.com/user-attachments/assets/fa574788-51f4-4812-9a8a-ff868efd6f5f" />
<img width="1080" alt="스크린샷 2026-08-31 161535" src="https://github.com/user-attachments/assets/ba93dce3-5026-4895-babb-6c1bafe1a514" />
<img width="1080" alt="스크린샷 2026-08-31 161541" src="https://github.com/user-attachments/assets/0ac862e2-8d5c-4183-ad93-43c89c716344" />
<img width="1080" alt="스크린샷 2026-08-31 161547" src="https://github.com/user-attachments/assets/1976f757-d705-469d-acb4-bd26a6db8fc7" />



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

## 📈Expected Effects & Development
<img width="1866" height="1047" alt="스크린샷 2026-08-31 163309" src="https://github.com/user-attachments/assets/8eb4700f-1c48-4e6d-9677-1277493fc8dc" />

본 시스템은 세탁 이후 사람이 직접 수행해야 했던 **의류 펼침·정렬·주름 및 접힘 보정·접기 과정을 자동화**함으로써 반복적인 가사 노동에 소요되는 시간과 신체적 부담을 줄이는 것을 목표로 합니다. 특히 일반적인 의류 정리에 평균 10~30분 정도가 소요되는 점을 고려할 때, 사용자의 개입을 최소화하여 의류 정리 과정을 자동으로 수행할 수 있다면 일상생활에서 실질적인 시간 절감 효과를 기대할 수 있습니다. 또한 자체 진행한 설문조사에서는 총 145명의 응답자 중 **111명, 약 76.6%가 '자동으로 옷을 개어주는 로봇'의 출시 시 구매 의향에 긍정적인 응답**을 보여, 자동 의류 정리에 대한 실제 사용자 수요와 활용 가능성도 확인하였습니다. 향후 세탁기와 건조기뿐만 아니라 의류 보관 시스템까지 연계한다면 **세탁 → 건조 → 정리 → 보관으로 이어지는 통합 스마트 홈 의류 관리 시스템**으로 발전할 수 있습니다.

본 기술은 가정용 스마트 홈을 넘어 **의류 유통·전자상거래 및 물류 산업으로의 확장 가능성**도 가지고 있습니다. 온라인 의류 판매 시장이 성장하면서 반품된 상품의 상태 확인, 펼침, 정렬, 재포장 등의 반복 작업 역시 증가하고 있으며, 이러한 과정에 비정형 의류 인식과 로봇 조작 기술을 적용하면 작업 효율과 공간 활용도를 높일 수 있습니다. 특히 다양한 형태로 놓인 의류를 AI 기반 컴퓨터 비전이 인식하고 상태에 따라 필요한 조작 동작을 선택하는 기술을 고도화할 경우, 패션 물류센터나 대형 세탁·정리 시설에서 반복적으로 수행되는 단순 작업을 자동화할 수 있습니다. 이를 통해 제한된 인력을 반복 작업에 투입하는 대신 **품질 관리, 고객 대응, 시스템 운영 등 보다 높은 부가가치를 갖는 업무에 집중**시킬 수 있으며, 장기적으로는 인력난 대응과 운영 비용 절감에도 기여할 수 있습니다. 최종적으로 본 프로젝트는 단순히 옷을 접는 하나의 가전제품을 넘어, **비정형 섬유 제품을 스스로 인식하고 판단하여 조작할 수 있는 지능형 로봇 자동화 플랫폼**으로 발전하는 것을 목표로 합니다.


---

## 👥 Team Members

- 조범규
- 유채린
- 임혜강
- 정유환
- 조승진
