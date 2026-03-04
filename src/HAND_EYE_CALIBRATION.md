USB 摄像头与手眼标定相关操作指南
一、USB 摄像头相关配置
1. 安装 usb_cam 驱动
2. 修改 usb_cam.launch
3. 进行相机内参标定
4. 完善 usb_cam.launch
注意：迁移程序后，需要检查调用标定结果路径
5. 修改相关文件（基于 D435I）
handeye_setup.launch
aruco 的 single.launch
handeye_record.py
handeye_calibrate.py
maker_tf_pub
注意：迁移程序后，需要对读取路径和保存路径进行修改
6. 改进 farsight_moveit_action_server.py
优化执行轨迹
7. 重新设计算法思路
重新设计 armpi_moveit_ik_demo.py、armpi_moveit_ik_test.py 算法思路，保证逆解过程正常执行
8. 创建 aruco_block_grasp.py
识别带有 aruco marker 的物块，并进行抓取
注意：迁移程序后，需要对读取路径进行修改
二、OpenCV calibrateHandEye () 接口使用
1. 安装依赖库
安装 Python 环境下的 OpenCV 核心库、扩展库及数值计算库
2. 修改配置文件
修改 /opt/ros/noetic/share/aruco_ros/launch/single.launch
3. 创建 handeye_record.py
读取机械臂末端位姿和 Aruco marker 相对于相机位姿
注意：迁移程序后，需要对保存路径进行修改
4. 数据采集
采集数量足够的数据
5. 创建 handeye_calibrate.py
将采集数据转换为 Opencv 手眼标定格式并进行手眼标定
注意：迁移程序后，需要对读取路径和保存路径进行修改
6. 创建 marker_tf_pub.py
发布 marker 到末端坐标系
注意：迁移程序后，需要对读取路径进行修改
7. 创建 blue_block_grasp.py
识别蓝色物块，并进行抓取
三、Easy_handeye 使用
1. 安装 RealSense SDK 2.0
2. 安装 easy_handeye
3. 修改 easy_handeye 的 launch 文件
<!-- 第2行 -->
<arg name="namespace_prefix" default="ur5_kinect_handeyecalibration" />

<!-- 第4行 -->
<arg name="robot_ip" doc="The IP address of the UR5 robot" />

<!-- 第6-7行 -->
<arg name="marker_size" doc="Size of the ArUco marker used, in meters" />
<arg name="marker_id" doc="The ID of the ArUco marker used" />

<!-- 第8-11行（Kinect启动部分） -->
<include file="$(find freenect_launch)/launch/freenect.launch" >
    <arg name="depth_registration" value="true" />
</include>

<!-- 第15-17行（ArUco tracker） -->
<remap from="/camera_info" to="/camera/rgb" />
<remap from="/image" to="/camera/rgb/image_rect_color" />

<!-- 第22行 -->
<param name="camera_frame" value="camera_rgb_optical_frame"/>

<!-- 第26-32行（UR5启动部分） -->
<include file="$(find ur_bringup)/launch/ur5_bringup.launch">
    <arg name="limited" value="true" />
    <arg name="robot_ip" value="192.168.0.21" />
</include>
<include file="$(find ur5_moveit_config)/launch/ur5_moveit_planning_execution.launch">
    <arg name="limited" value="true" />
</include>

<!-- 第39-42行（easy_handeye配置） -->
<arg name="robot_base_frame" value="base_link" />
<arg name="robot_effector_frame" value="wrist_3_link" />
4. 安装依赖包
安装 aruco_ros、transforms3d
5. 手眼标定