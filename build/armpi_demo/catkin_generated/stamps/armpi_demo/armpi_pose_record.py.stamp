#!/usr/bin/env python3
import rospy
import sys
import yaml
from pathlib import Path
import moveit_commander
from geometry_msgs.msg import PoseStamped

def get_next_filename(base_path, base_name, ext):
    """生成递增的文件名（如fixed_pose1.txt不存在则返回，存在则试fixed_pose2.txt）"""
    counter = 1
    while True:
        filename = f"{base_name}{counter}.{ext}"
        file_path = base_path / filename
        if not file_path.exists():
            return file_path
        counter += 1

def save_pose_to_file(pose, base_path):
    """自动保存位姿到TXT文件（文件名自动递增）"""
    # 生成递增的TXT文件名（基础名为fixed_pose）
    txt_file = get_next_filename(base_path, "fixed_pose", "txt")
    
    with open(txt_file, "w") as f:
        # 按指定格式写入：位置一行，姿态一行，逗号分隔
        f.write(f"\t{pose.pose.position.x:.4f},{pose.pose.position.y:.4f},{pose.pose.position.z:.4f},\n")
        f.write(f"\t{pose.pose.orientation.x:.4f},{pose.pose.orientation.y:.4f},{pose.pose.orientation.z:.4f},{pose.pose.orientation.w:.4f}\n")
    
    rospy.loginfo(f"位姿已保存到TXT文件: {txt_file}")
    return txt_file

def save_pose_to_yaml(pose, base_path):
    """自动保存位姿到YAML文件（与TXT文件序号一致）"""
    # 生成与TXT相同序号的YAML文件名
    yaml_file = get_next_filename(base_path, "fixed_pose", "yaml")
    
    data = {
        "frame_id": pose.header.frame_id,
        "position": {
            "x": round(pose.pose.position.x, 4),
            "y": round(pose.pose.position.y, 4),
            "z": round(pose.pose.position.z, 4)
        },
        "orientation": {
            "x": round(pose.pose.orientation.x, 4),
            "y": round(pose.pose.orientation.y, 4),
            "z": round(pose.pose.orientation.z, 4),
            "w": round(pose.pose.orientation.w, 4)
        }
    }
    
    with open(yaml_file, "w") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
    
    rospy.loginfo(f"位姿已保存到YAML文件: {yaml_file}")
    return yaml_file

def get_fixed_pose():
    # 初始化MoveIt
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('get_fixed_pose', anonymous=True)
    
    # 初始化规划组
    arm = moveit_commander.MoveGroupCommander('manipulator')
    reference_frame = 'base_link'
    arm.set_pose_reference_frame(reference_frame)
    
    # 自动获取当前末端位姿（无需用户回车确认）
    current_pose = arm.get_current_pose().pose
    rospy.loginfo(f"\n固定姿态的位姿坐标（{reference_frame}坐标系）：")
    rospy.loginfo(f"位置 x: {current_pose.position.x:.4f}")
    rospy.loginfo(f"位置 y: {current_pose.position.y:.4f}")
    rospy.loginfo(f"位置 z: {current_pose.position.z:.4f}")
    rospy.loginfo(f"姿态四元数 x: {current_pose.orientation.x:.4f}")
    rospy.loginfo(f"姿态四元数 y: {current_pose.orientation.y:.4f}")
    rospy.loginfo(f"姿态四元数 z: {current_pose.orientation.z:.4f}")
    rospy.loginfo(f"姿态四元数 w: {current_pose.orientation.w:.4f}\n")
    
    # 封装位姿消息
    target_pose = PoseStamped()
    target_pose.header.frame_id = reference_frame
    target_pose.header.stamp = rospy.Time.now()
    target_pose.pose = current_pose
    
    # 保存路径（自动创建目录）
    default_path = Path("/home/rosnoetic/armpi/src/armpi_demo/config")
    default_path.mkdir(parents=True, exist_ok=True)
    
    # 自动保存（无需用户确认）
    save_pose_to_file(target_pose, default_path)
    save_pose_to_yaml(target_pose, default_path)
    
    return target_pose

if __name__ == "__main__":
    try:
        get_fixed_pose()
        moveit_commander.roscpp_shutdown()
    except rospy.ROSInterruptException:
        rospy.loginfo("程序被中断")
    except Exception as e:
        rospy.logerr(f"发生错误: {str(e)}")
