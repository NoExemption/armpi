#!/usr/bin/env python3
import rospy, sys, os
import moveit_commander
import actionlib
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal

class MoveItTrajectoryExecutor:
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node('moveit_trajectory_executor', anonymous=True)

        self.manipulator = moveit_commander.MoveGroupCommander('manipulator')
        self.gripper = moveit_commander.MoveGroupCommander('gripper')

        self.manipulator.set_goal_joint_tolerance(0.001)
        self.manipulator.set_max_acceleration_scaling_factor(0.2)
        self.manipulator.set_max_velocity_scaling_factor(0.2)
        self.gripper.set_goal_joint_tolerance(0.001)
        self.gripper.set_max_acceleration_scaling_factor(0.1)
        self.gripper.set_max_velocity_scaling_factor(0.1)

        self.manipulator_joints = ["joint1", "joint2", "joint3", "joint4", "joint5"]
        self.gripper_joints = ["r_joint"]

        self.manipulator_client = actionlib.SimpleActionClient(
            "manipulator_controller/follow_joint_trajectory",
            FollowJointTrajectoryAction
        )
        self.gripper_client = actionlib.SimpleActionClient(
            "gripper_controller/follow_joint_trajectory",
            FollowJointTrajectoryAction
        )

        if not self.manipulator_client.wait_for_server(rospy.Duration(10)):
            rospy.logerr("机械臂Action Server连接超时，准备退出")
            os._exit(1)
        if not self.gripper_client.wait_for_server(rospy.Duration(10)):
            rospy.logerr("夹爪Action Server连接超时，准备退出")
            os._exit(1)
        rospy.loginfo("所有Action Server已连接")

        self.execute_sequence()

        moveit_commander.roscpp_shutdown()
        os._exit(0)

    def plan_and_execute_manipulator(self, target_joints, step_name):
        rospy.loginfo(f"开始执行：{step_name}（目标角度：{target_joints}）")
        try:
            self.manipulator.set_joint_value_target(dict(zip(self.manipulator_joints, target_joints)))
            plan_success, trajectory, planning_time, error_code = self.manipulator.plan()
            if not plan_success:
                rospy.logerr(f"{step_name}：轨迹规划失败，准备退出")
                os._exit(1)

            if not trajectory.joint_trajectory.points:
                rospy.logerr(f"{step_name}：轨迹为空，准备退出")
                os._exit(1)

            goal = FollowJointTrajectoryGoal()
            goal.trajectory = trajectory.joint_trajectory
            traj_duration = trajectory.joint_trajectory.points[-1].time_from_start.to_sec()
            rospy.loginfo(f"{step_name}：轨迹时长 {traj_duration:.2f}秒")

            self.manipulator_client.send_goal(goal)
            success = self.manipulator_client.wait_for_result(rospy.Duration(traj_duration + 8))
            if not success:
                rospy.logerr(f"{step_name}：执行超时，准备退出")
                os._exit(1)

            result = self.manipulator_client.get_result()
            if result.error_code != 0:
                rospy.logerr(f"{step_name}：执行失败，错误码：{result.error_code}，准备退出")
                os._exit(1)

            rospy.loginfo(f"{step_name}：执行成功（耗时~{traj_duration:.1f}秒）")
            return True
        except Exception as e:
            rospy.logerr(f"{step_name}：执行异常：{e}，准备退出")
            os._exit(1)

    def plan_and_execute_gripper(self, target_angle, action_name):
        rospy.loginfo(f"开始执行：{action_name}（目标角度：{target_angle}）")
        try:
            self.gripper.set_joint_value_target({self.gripper_joints[0]: target_angle})
            plan_success, trajectory, planning_time, error_code = self.gripper.plan()
            if not plan_success:
                rospy.logerr(f"{action_name}：轨迹规划失败，准备退出")
                os._exit(1)

            if not trajectory.joint_trajectory.points:
                rospy.logerr(f"{action_name}：轨迹为空，准备退出")
                os._exit(1)

            goal = FollowJointTrajectoryGoal()
            goal.trajectory = trajectory.joint_trajectory
            traj_duration = trajectory.joint_trajectory.points[-1].time_from_start.to_sec()
            rospy.loginfo(f"{action_name}：轨迹时长 {traj_duration:.2f}秒")

            self.gripper_client.send_goal(goal)
            success = self.gripper_client.wait_for_result(rospy.Duration(traj_duration + 5))
            if not success:
                rospy.logerr(f"{action_name}：执行超时，准备退出")
                os._exit(1)

            result = self.gripper_client.get_result()
            if result.error_code != 0:
                rospy.logerr(f"{action_name}：执行失败，错误码：{result.error_code}，准备退出")
                os._exit(1)

            rospy.loginfo(f"{action_name}：执行成功（耗时~{traj_duration:.1f}秒）")
            return True
        except Exception as e:
            rospy.logerr(f"{action_name}：执行异常：{e}，准备退出")
            os._exit(1)

    def execute_sequence(self):
        try:
            pose1 = [0.000, -0.022, -0.008, 0.067, 0.071]
            pose2 = [-1.83, 0.15, -1.75, -0.99, -0.13]
            pose3 = [1.731, 0.14, -1.662, -1.109, 0.0945]
            gripper_open = -1.57
            gripper_close = 0.0

            rospy.loginfo("===== 开始执行完整动作序列 =====")

            rospy.loginfo("\n===== 步骤1：回到初始态 =====")
            if not self.plan_and_execute_manipulator(pose1, "机械臂回到初始态"):
                rospy.logerr("步骤1机械臂失败，准备退出")
                os._exit(1)
            rospy.sleep(2)

            if not self.plan_and_execute_gripper(gripper_open, "夹爪张开"):
                rospy.logerr("步骤1夹爪失败，准备退出")
                os._exit(1)
            rospy.sleep(2)

            rospy.loginfo("\n===== 步骤2：运动到姿态2 =====")
            if not self.plan_and_execute_manipulator(pose2, "运动到姿态2"):
                rospy.logerr("步骤2失败，准备退出")
                os._exit(1)
            rospy.sleep(3)

            rospy.loginfo("\n===== 步骤3：夹爪闭合 =====")
            if not self.plan_and_execute_gripper(gripper_close, "夹爪闭合"):
                rospy.logerr("步骤3失败，准备退出")
                os._exit(1)
            rospy.sleep(3)

            rospy.loginfo("\n===== 步骤4：运动到姿态3 =====")
            if not self.plan_and_execute_manipulator(pose3, "运动到姿态3"):
                rospy.logerr("步骤4失败，准备退出")
                os._exit(1)
            rospy.sleep(3)

            rospy.loginfo("\n===== 步骤5：夹爪张开 =====")
            if not self.plan_and_execute_gripper(gripper_open, "夹爪张开"):
                rospy.logerr("步骤5失败，准备退出")
                os._exit(1)
            rospy.sleep(3)

            rospy.loginfo("\n===== 步骤6：返回初始态 =====")
            if not self.plan_and_execute_manipulator(pose1, "返回初始态"):
                rospy.logerr("步骤6失败，准备退出")
                os._exit(1)
            rospy.sleep(3)

            rospy.loginfo("\n===== 完整动作组执行完毕 =====")
            os._exit(1)

        except Exception as e:
            rospy.logerr(f"流程执行异常：{e}，准备退出")
            os._exit(1)

if __name__ == "__main__":
    try:
        MoveItTrajectoryExecutor()
    except rospy.ROSInterruptException:
        rospy.loginfo("程序被中断，准备退出")
        os._exit(1)

