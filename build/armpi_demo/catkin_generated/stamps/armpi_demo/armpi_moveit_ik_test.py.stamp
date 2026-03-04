#!/usr/bin/env python3

import sys
import rospy
import moveit_commander
from geometry_msgs.msg import Pose

class RobotController:
    def __init__(self, manipulator_group="manipulator", gripper_group="gripper"):
        """初始化 MoveIt 控制器"""
        rospy.init_node('moveit_robot_controller', anonymous=True)
        moveit_commander.roscpp_initialize(sys.argv)

        # 初始化两个控制组：机械臂与夹爪
        self.manipulator = moveit_commander.MoveGroupCommander(manipulator_group)
        self.gripper = moveit_commander.MoveGroupCommander(gripper_group)

        # 设置规划参数
        self.manipulator.set_planning_time(8.0)
        self.manipulator.allow_replanning(True)
        self.manipulator.set_goal_joint_tolerance(0.05)
        self.manipulator.set_goal_position_tolerance(0.01)
        self.manipulator.set_goal_orientation_tolerance(0.01)

        rospy.loginfo("机械臂控制器初始化完成。")

    def move_to_pose(self, pose_list, retries=3):
        """
        控制机械臂移动到指定的姿态
        pose_list: [x, y, z, qx, qy, qz, qw]
        """
        pose_goal = Pose()
        pose_goal.position.x = pose_list[0]
        pose_goal.position.y = pose_list[1]
        pose_goal.position.z = pose_list[2]
        pose_goal.orientation.x = pose_list[3]
        pose_goal.orientation.y = pose_list[4]
        pose_goal.orientation.z = pose_list[5]
        pose_goal.orientation.w = pose_list[6]

        for attempt in range(1, retries + 1):
            try:
                rospy.loginfo(f"第 {attempt} 次尝试移动到目标位姿：{pose_list}")
                # 同步当前状态
                self.manipulator.set_start_state_to_current_state()
                self.manipulator.set_pose_target(pose_goal)

                success = self.manipulator.go(wait=True)
                self.manipulator.stop()
                self.manipulator.clear_pose_targets()

                if success:
                    rospy.loginfo(f"第 {attempt} 次尝试：机械臂成功到达目标位姿。")
                    return True
                else:
                    rospy.logwarn(f"第 {attempt} 次尝试：机械臂未能到达目标位姿，准备重试...")
            except Exception as e:
                rospy.logerr(f"第 {attempt} 次执行位姿控制时发生错误：{e}")

            rospy.sleep(0.5)

        rospy.logerr("连续多次尝试均失败，程序终止。")
        sys.exit(1)

    def move_gripper(self, position):
        """控制夹爪移动到指定位置"""
        try:
            self.gripper.set_joint_value_target([position])
            self.gripper.go(wait=True)
            self.gripper.stop()
            rospy.loginfo(f"夹爪已移动到目标位置：{position}")
        except Exception as e:
            rospy.logerr(f"夹爪控制失败：{e}")

    def shutdown(self):
        """安全关闭 MoveIt"""
        moveit_commander.roscpp_shutdown()
        rospy.loginfo("MoveIt 控制程序已安全退出。")


if __name__ == "__main__":
    try:
        robot = RobotController()

        # 定义目标位姿（列表形式）
        pose1 = [-0.0109,0.1134,0.1680,
	-0.9524,-0.0319,0.0190,0.3025]
        pose2 = [-0.1094, 0.0165, 0.1163,
                 -0.7250, -0.6346, 0.1728, 0.2043]

        rospy.loginfo("开始执行机械臂位姿控制流程。")

        robot.move_to_pose(pose1)
        rospy.sleep(1)
        robot.move_to_pose(pose2)

    except KeyboardInterrupt:
        rospy.logwarn("检测到 Ctrl+C，安全关闭系统...")
    except Exception as e:
        rospy.logerr(f"主程序运行过程中发生异常：{e}")
    finally:
        robot.shutdown()

