#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from moveit_commander import MoveGroupCommander, roscpp_initialize, roscpp_shutdown
import tf.transformations as tft
import yaml
from pathlib import Path
import sys

class BlueBlockGrasper:
    def __init__(self):
        roscpp_initialize([])
        rospy.init_node('blue_block_grasper', anonymous=True)

        # CV Bridge
        self.bridge = CvBridge()

        # 手眼标定文件
        self.calib_file = Path("/home/rosnoetic/armpi/src/armpi_demo/config/handeye_calibrate.yaml")
        self.R_cam2gripper = None
        self.t_cam2gripper = None
        self.T_cam2gripper = None

        # 摄像头话题
        self.rgb_topic = "/camera/color/image_raw"
        self.depth_topic = "/camera/aligned_depth_to_color/image_raw"
        self.depth_image = None

        # 相机内参（深度相机）
        self.fx = 909.210693359375
        self.fy = 908.8849487304688
        self.cx = 652.5352783203125
        self.cy = 350.0932312011719

        # 蓝色 HSV 范围
        self.lower_blue = np.array([100, 150, 50])
        self.upper_blue = np.array([140, 255, 255])

        # 初始化规划组
        self.manipulator = None
        self.gripper = None

        # 程序状态
        self.task_done = False

        # 运行前检查
        if not self.pre_run_check():
            rospy.logerr("启动前检查未通过，程序终止")
            sys.exit(1)

        rospy.loginfo("蓝色方块抓取节点初始化完成，等待图像数据")

        # 订阅话题
        rospy.Subscriber(self.rgb_topic, Image, self.image_callback)
        rospy.Subscriber(self.depth_topic, Image, self.depth_callback)

    def pre_run_check(self):
        success = True

        # 1️⃣ 检查手眼标定文件
        if not self.calib_file.exists():
            rospy.logerr("手眼标定文件不存在: %s" % str(self.calib_file))
            success = False
        else:
            try:
                with open(self.calib_file, "r") as f:
                    calib_data = yaml.safe_load(f)
                self.R_cam2gripper = np.array(calib_data["R_cam2gripper"])
                self.t_cam2gripper = np.array(calib_data["t_cam2gripper"]).flatten()
                self.T_cam2gripper = np.eye(4)
                self.T_cam2gripper[0:3, 0:3] = self.R_cam2gripper
                self.T_cam2gripper[0:3, 3] = self.t_cam2gripper
                rospy.loginfo("手眼标定文件加载成功")
            except Exception as e:
                rospy.logerr("手眼标定文件加载失败，原因: %s" % str(e))
                success = False

        # 2️⃣ 检查 MoveIt 规划组
        try:
            self.manipulator = MoveGroupCommander('manipulator')
            self.gripper = MoveGroupCommander('gripper')
            rospy.loginfo("MoveIt 规划组加载成功")
        except Exception as e:
            rospy.logerr("MoveIt 规划组加载失败，原因: %s" % str(e))
            success = False

        # 3️⃣ 检查 RGB / Depth 话题是否有发布
        import rosgraph
        master = rosgraph.Master('/rostopic_check')
        try:
            published_topics = [t[0] for t in master.getTopicTypes()]
            if self.rgb_topic not in published_topics:
                rospy.logwarn("RGB 图像话题没有发布: %s" % self.rgb_topic)
            else:
                rospy.loginfo("RGB 图像话题正常")
            if self.depth_topic not in published_topics:
                rospy.logwarn("Depth 图像话题没有发布: %s" % self.depth_topic)
            else:
                rospy.loginfo("Depth 图像话题正常")
        except Exception as e:
            rospy.logwarn("无法检查话题发布状态: %s" % str(e))

        return success

    # ------------------------- 原有回调函数 -------------------------
    def depth_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        except Exception as e:
            rospy.logerr("深度图像转换失败，原因: %s" % str(e))

    def image_callback(self, msg):
        if self.task_done:
            return

        if self.depth_image is None:
            rospy.logwarn("未收到深度图像，无法抓取")
            return

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            rospy.logerr("彩色图像转换失败，原因: %s" % str(e))
            return

        target_pixel = self.detect_blue_block(cv_image)
        if target_pixel is None:
            rospy.logwarn("未检测到蓝色方块")
            return

        cx, cy = target_pixel
        Z = self.depth_image[cy, cx]
        if Z == 0:
            rospy.logwarn("深度值为0，无法抓取")
            return

        p_cam = self.pixel_to_camera(cx, cy, Z)
        self.execute_grasp(p_cam)
        self.task_done = True
        rospy.loginfo("抓取任务已完成，程序将退出")
        rospy.signal_shutdown("任务完成")

    # ------------------------- 原有方法保持不变 -------------------------
    def detect_blue_block(self, cv_image):
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_blue, self.upper_blue)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return None
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        return (cx, cy)

    def pixel_to_camera(self, cx, cy, Z):
        X = (cx - self.cx) * Z / self.fx
        Y = (cy - self.cy) * Z / self.fy
        return np.array([X, Y, Z])

    def execute_grasp(self, p_cam):
        T_block_cam = np.eye(4)
        T_block_cam[0:3, 3] = p_cam
        T_block_cam[0:3, 0:3] = np.eye(3)
        T_block_gripper = np.dot(self.T_cam2gripper, T_block_cam)
        pos_target = T_block_gripper[0:3, 3]
        quat_target = tft.quaternion_from_matrix(T_block_gripper)
        pre_grasp_pos = pos_target.copy()
        pre_grasp_pos[2] += 0.1
        rospy.loginfo("移动到预抓位置")
        self.move_arm(pre_grasp_pos, quat_target)
        rospy.sleep(0.5)
        rospy.loginfo("下降抓取")
        self.move_arm(pos_target, quat_target)
        rospy.sleep(0.5)
        rospy.loginfo("闭合夹爪")
        self.close_gripper()
        rospy.sleep(0.5)
        post_grasp_pos = pos_target.copy()
        post_grasp_pos[2] += 0.1
        rospy.loginfo("抓起物体")
        self.move_arm(post_grasp_pos, quat_target)

    def move_arm(self, position, quaternion):
        pose_goal = self.manipulator.get_current_pose().pose
        pose_goal.position.x = position[0]
        pose_goal.position.y = position[1]
        pose_goal.position.z = position[2]
        pose_goal.orientation.x = quaternion[0]
        pose_goal.orientation.y = quaternion[1]
        pose_goal.orientation.z = quaternion[2]
        pose_goal.orientation.w = quaternion[3]
        self.manipulator.set_pose_target(pose_goal)
        self.manipulator.go(wait=True)

    def close_gripper(self):
        self.gripper.set_named_target("close")
        self.gripper.go(wait=True)

    def open_gripper(self):
        self.gripper.set_named_target("spread")
        self.gripper.go(wait=True)

if __name__ == "__main__":
    try:
        grasper = BlueBlockGrasper()
        rospy.spin()
    except rospy.ROSInterruptException:
        roscpp_shutdown()
        rospy.loginfo("程序被中断并安全退出")

