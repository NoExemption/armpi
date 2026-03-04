#!/usr/bin/env python3
import rospy
import actionlib
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal, FollowJointTrajectoryResult
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import sys

# 控制器命名空间
MANIPULATOR_NS = "manipulator_controller"
GRIPPER_NS = "gripper_controller"

# 关节名称
MANIPULATOR_JOINTS = [
    "joint1", "joint2", "joint3", "joint4", "joint5"
]
GRIPPER_JOINTS = [
    "r_joint"
]

class FarsightActionServer:
    def __init__(self):
        # 创建机械臂Action Server
        self.manipulator_server = actionlib.SimpleActionServer(
            f"{MANIPULATOR_NS}/follow_joint_trajectory",
            FollowJointTrajectoryAction,
            execute_cb=self.execute_manipulator_callback,
            auto_start=False
        )
        
        # 创建夹爪Action Server
        self.gripper_server = actionlib.SimpleActionServer(
            f"{GRIPPER_NS}/follow_joint_trajectory",
            FollowJointTrajectoryAction,
            execute_cb=self.execute_gripper_callback,
            auto_start=False
        )
        
        # 启动两个服务器
        self.manipulator_server.start()
        self.gripper_server.start()
        
        rospy.loginfo("Farsight Action Server已启动，等待机械臂和夹爪轨迹指令...")
        self.trajectory_pub = rospy.Publisher('/armpi_trajectory_cmd', JointTrajectory, queue_size=10)

    def execute_manipulator_callback(self, goal):
        """处理接收到的机械臂轨迹目标"""
        result = FollowJointTrajectoryResult()
        
        try:
            trajectory = goal.trajectory
            n_joints = len(trajectory.joint_names)
            n_points = len(trajectory.points)
            
            rospy.loginfo(f"接收到机械臂轨迹：{n_joints}个关节，{n_points}个路点")

            # 打印轨迹信息（保持原有日志格式）
            self.print_simplified_trajectory(trajectory, "机械臂")

            # 验证关节名称是否匹配
            if not all(joint in MANIPULATOR_JOINTS for joint in trajectory.joint_names):
                rospy.logerr("关节名称与机械臂配置不匹配！")
                result.error_code = FollowJointTrajectoryResult.INVALID_JOINTS
                self.manipulator_server.set_aborted(result)
                return

            # 发送轨迹
            success = self.send_full_trajectory(trajectory)
            
            if success:
                result.error_code = FollowJointTrajectoryResult.SUCCESSFUL
                self.manipulator_server.set_succeeded(result)
                rospy.loginfo("机械臂轨迹执行成功")
            else:
                result.error_code = FollowJointTrajectoryResult.PATH_TOLERANCE_VIOLATED
                self.manipulator_server.set_aborted(result)
                rospy.logerr("机械臂轨迹执行失败")

        except Exception as e:
            rospy.logerr(f"处理机械臂轨迹时出错：{str(e)}")
            result.error_code = FollowJointTrajectoryResult.INVALID_GOAL
            self.manipulator_server.set_aborted(result)

    def execute_gripper_callback(self, goal):
        """处理接收到的夹爪轨迹目标"""
        result = FollowJointTrajectoryResult()
        
        try:
            trajectory = goal.trajectory
            n_joints = len(trajectory.joint_names)
            n_points = len(trajectory.points)
            
            rospy.loginfo(f"接收到夹爪轨迹：{n_joints}个关节，{n_points}个路点")
            self.print_simplified_trajectory(trajectory, "夹爪")

            if not all(joint in GRIPPER_JOINTS for joint in trajectory.joint_names):
                rospy.logerr("关节名称与夹爪配置不匹配！")
                result.error_code = FollowJointTrajectoryResult.INVALID_JOINTS
                self.gripper_server.set_aborted(result)
                return

            # 发送轨迹
            success = self.send_full_trajectory(trajectory)
            
            if success:
                result.error_code = FollowJointTrajectoryResult.SUCCESSFUL
                self.gripper_server.set_succeeded(result)
                rospy.loginfo("夹爪轨迹执行成功")
            else:
                result.error_code = FollowJointTrajectoryResult.PATH_TOLERANCE_VIOLATED
                self.gripper_server.set_aborted(result)
                rospy.logerr("夹爪轨迹执行失败")

        except Exception as e:
            rospy.logerr(f"处理夹爪轨迹时出错：{str(e)}")
            result.error_code = FollowJointTrajectoryResult.INVALID_GOAL
            self.gripper_server.set_aborted(result)

    def print_simplified_trajectory(self, trajectory, controller_type):
        """打印轨迹的位置和时间信息"""
        rospy.loginfo(f"===== {controller_type}轨迹信息 =====")
        rospy.loginfo(f"关节名称: {trajectory.joint_names}")
        max_points_to_print = min(5, len(trajectory.points))
        for i in range(max_points_to_print):
            point = trajectory.points[i]
            time_from_start = point.time_from_start.to_sec()
            positions = [f"{pos:.2f}" for pos in point.positions]
            rospy.loginfo(f"轨迹点 {i+1}/{len(trajectory.points)} (t={time_from_start:.2f}s):")
            rospy.loginfo(f"  位置: {positions}")
        if len(trajectory.points) > max_points_to_print:
            rospy.loginfo(f"... 省略剩余 {len(trajectory.points) - max_points_to_print} 个轨迹点")
        rospy.loginfo("=====================================")

    def send_full_trajectory(self, trajectory):
        """直接发送完整轨迹"""
        try:
            self.trajectory_pub.publish(trajectory)
            rospy.loginfo("完整轨迹已发布")
            return True
        except Exception as e:
            rospy.logerr(f"发送轨迹时出错: {e}")
            return False

if __name__ == "__main__":
    try:
        rospy.init_node("farsight_moveit_action_server")
        server = FarsightActionServer()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点被中断")
    except Exception as e:
        rospy.logerr(f"节点启动失败：{str(e)}")

