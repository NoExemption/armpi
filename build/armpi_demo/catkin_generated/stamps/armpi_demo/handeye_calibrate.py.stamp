#!/usr/bin/env python3
import yaml
import numpy as np
import cv2
from tf.transformations import quaternion_matrix, quaternion_from_matrix

# 配置路径
dataset_file = "/home/rosnoetic/armpi/src/armpi_demo/config/handeye_dataset.yaml"
output_file = "/home/rosnoetic/armpi/src/armpi_demo/config/handeye_calibrate.yaml"

# 读取采集数据
with open(dataset_file, "r") as f:
    dataset = yaml.safe_load(f)

gripper_poses = dataset.get('gripper_poses', [])
marker_poses = dataset.get('marker_poses', [])

if len(gripper_poses) != len(marker_poses):
    raise ValueError("末端位姿和 marker 位姿数量不一致")

print(f"读取到 {len(gripper_poses)} 组数据，用于手眼标定。")

# 转换为 4x4 矩阵
def pose_to_matrix(p):
    q = [p['orientation']['x'], p['orientation']['y'], p['orientation']['z'], p['orientation']['w']]
    T = quaternion_matrix(q)
    T[0:3, 3] = [p['position']['x'], p['position']['y'], p['position']['z']]
    return T

gripper_matrices = [pose_to_matrix(g) for g in gripper_poses]
marker_matrices = [pose_to_matrix(m) for m in marker_poses]

# 计算增量变换
def compute_deltas(matrices):
    R_list = []
    t_list = []
    for i in range(1, len(matrices)):
        T_prev = matrices[i-1]
        T_curr = matrices[i]
        # 增量变换
        T_delta = np.linalg.inv(T_prev) @ T_curr
        R_list.append(T_delta[0:3, 0:3])
        t_list.append(T_delta[0:3, 3])
    return R_list, t_list

# Eye-in-Hand 模式：末端变化导致相机观测 Marker 变化
R_gripper2base, t_gripper2base = compute_deltas(gripper_matrices)
R_target2cam, t_target2cam = compute_deltas(marker_matrices)

# 手眼标定
R_cam2gripper, t_cam2gripper = cv2.calibrateHandEye(
    R_gripper2base, t_gripper2base,
    R_target2cam, t_target2cam,
    method=cv2.CALIB_HAND_EYE_TSAI
)

print("\n手眼标定结果：")
print("R_cam2gripper:\n", R_cam2gripper)
print("t_cam2gripper:\n", t_cam2gripper)

# 保存结果
handeye_result = {
    'R_cam2gripper': R_cam2gripper.tolist(),
    't_cam2gripper': t_cam2gripper.tolist()
}

with open(output_file, 'w') as f:
    yaml.dump(handeye_result, f)

print(f"\n标定结果已保存到: {output_file}")

