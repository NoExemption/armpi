#!/usr/bin/env python3
import rospy
import moveit_commander
import geometry_msgs.msg
import tf
import tf.transformations as tft
import numpy as np
import yaml, sys, signal, os

class ArucoPickPlace:
    def __init__(self):
        """初始化 MoveIt 与标定"""
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node('aruco_pick_place', anonymous=True)

        signal.signal(signal.SIGINT, self.shutdown_handler)
        self.shutdown_requested = False

        rospy.loginfo("初始化 MoveIt 控制器...")
        self.robot = moveit_commander.RobotCommander()
        self.scene = moveit_commander.PlanningSceneInterface()
        self.arm_group = moveit_commander.MoveGroupCommander("manipulator")
        self.gripper_group = moveit_commander.MoveGroupCommander("gripper")
        self.arm_group.set_planning_time(10.0)
        self.max_retry = 3

        # 读取手眼标定
        calib_file = "/home/rosnoetic/armpi/src/armpi_demo/config/handeye_calibrate.yaml"
        if not os.path.exists(calib_file):
            rospy.logerr("标定文件不存在: %s" % calib_file)
            sys.exit(1)
        with open(calib_file, "r") as f:
            data = yaml.safe_load(f)
        self.R_cam2gripper = np.array(data["R_cam2gripper"])
        self.t_cam2gripper = np.array(data["t_cam2gripper"]).flatten()
        rospy.loginfo("加载标定结果成功。")

        # 订阅aruco位姿
        rospy.Subscriber("/aruco_single/pose", geometry_msgs.msg.PoseStamped, self.marker_cb)
        self.marker_pose = None

    def shutdown_handler(self, signum, frame):
        rospy.logwarn("检测到 Ctrl+C，安全关闭系统...")
        self.shutdown_requested = True
        self.arm_group.stop()
        moveit_commander.roscpp_shutdown()
        sys.exit(0)

    def marker_cb(self, msg):
        """接收marker位姿并保存（相机坐标系下）"""
        self.marker_pose = msg

    def execute_with_retry(self, action_func, description):
        for i in range(1, self.max_retry + 1):
            if self.shutdown_requested:
                rospy.logwarn("检测到关闭请求，中止任务。")
                sys.exit(0)
            rospy.loginfo(f"第 {i}/{self.max_retry} 次执行：{description}")
            if action_func():
                rospy.loginfo(f"{description} 成功。")
                return True
            rospy.logwarn(f"{description} 第 {i} 次失败。")
        rospy.logerr(f"{description} 连续 {self.max_retry} 次失败，程序终止。")
        sys.exit(1)

    def move_to_named(self, name):
        def action():
            self.arm_group.set_named_target(name)
            success, plan, _, _ = self.arm_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                return self.arm_group.execute(plan, wait=True)
            return False
        self.execute_with_retry(action, f"移动到预定义姿态 '{name}'")

    def move_to_pose(self, pose):
        def action():
            pose_goal = geometry_msgs.msg.Pose()
            pose_goal.position.x, pose_goal.position.y, pose_goal.position.z = pose[:3]
            pose_goal.orientation.x, pose_goal.orientation.y, pose_goal.orientation.z, pose_goal.orientation.w = pose[3:]
            self.arm_group.set_pose_target(pose_goal)
            success, plan, _, _ = self.arm_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                return self.arm_group.execute(plan, wait=True)
            return False
        self.execute_with_retry(action, f"移动到目标位姿 {np.round(pose, 4)}")

    def control_gripper(self, action):
        def gripper_action():
            self.gripper_group.set_named_target(action)
            success, plan, _, _ = self.gripper_group.plan()
            if success and len(plan.joint_trajectory.points) > 0:
                return self.gripper_group.execute(plan, wait=True)
            return False
        self.execute_with_retry(gripper_action, f"夹爪动作 '{action}'")

    def get_marker_in_gripper(self):
        """将 marker 位姿从相机系转换到 gripper 系"""
        msg = self.marker_pose
        if msg is None:
            rospy.logwarn("等待检测到 ArUco marker...")
            rospy.sleep(0.1)
            return None

        # marker在相机系下
        p_cam = np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])
        q_cam = [msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w]
        T_marker_cam = tft.quaternion_matrix(q_cam)
        T_marker_cam[0:3, 3] = p_cam

        # 相机→夹爪变换
        T_cam2gripper = np.eye(4)
        T_cam2gripper[:3, :3] = self.R_cam2gripper
        T_cam2gripper[:3, 3] = self.t_cam2gripper

        # marker在基坐标下
        T_marker_gripper = np.dot(np.linalg.inv(T_cam2gripper), T_marker_cam)
        pos = T_marker_gripper[:3, 3]
        quat = tft.quaternion_from_matrix(T_marker_gripper)
        return np.hstack((pos, quat))

    def execute_sequence(self):
        """执行抓取流程：识别→抓取→放置"""
        home_pose = [0.0305,0.0087,0.2822,
	-0.3981,0.3298,-0.4832,0.7066]
        self.move_to_pose(home_pose)
        self.control_gripper("spread")

        rospy.loginfo("等待识别到 ArUco marker...")
        while not rospy.is_shutdown() and self.marker_pose is None:
            rospy.sleep(0.2)

        rospy.loginfo("检测到 marker，计算抓取位姿...")
        target_pose = self.get_marker_in_gripper()
        if target_pose is None:
            rospy.logerr("无法获取 marker 位姿")
            sys.exit(1)

        # 直接移动到 marker 位姿
        self.move_to_pose(target_pose)
        self.control_gripper("close")

        # 抓取后直接移动到目标位姿
        place_pose = [0.0059, -0.0785, 0.1760, 0.9698, 0.0731, 0.0000, 0.2328]
        self.move_to_pose(place_pose)
        self.control_gripper("spread")

        rospy.loginfo("抓取并放置任务完成。")

if __name__ == "__main__":
    node = ArucoPickPlace()
    node.execute_sequence()

