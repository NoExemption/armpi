#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import rospy
import moveit_commander
from geometry_msgs.msg import Pose

def move_to_pose(pose_goal):
    # 初始化 ROS 节点
    rospy.init_node('moveit_move_to_pose', anonymous=True)

    # 初始化 moveit_commander
    moveit_commander.roscpp_initialize(sys.argv)

    # 指定机械臂 MoveGroup 名称（通常在 MoveIt setup 时定义）
    arm = moveit_commander.MoveGroupCommander("manipulator")  # 替换为你的 move_group 名称

    # 可选：设置最大速度和加速度比例
    arm.set_max_velocity_scaling_factor(0.5)
    arm.set_max_acceleration_scaling_factor(0.5)

    # 设置目标位姿
    arm.set_pose_target(pose_goal)

    # 规划并执行
    plan = arm.go(wait=True)
    arm.stop()
    arm.clear_pose_targets()

    if plan:
        rospy.loginfo("机械臂到达目标位姿成功！")
    else:
        rospy.logwarn("机械臂未能到达目标位姿！")

if __name__ == "__main__":
    # 定义目标位姿 1
    pose1 = Pose()
    pose1.position.x = 0.0490
    pose1.position.y = 0.0165
    pose1.position.z = 0.2806
    pose1.orientation.x = -0.3294
    pose1.orientation.y = 0.2482
    pose1.orientation.z = -0.5143
    pose1.orientation.w = 0.7520

    # 定义目标位姿 2
    pose2 = Pose()
    pose2.position.x = 0.0715
    pose2.position.y = 0.0238
    pose2.position.z = 0.1277
    pose2.orientation.x = -0.7869
    pose2.orientation.y = 0.5982
    pose2.orientation.z = -0.0857
    pose2.orientation.w = 0.1254

    # 控制机械臂依次到达两个位姿
    move_to_pose(pose1)
    rospy.sleep(1)  # 可选：等待一秒
    move_to_pose(pose2)

    # 关闭 moveit_commander
    moveit_commander.roscpp_shutdown()

