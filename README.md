# ArmPi ROS Control System 🤖

[![ROS](https://img.shields.io/badge/ROS-Melodic%2FNoetic-blue)](http://wiki.ros.org/)
[![Python](https://img.shields.io/badge/Python-2.7%2F3.8-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)

**ArmPi** 是一个基于 ROS (Robot Operating System) 的智能机械臂控制项目。本项目深度集成了 **MoveIt** 运动规划框架与 **OpenCV/RealSense** 视觉算法，实现了从基础运动控制、手眼标定到复杂视觉抓取的一整套解决方案。

## ✨ 核心功能 (Key Features)

- **🦾 运动规划 (Motion Planning):** 基于 MoveIt 框架，支持正逆运动学解算 (IK/FK)、避障规划与平滑轨迹控制。
- **👁️ 视觉感知 (Visual Perception):** 兼容 **Intel RealSense D435** 及 USB 摄像头，具备 Aruco 标签识别、颜色识别与 3D 物体定位能力。
- **📏 手眼标定 (Hand-Eye Calibration):** 提供自动化的 Eye-to-Hand 标定工具，快速获取相机与机械臂基座的坐标变换矩阵。
- **🎯 智能抓取 (Intelligent Grasping):** 包含基于视觉反馈的物体抓取、分拣与堆叠 Demo，支持动态修正抓取位姿。
- **🖥️ 仿真支持 (Simulation):** 支持 Rviz 可视化仿真，方便在无实物环境下进行算法验证与调试。

## 🛠️ 技术架构 (Tech Stack)

- **操作系统:** Ubuntu 18.04 (Melodic) / 20.04 (Noetic)
- **核心框架:** ROS (Robot Operating System)
- **运动控制:** MoveIt!, KDL/Trac-IK Solver
- **计算机视觉:** OpenCV, cv_bridge, realsense-ros
- **编程语言:** Python, C++

## ⚙️ 环境配置 (Prerequisites)

在开始之前，请确保您已安装 ROS 基础环境。

1. **安装依赖包:**

   ```bash
   # 安装 MoveIt 及相关依赖
   sudo apt-get install ros-$ROS_DISTRO-moveit
   # 安装 RealSense 驱动 (如使用 RealSense 相机)
   sudo apt-get install ros-$ROS_DISTRO-realsense2-camera
   # Python 依赖
   pip install opencv-python transforms3d
   ```

2. **硬件连接:**
   - 使用 USB 线连接 ArmPi 机械臂扩展板。
   - 连接 RealSense 或 USB 摄像头至上位机。

## 🚀 快速开始 (Quick Start)

### 1. 编译项目

```bash
cd ~/catkin_ws/src
# 克隆本项目
git clone https://github.com/your-username/armpi.git
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### 2. 启动 MoveIt 控制

启动机械臂底层驱动、MoveIt 规划组及 Rviz 可视化界面：

```bash
roslaunch armpi_pro_moveit_config demo.launch
```

### 3. 运行手眼标定 (Hand-Eye Calibration)

若使用视觉功能，需先进行标定以建立坐标系关系：

```bash
roslaunch armpi_pro_demo hand_eye_calibration.launch
```

_注：详细标定步骤请参考 [README_RealSense.markdown](./README_RealSense.markdown)_

### 4. 运行功能 Demo

**颜色识别与抓取:**

```bash
rosrun armpi_pro_demo color_grasp_demo.py
```

**Aruco 标签追踪:**

```bash
rosrun armpi_pro_demo ar_label_detect.py
```

## 📂 目录结构 (Directory Structure)

```text
armpi/
├── armpi_pro_control/       # 机械臂底层通信与硬件驱动节点
│   ├── launch/              # 硬件驱动启动文件
│   └── scripts/             # 串口通信与舵机控制脚本
├── armpi_pro_demo/          # 核心应用功能
│   ├── launch/              # 功能 Demo 启动文件 (如标定、视觉识别)
│   └── scripts/             # 核心 Python 策略脚本
│       ├── color_grasp_demo.py
│       └── ar_label_detect.py
├── armpi_pro_moveit_config/ # MoveIt 参数配置包
│   ├── config/              # SRDF, 关节限制, 运动学参数
│   └── launch/              # MoveIt 启动入口 (demo.launch)
├── armpi_pro_description/   # 机械臂描述文件
│   ├── urdf/                # 机器人模型文件 (.xacro/.urdf)
│   └── meshes/              # 3D 模型资源 (.stl/.dae)
└── README.md                # 项目主文档
```
