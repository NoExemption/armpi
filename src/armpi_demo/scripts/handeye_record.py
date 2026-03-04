#!/usr/bin/env python3
import rospy
import sys
import yaml
import moveit_commander
from pathlib import Path
from geometry_msgs.msg import PoseStamped
from aruco_msgs.msg import MarkerArray

# 获取机械臂末端位姿
def get_gripper_pose(arm, reference_frame="base_link"):
    current_pose = arm.get_current_pose().pose
    pose = {
        "frame_id": reference_frame,
        "position": {
            "x": round(current_pose.position.x, 6),
            "y": round(current_pose.position.y, 6),
            "z": round(current_pose.position.z, 6)
        },
        "orientation": {
            "x": round(current_pose.orientation.x, 6),
            "y": round(current_pose.orientation.y, 6),
            "z": round(current_pose.orientation.z, 6),
            "w": round(current_pose.orientation.w, 6)
        }
    }
    return pose

# 获取 ArUco marker 位姿
def get_marker_pose():
    msg = rospy.wait_for_message('/aruco_single/pose', PoseStamped)
    pose = {
        "frame_id": msg.header.frame_id,
        "position": {
            "x": round(msg.pose.position.x, 6),
            "y": round(msg.pose.position.y, 6),
            "z": round(msg.pose.position.z, 6)
        },
        "orientation": {
            "x": round(msg.pose.orientation.x, 6),
            "y": round(msg.pose.orientation.y, 6),
            "z": round(msg.pose.orientation.z, 6),
            "w": round(msg.pose.orientation.w, 6)
        }
    }
    return pose

# 主采集函数
def collect_and_save():
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('collect_handeye_data', anonymous=True)

    # 初始化 MoveIt 机械臂
    arm = moveit_commander.MoveGroupCommander('manipulator')
    arm.set_pose_reference_frame('base_link')

    # 保存路径
    save_path = Path("/home/rosnoetic/armpi/src/armpi_demo/config")
    save_path.mkdir(parents=True, exist_ok=True)
    yaml_file = save_path / "handeye_dataset.yaml"

    # 如果文件已存在，先加载已有数据
    dataset = {"gripper_poses": [], "marker_poses": []}
    if yaml_file.exists():
    	with open(yaml_file, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded is not None:
            	dataset = loaded
            else:
            	dataset = {"gripper_poses": [], "marker_poses": []}

    print("按回车采集一组数据，输入 q + 回车退出。")

    while True:
        key = input(">>> ")
        if key.strip().lower() == "q":
            break

        # 获取末端位姿
        gpose = get_gripper_pose(arm)
        # 获取 marker 位姿
        mpose = get_marker_pose()
        if mpose is None:
            rospy.logwarn("未检测到 marker，请重试")
            continue

        dataset["gripper_poses"].append(gpose)
        dataset["marker_poses"].append(mpose)

        # 保存到文件
        with open(yaml_file, "w") as f:
            yaml.dump(dataset, f, sort_keys=False)

        rospy.loginfo(f"已保存一组数据，共 {len(dataset['gripper_poses'])} 组")

    moveit_commander.roscpp_shutdown()
    print("采集完成，数据保存在:", yaml_file)

if __name__ == "__main__":
    try:
        collect_and_save()
    except rospy.ROSInterruptException:
        pass

