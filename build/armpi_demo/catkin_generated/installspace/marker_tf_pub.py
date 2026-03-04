#!/usr/bin/env python3

import rospy
import tf
import tf.transformations as tft
import numpy as np
import yaml
import os
from geometry_msgs.msg import PoseStamped

class MarkerTFPublisher:
    def __init__(self):
        # 读取标定结果
        calib_file = "/home/rosnoetic/armpi/src/armpi_demo/config/handeye_calibrate.yaml"
        if not os.path.exists(calib_file):
            rospy.logerr("标定文件不存在: %s" % calib_file)
            exit(1)

        with open(calib_file, "r") as f:
            calib_data = yaml.safe_load(f)

        self.R = np.array(calib_data["R_cam2gripper"])
        self.t = np.array(calib_data["t_cam2gripper"]).flatten()

        rospy.loginfo("加载手眼标定结果成功")
        rospy.loginfo("R:\n%s" % self.R)
        rospy.loginfo("t:\n%s" % self.t)

        # TF broadcaster
        self.br = tf.TransformBroadcaster()

        # 订阅相机的 marker 位姿
        rospy.Subscriber("/aruco_single/pose", PoseStamped, self.pose_callback)

    def pose_callback(self, msg: PoseStamped):
        # marker 在相机坐标系下的位姿
        p_cam = np.array([msg.pose.position.x,
                          msg.pose.position.y,
                          msg.pose.position.z])
        q_cam = [msg.pose.orientation.x,
                 msg.pose.orientation.y,
                 msg.pose.orientation.z,
                 msg.pose.orientation.w]

        # 相机到gripper的变换矩阵
        T_cam2gripper = np.eye(4)
        T_cam2gripper[0:3, 0:3] = self.R
        T_cam2gripper[0:3, 3] = self.t

        # marker在相机系下的齐次矩阵
        T_marker_cam = tft.quaternion_matrix(q_cam)
        T_marker_cam[0:3, 3] = p_cam

        # 转换到gripper系
        T_marker_gripper = np.dot(np.linalg.inv(T_cam2gripper), T_marker_cam)

        pos = T_marker_gripper[0:3, 3]
        quat = tft.quaternion_from_matrix(T_marker_gripper)

        # 发布TF
        self.br.sendTransform(pos,
                              quat,
                              rospy.Time.now(),
                              "marker_in_gripper",
                              "r_link")

if __name__ == "__main__":
    rospy.init_node('marker_tf_pub')
    MarkerTFPublisher()
    rospy.spin()

