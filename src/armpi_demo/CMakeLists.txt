cmake_minimum_required(VERSION 3.1.3)
project(armpi_demo)

# 查找必需的ROS包
find_package(catkin REQUIRED COMPONENTS
  rospy
  moveit_commander
  std_msgs
  geometry_msgs
  aruco_msgs
  trajectory_msgs 
)

# 声明catkin包
catkin_package(
  CATKIN_DEPENDS rospy moveit_commander std_msgs trajectory_msgs
)

# 安装launch文件
install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

# 安装Python脚本
catkin_install_python(PROGRAMS
  scripts/armpi_moveit_fk_demo.py 
  scripts/armpi_moveit_ik_demo.py
  scripts/armpi_moveit_ik_test.py
  scripts/armpi_pose_record.py
  scripts/handeye_record.py
  scripts/handeye_calibrate.py
  scripts/marker_tf_pub.py
  scripts/blue_block_grasp.py
  scripts/capture_blocks.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
