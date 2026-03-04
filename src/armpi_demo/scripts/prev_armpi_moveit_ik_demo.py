#!/usr/bin/env python3
import rospy, sys
import moveit_commander
import os
import signal
from geometry_msgs.msg import PoseStamped

class MoveItIkThreePoses:
    def __init__(self):
        # 初始化move_group的API
        moveit_commander.roscpp_initialize(sys.argv)

        # 初始化ROS节点
        rospy.init_node('moveit_ik_three_poses', anonymous=True)
        
        # 初始化规划组
        self.manipulator = moveit_commander.MoveGroupCommander('manipulator')  # 机械臂主体
        self.gripper = moveit_commander.MoveGroupCommander('gripper')          # 夹爪组
        
        # 获取终端link的名称
        self.end_effector_link = self.manipulator.get_end_effector_link()
        rospy.loginfo(f"终端link名称: {self.end_effector_link}")
                        
        # 设置参考坐标系
        self.reference_frame = 'base_link'
        self.manipulator.set_pose_reference_frame(self.reference_frame)
        rospy.loginfo(f"参考坐标系: {self.reference_frame}")
        
        # 设置运动参数
        self.manipulator.set_goal_position_tolerance(0.001)       # 位置允许误差(m)
        self.manipulator.set_goal_orientation_tolerance(0.01)    # 姿态允许误差(rad)
        self.manipulator.set_max_acceleration_scaling_factor(0.2)
        self.manipulator.set_max_velocity_scaling_factor(0.2)
        self.manipulator.allow_replanning(True)                   # 允许重规划
        
        self.manipulator.set_planning_time(50)                  # 规划超时时间
        self.manipulator.set_num_planning_attempts(30)     # 规划尝试次数
        rospy.loginfo(f"规划超时时间: {self.manipulator.get_planning_time()}秒, 尝试次数: 30")
        
        self.gripper.set_goal_joint_tolerance(0.001)
        self.gripper.set_max_acceleration_scaling_factor(0.1)
        self.gripper.set_max_velocity_scaling_factor(0.1)
        
        # 夹爪关节名称
        self.gripper_joints = ["r_joint"]
        
        # 执行完整动作流程
        self.execute_sequence()
        
        # 关闭并退出
        moveit_commander.roscpp_shutdown()
        rospy.signal_shutdown("动作执行完毕")
    
    def plan_and_execute_manipulator_ik(self, target_pose, step_name):
        """通过MoveIt规划并自动发送轨迹给Action Server"""
        rospy.loginfo(f"开始执行：{step_name}")
        rospy.loginfo(f"目标位置: x={target_pose.pose.position.x:.4f}, y={target_pose.pose.position.y:.4f}, z={target_pose.pose.position.z:.4f}")
        rospy.loginfo(f"目标姿态: x={target_pose.pose.orientation.x:.4f}, y={target_pose.pose.orientation.y:.4f}, z={target_pose.pose.orientation.z:.4f}, w={target_pose.pose.orientation.w:.4f}")
        
        try:
            # 设置当前状态为初始状态
            self.manipulator.set_start_state_to_current_state()
            
            # 设置目标位姿
            self.manipulator.set_pose_target(target_pose, self.end_effector_link)
            
            # 规划轨迹
            plan_success, trajectory, planning_time, error_code = self.manipulator.plan()
            if not plan_success:
                rospy.logerr(f"{step_name}：执行失败，准备退出")
                os._exit(1)
            
            # 检查轨迹是否为空
            if not trajectory.joint_trajectory.points:
                rospy.logerr(f"{step_name}：执行失败，准备退出")
                os._exit(1)

            
            traj_duration = trajectory.joint_trajectory.points[-1].time_from_start.to_sec()
            rospy.loginfo(f"{step_name}：轨迹时长 {traj_duration:.2f}秒")
            
            # MoveIt内部发送轨迹给Action Server
            execute_success = self.manipulator.execute(trajectory, wait=True)
            
            if not execute_success:
                rospy.logerr(f"{step_name}：执行失败，准备退出")
                os._exit(1)

            
            rospy.loginfo(f"{step_name}：执行成功（耗时~{traj_duration:.1f}秒）")
            return True
            
        except Exception as e:
            rospy.logerr(f"{step_name}：执行异常：{e}")
            os._exit(1)
    
    def plan_and_execute_gripper(self, target_angle, action_name):
        """夹爪控制（由MoveIt转发轨迹）"""
        rospy.loginfo(f"开始执行：{action_name}（目标角度：{target_angle:.4f}）")
        
        try:
            # 设置目标角度
            self.gripper.set_joint_value_target({self.gripper_joints[0]: target_angle})
            
            # 规划轨迹
            plan_success, trajectory, planning_time, error_code = self.gripper.plan()
            if not plan_success:
                rospy.logerr(f"{action_name}：执行失败，准备退出")
                os._exit(1)
            
            # 检查轨迹是否为空
            if not trajectory.joint_trajectory.points:
                rospy.logerr(f"{action_name}：执行失败，准备退出")
                os._exit(1)

            
            traj_duration = trajectory.joint_trajectory.points[-1].time_from_start.to_sec()
            rospy.loginfo(f"{action_name}：轨迹时长 {traj_duration:.2f}秒")
            
            execute_success = self.gripper.execute(trajectory, wait=True)
            
            if not execute_success:
                rospy.logerr(f"{action_name}：执行失败，准备退出")
                os._exit(1)

            
            rospy.loginfo(f"{action_name}：执行成功（耗时~{traj_duration:.1f}秒）")
            return True
            
        except Exception as e:
            rospy.logerr(f"{action_name}：执行异常：{e}")
            os._exit(1)
    
    def create_pose_stamped(self, x, y, z, ox, oy, oz, ow):
        """创建位姿消息对象"""
        pose = PoseStamped()
        pose.header.frame_id = self.reference_frame
        pose.header.stamp = rospy.Time.now()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.x = ox
        pose.pose.orientation.y = oy
        pose.pose.orientation.z = oz
        pose.pose.orientation.w = ow
        return pose
    
    def execute_sequence(self):
        """执行完整动作序列"""
        try:
            # 定义四个姿态：姿态一 → 中间姿态 → 姿态二 → 姿态三
            pose1 = self.create_pose_stamped(
                0.0006, -0.0140, 0.4222,
                0.0506, -0.0025, 0.0959, 0.9941
            )  # 姿态一（初始高位）
            
            pose2 = self.create_pose_stamped(
                -0.0147,0.1675,0.0710,
	        -0.9530,0.0139,0.0309,0.3011
            )  # 姿态二（目标低位）
            
            pose3 = self.create_pose_stamped(
                0.0158,-0.1570,0.0879,
	        0.9586,0.0662,0.0087,0.2769
            )  # 姿态三
            
            # 夹爪角度参数
            gripper_open = -1.57
            gripper_close = 0.0
            
            rospy.loginfo("===== 开始执行动作序列 =====")
            
            # 步骤1：运动到姿态一
            if not self.plan_and_execute_manipulator_ik(pose1, "运动到姿态一"):
                rospy.logerr("步骤1失败，终止执行")
                return
            rospy.sleep(2)
            
	    # 步骤2：夹爪张开
            if not self.plan_and_execute_gripper(gripper_open, "夹爪张开"):
                rospy.logerr("步骤2失败，终止执行")
                return
            rospy.sleep(2)

            # 步骤3：运动到姿态二
            if not self.plan_and_execute_manipulator_ik(pose2, "运动到姿态二"):
                rospy.logerr("步骤3失败，终止执行")
                return
            rospy.sleep(2)
            
            # 步骤4：夹爪闭合
            if not self.plan_and_execute_gripper(gripper_close, "夹爪闭合"):
                rospy.logerr("步骤4失败，终止执行")
                return
            rospy.sleep(2)
            
            # 步骤5：运动到姿态三
            if not self.plan_and_execute_manipulator_ik(pose3, "运动到姿态三"):
                rospy.logerr("步骤5失败，终止执行")
                return
            rospy.sleep(2)
            
            # 步骤6：夹爪再次张开
            if not self.plan_and_execute_gripper(gripper_open, "夹爪张开"):
                rospy.logerr("步骤6失败，终止执行")
                return
            rospy.sleep(2)
            
            # 步骤7：返回姿态一
            if not self.plan_and_execute_manipulator_ik(pose1, "返回姿态一"):
                rospy.logerr("步骤7失败，终止执行")
                return
            rospy.sleep(2)
            
            rospy.loginfo("\n===== 动作序列执行完毕 =====")
            os._exit(0)
            
        except Exception as e:
            rospy.logerr(f"流程执行异常：{e}")
            # 异常恢复
            rospy.loginfo("尝试异常恢复...")
            self.plan_and_execute_manipulator_ik(pose1, "异常恢复：回到姿态一")
            self.plan_and_execute_gripper(gripper_open, "异常恢复：夹爪张开")

def shutdown_handler(signum, frame):
    rospy.loginfo("收到 Ctrl+C，强制退出")
    try:
        current_instance.manipulator.stop()
        current_instance.gripper.stop()
    except Exception:
        pass
    # 强制立刻退出
    os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    try:
        MoveItIkThreePoses()
    except rospy.ROSInterruptException:
        rospy.loginfo("程序被中断")

