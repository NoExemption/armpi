#!/usr/bin/env python3
import rospy
import time
import sys
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory

# 获取src目录下scripts的绝对路径
script_dir = "/home/HwHiAiUser/armpi/src/armpi_gripper_moveit_config/scripts"
sys.path.insert(0, script_dir)

from arm_protocol import ArmProtocol  # 导入通信协议类


class JointStatePublisher:
    def __init__(self):
        rospy.init_node('joint_state_publisher', anonymous=True)
        self.pub = rospy.Publisher('/joint_states', JointState, queue_size=10)
        
        # 关节名称（与URDF和MoveIt配置严格一致）
        self.joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "r_joint"]
        # 关节名称到ID的映射（根据实际物理连接调整）
        self.JOINT_NAME_TO_ID = {
            "joint1": 6,
            "joint2": 5,
            "joint3": 4,
            "joint4": 3,
            "joint5": 2,
            "r_joint": 1
        }
        self.rate = rospy.Rate(50)  # 50Hz发布频率
        
        # 初始化协议通信
        try:
            self.arm_protocol = ArmProtocol(
                port='/dev/ttyUSB0',
                baudrate=9600
            )
            rospy.loginfo("通信协议初始化成功，已连接机械臂")
            time.sleep(2)  # 等待设备稳定
        except Exception as e:
            rospy.logerr(f"协议初始化失败: {e}")
            raise
        
        # 订阅轨迹指令
        self.trajectory_sub = rospy.Subscriber(
            '/armpi_trajectory_cmd', 
            JointTrajectory, 
            self.trajectory_callback,
            queue_size=1  # 只缓存最新轨迹，避免旧轨迹干扰
        )
        self.trajectory_queue = []
        self.executing = False
        rospy.loginfo("关节状态发布器已启动")
    
    def trajectory_callback(self, msg):
        """接收轨迹指令并加入队列（只保留最新轨迹）"""
        if self.trajectory_queue:
            self.trajectory_queue.pop()  # 移除旧轨迹
        self.trajectory_queue.append(msg)
        rospy.loginfo(f"收到新轨迹指令，共{len(msg.points)}个点")

    def execute_trajectory(self, trajectory):
        """同步执行轨迹：同一时间点的所有关节指令批量发送"""
        try:
            points = trajectory.points
            if not points:
                rospy.logwarn("轨迹点为空，跳过执行")
                return
            
            # 记录轨迹开始时间（用于精确控制时间戳）
            trajectory_start_time = rospy.Time.now().to_sec()
            
            for idx, point in enumerate(points):
                # 1. 解析当前轨迹点的目标位置和时间
                target_time = trajectory_start_time + point.time_from_start.to_sec()
                current_time = rospy.Time.now().to_sec()
                
                # 2. 计算需要等待的时间（确保按规划节奏执行）
                sleep_time = target_time - current_time
                if sleep_time > 0:
                    rospy.sleep(sleep_time)  # 使用rospy.sleep提高时间精度
                
                # 3. 收集当前时间点所有关节的ID和目标位置
                joint_ids = []
                target_positions = []
                for name, pos in zip(trajectory.joint_names, point.positions):
                    joint_id = self.JOINT_NAME_TO_ID.get(name)
                    if joint_id is None:
                        rospy.logwarn(f"跳过未知关节: {name}")
                        continue
                    joint_ids.append(joint_id)
                    target_positions.append(pos)
                
                # 4. 批量发送关节指令（同步控制，避免逐个发送的延迟）
                if joint_ids:
                    # 调用协议中的多关节控制方法（假设arm_protocol支持）
                    # 若协议仅支持单关节控制，可在此处实现批量发送逻辑
                    success = self.arm_protocol.set_multiple_joints(
                        joint_ids=joint_ids,
                        positions=target_positions,
                        time_ms=0  # 已通过sleep控制时间，此处时间参数无效
                    )
                    if not success:
                        rospy.logwarn(f"轨迹点{idx+1}发送失败")
            
            rospy.loginfo(f"轨迹执行完成，共{len(points)}个点")
        except Exception as e:
            rospy.logerr(f"执行轨迹时出错: {e}")
    
    def read_joint_positions(self):
        """一次性读取所有关节角度（简化逻辑，直接使用协议返回的弧度值）"""
        try:
            # 一次性读取所有关节ID（按正确顺序排列）
            all_ids = [6, 5, 4, 3, 2, 1]  # 对应joint1到r_joint
            all_angles = self.arm_protocol.get_joint_angles(all_ids)
            
            # 检查数据完整性
            if not all_angles or len(all_angles) != len(all_ids):
                rospy.logwarn(f"角度数据不完整，实际{len(all_angles)}个，期望{len(all_ids)}个")
                return None
            
            # 直接使用协议返回的弧度值
            return all_angles
            
        except Exception as e:
            rospy.logerr(f"读取关节角度失败: {e}")
            return None
    
    def run(self):
        while not rospy.is_shutdown():
            # 优先执行轨迹队列
            if self.trajectory_queue and not self.executing:
                self.executing = True
                current_traj = self.trajectory_queue.pop(0)
                self.execute_trajectory(current_traj)
                self.executing = False
            
            # 发布关节状态（50Hz）
            positions = self.read_joint_positions()
            if positions:
                joint_state = JointState()
                joint_state.header.stamp = rospy.Time.now()
                joint_state.name = self.joint_names
                joint_state.position = positions
                self.pub.publish(joint_state)
            
            self.rate.sleep()


if __name__ == '__main__':
    try:
        publisher = JointStatePublisher()
        publisher.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点已停止")
