# RPi Smart Inspection Car / 智能管道巡检车

<p align="center">
  <img src="上位机运行图.jpg" alt="PC Client Interface" width="800"/>
</p>

<p align="center">
  <a href="https://github.com/Pedrolino-X/RPi-Monitor-Car/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Windows-orange.svg" alt="Platform"></a>
</p>

A smart inspection car system based on Raspberry Pi 5 and a PC client, designed for remote visual inspection in narrow environments like pipelines.

一个基于树莓派5和PC上位机的智能巡检车系统，旨在实现对管道等狭窄环境的远程可视化巡检。

---

## 核心功能 / Core Features

**车载端 (Raspberry Pi):**
- **🚗 运动控制 (Motion Control):** 精确控制直流电机，实现前进、后退及转向。
- **🧭 姿态感知 (Attitude Sensing):** 集成IMU（JY901S），实时获取并回传车辆的三轴姿态角、温度等数据。
- **📹 视觉采集 (Visual Capture):** 通过摄像头捕捉高清实时视频流，并支持远程拍照。
- **🦾 简易机械臂 (Simple Robotic Arm):** 控制两个舵机，执行预设的抓取或调整动作。
- **📡 无线通信 (Wireless Communication):** 内置TCP服务器，稳定接收PC指令并回传数据。支持AP（热点）和STA（客户端）两种网络模式。

**上位机 (PC Client):**
- **🖥️ 图形化界面 (GUI):** 基于PyQt构建，提供直观的控制与数据显示界面。
- **🕹️ 远程遥控 (Remote Control):** 支持键盘 (W/A/S/D) 和UI按钮两种方式控制小车运动。
- **📊 实时监控 (Real-time Monitoring):**
  - 左侧窗口实时显示摄像头回传的视频流。
  - 中间仪表盘动态可视化展示车辆的俯仰、横滚、偏航角度。
  - 右侧窗口通过VTK加载3D模型，同步模拟车辆姿态。
- **📂 自动文件同步 (Auto File Sync):** 后台服务通过SCP协议自动下载车载端拍摄的照片到本地，方便查看和管理。

---

## 技术栈 / Tech Stack

- **Hardware:** Raspberry Pi 5, JY901S IMU, TB6612FNG Motor Driver, SG90 Servos, Pi Camera
- **Raspberry Pi Software:** Python, OpenCV, RPi.GPIO, Pyserial, Socket
- **PC Client Software:** Python, PyQt5, PyOpenGL, VTK, Paramiko (for SCP)
- **Communication Protocol:** TCP/IP, SCP

---

## 快速开始 / Getting Started

### 1. 树莓派端设置 / Raspberry Pi Setup

1.  **硬件连接 (Hardware Connection):**
    - 根据 `交接文档.md` 内的接线图，连接好电机、舵机、IMU和摄像头。
    - 使用能提供5V/5A的稳定电源为树莓派供电。

2.  **软件部署 (Software Deployment):**
    - **(推荐)** 烧录项目提供的预配置系统镜像 (`.pmfx` 文件，不包含在仓库中)。
    - **(手动)** 或在一个干净的Raspberry Pi OS上，根据 `交接文档.md` 的指南安装所有依赖，并将 `树莓派端代码/` 目录下的文件部署到树莓派。

3.  **启动服务 (Start Service):**
    - 树莓派开机后，系统将默认创建一个名为 `MyPiAP` 的Wi-Fi热点 (密码: `raspberry`)。
    - 服务会自动运行。如果需要手动启动，请在代码目录下执行 `python3 server.py`。

### 2. 上位机端设置 / PC Client Setup

1.  **环境准备 (Environment):**
    - 确保你的PC上安装了 Python 3.7+。
    - 克隆或下载本仓库代码。

2.  **安装依赖 (Install Dependencies):**
    - 打开命令行，进入 `上位机软件代码/` 目录。
    - (推荐) 创建并激活虚拟环境。
    - 运行以下命令安装所有必需的库：
      ```bash
      pip install -r requirements.txt
      ```

3.  **运行程序 (Run Application):**
    - **(开发模式)** 直接运行主程序：
      ```bash
      python main.py
      ```
    - **(可执行文件)** 或直接运行 `上位机软件代码/dist/` 目录下的 `.exe` 文件。

---

## 操作流程 / Usage

1.  **连接网络:** 将你的PC连接到树莓派创建的 `MyPiAP` Wi-Fi网络。
2.  **启动上位机:** 运行PC端的应用程序。
3.  **建立连接:** 在上位机界面点击 **"开"** 按钮。
4.  **开始控制:**
    - 使用 **W, A, S, D** 或界面按钮控制移动。
    - 点击 **"◈"** 按钮拍照。
    - 点击 **"查看图片"** 按钮，会自动打开存放同步照片的文件夹。
    - 使用右下角的按钮控制机械臂。
5.  **断开连接:** 点击 **"关"** 按钮结束。

---

## 协议 / License

This project is licensed under the MIT License. See the `LICENSE` file for details.

本项目采用 MIT 协议。详情见 `LICENSE` 文件。
