import rospy
import sys
import os
# 获取src目录下scripts的绝对路径
script_dir = "/home/HwHiAiUser/armpi/src/armpi_gripper_moveit_config/scripts"
# 将该路径添加到模块搜索的最前面（优先于devel目录）
sys.path.insert(0, script_dir)
from arm_protocol import ArmProtocol

def test_ros_node():
    rospy.init_node('arm_protocol_test')
    
    # 初始化协议
    try:
        protocol = ArmProtocol('/dev/ttyUSB0', 9600)
        rospy.loginfo("协议初始化成功")
    except Exception as e:
        rospy.logerr(f"协议初始化失败: {e}")
        return
    
    # 循环读取关节角度和电池电压并发布
    rate = rospy.Rate(1)  # 1Hz
    while not rospy.is_shutdown():
        # 获取关节角度
        angles = protocol.get_joint_angles()
        if angles:
            rospy.loginfo(f"关节角度(弧度): {[round(angle, 4) for angle in angles]}")
        else:
            rospy.logwarn("未获取到关节角度")
        
        # 获取电池电压
        voltage = protocol.get_battery_voltage()
        if voltage is not None:
            rospy.loginfo(f"电池电压: {voltage} mV ({voltage / 1000.0} V)")
        else:
            rospy.logwarn("未获取到电池电压")
        
        rate.sleep()

if __name__ == '__main__':
    try:
        test_ros_node()
    except rospy.ROSInterruptException:
        rospy.loginfo("节点已停止")
