import serial
import struct
import time

class ArmProtocol:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1.0)
        self.frame_header = b'\x55\x55'  # 协议固定帧头
        # 每个舵机的角度到弧度转换参数 (斜率, 截距)
        self.conversion_params = {
            1: (0.00314, -1.9),
            2: (0.00418, -2.09),
            3: (0.00418, -2.09),
            4: (-0.00418, 2.09),
            5: (0.00314, -1.57),
            6: (0.00418, -2.09)
        }
        self.last_print_time = 0  # 上一次打印时间
        print(f"协议初始化成功 - 端口: {port}, 波特率: {baudrate}")

    def _should_print(self):
        """判断是否超过60秒可以打印一次"""
        now = time.time()
        if now - self.last_print_time >= 60:
            self.last_print_time = now
            return True
        return False

    def send_command(self, cmd, params=b'', need_response=True):
        """发送指令，根据指令类型决定是否接收响应"""
        length = len(params) + 2  # 参数个数 + 2（指令字节 + 长度字节本身）
        if length > 255:
            raise ValueError(f"参数过长，长度 {length} 超过255")
            
        # 构建完整帧
        frame = (
            self.frame_header
            + length.to_bytes(1, 'big')
            + cmd.to_bytes(1, 'big')
            + params
        )
        
        # 控制打印频率
        if self._should_print():
            print(f"发送帧: {frame.hex()}")
        
        self.ser.reset_input_buffer()
        self.ser.write(frame)
        
        if need_response:
            return self._receive_response(cmd)
        else:
            return None

    def _receive_response(self, expected_cmd):
        """接收并解析响应帧"""
        # 读取帧头（2字节）
        header = self.ser.read(2)
        if header != self.frame_header:
            if self._should_print():
                print(f"帧头错误，收到: {header.hex()}")
            return None
            
        # 读取长度和指令
        length = int.from_bytes(self.ser.read(1), 'big')
        cmd = int.from_bytes(self.ser.read(1), 'big')
        if self._should_print():
            print(f"接收响应 - 长度: {length}, 指令: {cmd}")
        
        # 验证指令是否匹配
        if cmd != expected_cmd:
            if self._should_print():
                print(f"指令不匹配，预期: {expected_cmd}, 收到: {cmd}")
            return None
            
        # 读取参数（长度 - 2：减去指令和长度本身）
        params = self.ser.read(length - 2)
        if self._should_print():
            print(f"接收参数: {params.hex()}")
        
        return params

    # ===== 关节控制方法 =====
    def get_joint_angles(self, servo_ids=[1, 2, 3, 4, 5, 6]):
        """获取多个关节角度（使用新的线性转换关系）"""
        # 构建参数：舵机个数 + 舵机ID列表
        num_servos = len(servo_ids).to_bytes(1, 'big')
        params = num_servos + b''.join([id_.to_bytes(1, 'big') for id_ in servo_ids])
        
        # 发送读取角度指令（CMD_MULT_SERVO_POS_READ = 21，需要响应）
        response_params = self.send_command(cmd=21, params=params)
        if not response_params:
            return None
            
        # 解析响应参数
        try:
            num = response_params[0]  # 实际返回的舵机个数
            angles_rad = []
            for i in range(num):
                id_pos = 1 + i*3  # ID的位置
                servo_id = response_params[id_pos]
                angle_low = response_params[id_pos + 1]
                angle_high = response_params[id_pos + 2]
                angle_value = (angle_high << 8) | angle_low  # 合并为16位整数
                
                # 使用对应舵机的线性转换参数计算弧度值
                if servo_id in self.conversion_params:
                    slope, intercept = self.conversion_params[servo_id]
                    rad = slope * angle_value + intercept
                    angles_rad.append(rad)
                else:
                    if self._should_print():
                        print(f"未知舵机ID: {servo_id}，使用默认转换")
                    # 保留原转换作为 fallback
                    angles_rad.append(angle_value * 0.24 * 3.1415926 / 180.0)
                
            return angles_rad
            
        except Exception as e:
            if self._should_print():
                print(f"解析角度失败: {e}")
            return None
            
    def set_joint_position(self, joint_id, position, time_ms=500):
        """设置单个关节位置（使用新的线性转换关系）"""
        if joint_id not in self.conversion_params:
            if self._should_print():
                print(f"未知舵机ID: {joint_id}，使用默认转换")
            angle_value = int(position * 180.0 / 3.1415926 / 0.24)
        else:
            slope, intercept = self.conversion_params[joint_id]
            angle_value = int((position - intercept) / slope)
        
        angle_value = max(0, min(1000, angle_value))
        time_low = time_ms & 0xFF
        time_high = (time_ms >> 8) & 0xFF
        angle_low = angle_value & 0xFF
        angle_high = (angle_value >> 8) & 0xFF
        
        params = (
            b'\x01'  # 舵机个数
            + time_low.to_bytes(1, 'big')
            + time_high.to_bytes(1, 'big')
            + joint_id.to_bytes(1, 'big')
            + angle_low.to_bytes(1, 'big')
            + angle_high.to_bytes(1, 'big')
        )
        
        self.send_command(cmd=3, params=params, need_response=False)
        return True

    def set_multiple_joints(self, joint_ids, positions, time_ms=500):
        """批量设置多个关节位置（同步控制）"""
        if len(joint_ids) != len(positions):
            if self._should_print():
                print("关节ID与位置列表长度不匹配")
            return False
            
        num_joints = len(joint_ids)
        if num_joints == 0:
            if self._should_print():
                print("未指定关节")
            return False
            
        time_low = time_ms & 0xFF
        time_high = (time_ms >> 8) & 0xFF
        
        params = (
            num_joints.to_bytes(1, 'big')
            + time_low.to_bytes(1, 'big')
            + time_high.to_bytes(1, 'big')
        )
        
        for joint_id, pos in zip(joint_ids, positions):
            if joint_id not in self.conversion_params:
                if self._should_print():
                    print(f"未知舵机ID: {joint_id}，使用默认转换")
                angle_value = int(pos * 180.0 / 3.1415926 / 0.24)
            else:
                slope, intercept = self.conversion_params[joint_id]
                angle_value = int((pos - intercept) / slope)
            angle_value = max(0, min(1000, angle_value))
            angle_low = angle_value & 0xFF
            angle_high = (angle_value >> 8) & 0xFF
            params += joint_id.to_bytes(1, 'big') + angle_low.to_bytes(1, 'big') + angle_high.to_bytes(1, 'big')
        
        self.send_command(cmd=3, params=params, need_response=False)
        return True
        
    # ===== 调试辅助方法 =====
    def get_battery_voltage(self):
        """获取电池电压（用于调试通信）"""
        response_params = self.send_command(cmd=15, params=b'')
        if not response_params or len(response_params) != 2:
            if self._should_print():
                print("获取电压失败")
            return None
            
        voltage = (response_params[1] << 8) | response_params[0]
        if self._should_print():
            print(f"电池电压: {voltage} mV")
        return voltage

