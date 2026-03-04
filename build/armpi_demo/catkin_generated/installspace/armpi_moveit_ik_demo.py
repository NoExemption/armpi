#!/usr/bin/env python3

import rospy
import moveit_commander
import geometry_msgs.msg
import sys
import signal
import numpy as np


class ArmGripperController:
    def __init__(self):
        """初始化 MoveIt 控制器"""
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node('arm_gripper_controller', anonymous=True)

        # 注册 Ctrl+C 信号处理
        signal.signal(signal.SIGINT, self.shutdown_handler)

        rospy.loginfo("正在初始化 MoveIt Commander...")
        self.robot = moveit_commander.RobotCommander()
        self.scene = moveit_commander.PlanningSceneInterface()

        # 初始化两个规划组
        self.arm_group = moveit_commander.MoveGroupCommander("manipulator")
        self.gripper_group = moveit_commander.MoveGroupCommander("gripper")

        # 设置规划参数
        self.arm_group.set_planning_time(10.0)
        self.max_retry = 3

        rospy.loginfo("初始化完成，系统已准备好执行动作。")
        self.shutdown_requested = False

    def shutdown_handler(self, signum, frame):
        """捕获 Ctrl+C 中断信号"""
        rospy.logwarn("检测到 Ctrl+C，安全关闭系统...")
        self.shutdown_requested = True
        self.arm_group.stop()
        self.arm_group.clear_pose_targets()
        moveit_commander.roscpp_shutdown()
        sys.exit(0)

    def sync_current_state(self):
        """同步机械臂当前状态"""
        rospy.loginfo("正在同步机械臂当前关节状态...")
        current_joints = self.arm_group.get_current_joint_values()
        rospy.loginfo(f"当前关节角度：{np.round(current_joints, 4)}")

    def execute_with_retry(self, action_func, description):
        """统一的重试与终止逻辑"""
        for i in range(1, self.max_retry + 1):
            if self.shutdown_requested:
                rospy.logwarn("检测到关闭请求，中止任务执行。")
                sys.exit(0)

            rospy.loginfo(f"第 {i}/{self.max_retry} 次尝试执行：{description}")
            if action_func():
                rospy.loginfo(f"{description} 成功。")
                return True
            else:
                rospy.logwarn(f"{description} 第 {i} 次执行失败。")

        rospy.logerr(f"{description} 连续 {self.max_retry} 次失败，程序终止。")
        sys.exit(1)

    def move_to_named(self, name):
        """移动到预定义姿态"""
        def action():
            self.arm_group.set_named_target(name)
            success, plan, _, _ = self.arm_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                result = self.arm_group.execute(plan, wait=True)
                self.arm_group.stop()
                self.arm_group.clear_pose_targets()
                return result
            return False

        self.execute_with_retry(action, f"移动到预定义姿态 '{name}'")

    def move_to_pose(self, pose_target):
        """移动到指定位姿"""
        def action():
            pose_goal = geometry_msgs.msg.Pose()
            pose_goal.position.x = pose_target[0]
            pose_goal.position.y = pose_target[1]
            pose_goal.position.z = pose_target[2]
            pose_goal.orientation.x = pose_target[3]
            pose_goal.orientation.y = pose_target[4]
            pose_goal.orientation.z = pose_target[5]
            pose_goal.orientation.w = pose_target[6]

            self.arm_group.set_pose_target(pose_goal)
            success, plan, _, _ = self.arm_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                result = self.arm_group.execute(plan, wait=True)
                self.arm_group.stop()
                self.arm_group.clear_pose_targets()
                return result
            return False

        self.execute_with_retry(action, f"移动到目标位姿 {np.round(pose_target, 4)}")

    def control_gripper(self, action):
        """控制夹爪张开或闭合"""
        def gripper_action():
            self.gripper_group.set_named_target(action)
            success, plan, _, _ = self.gripper_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                return self.gripper_group.execute(plan, wait=True)
            return False

        self.execute_with_retry(gripper_action, f"夹爪动作 '{action}'")

    def execute_sequence(self):
        """执行完整动作序列"""
        try:
            self.sync_current_state()

            # Step 1: 回到 home 并张开夹爪
            self.move_to_named("home")
            self.control_gripper("spread")

            # Step 2: 移动到姿态二
            pose2 = [0.1104, 0.0287, 0.1404, 
                     -0.7294,0.6714, -0.0712, 0.1104]
            self.move_to_pose(pose2)

            # Step 3: 闭合夹爪进行抓取
            self.control_gripper("close")

            # Step 4: 回到 home
            self.move_to_named("home")

            # Step 5: 移动到姿态三
            pose3 = [-0.1144, 0.0114, 0.1433,
                     -0.7122, -0.6723, 0.1324, 0.1525]
            self.move_to_pose(pose3)

            # Step 6: 张开夹爪释放物体
            self.control_gripper("spread")

            # Step 7: 返回 home
            self.move_to_named("home")

            rospy.loginfo("完整动作序列执行完毕。")
        except KeyboardInterrupt:
            self.shutdown_handler(None, None)
        except Exception as e:
            rospy.logerr(f"执行过程中发生错误：{e}")
            sys.exit(1)


if __name__ == "__main__":
    controller = ArmGripperController()
    controller.execute_sequence()

