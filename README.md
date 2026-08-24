# 2026 ESWContest_free_옷개스트라

---

## 🏷️ Project Introduction

**옷개스트라**는 비전 AI와 듀얼 로봇팔을 활용하여 비정형 의류를 자동으로 인식하고 정리하는 **의류 자동 정리 로봇 시스템 「접신」**을 개발하고 있습니다.

일정한 형태를 유지하지 않는 의류의 특성을 고려하여 카메라 기반의 의류 인식과 상태 판단을 수행하고, 두 대의 로봇팔이 협업하여 의류를 파지하고 펼친 뒤 정렬 및 접기까지 수행하도록 시스템을 구성하였습니다.  
이를 통해 사람이 직접 수행하던 반복적인 의류 정리 작업을 로봇과 인공지능을 이용하여 자동화하는 것을 목표로 합니다.

---

## 💡 Motivation



---

## 🎯 Project Goal

본 프로젝트의 목표는 **무작위로 놓여 있거나 구겨진 의류의 상태를 로봇이 스스로 인식하고, 최종적으로 정돈된 형태까지 만드는 전 과정을 자동화하는 것**입니다.

의류의 형태와 위치를 비전 AI를 통해 판단한 뒤, 두 대의 로봇팔이 협업하여 **의류 파지 → 배치 → 펼침 → 정렬 → 주름 및 접힘 보정 → 접기 → 완료 상태 판단**의 과정을 순차적으로 수행합니다.

특히 형태 변화가 큰 비정형 의류를 안정적으로 조작하기 위해 다양한 시각 인식 기술과 의류 상태에 따른 로봇 동작 판단 알고리즘을 결합하여, 여러 의류 상태에서도 유연하게 대응할 수 있는 자동 정리 시스템을 구현하는 것을 최종 목표로 합니다.

---

## 🤖 System Overview



---

## ⚙️ Hardware



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
