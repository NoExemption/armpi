#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import os

# -----------------------------
# 配置参数
# -----------------------------
SAVE_DIR = "/home/rosnoetic/图片"  # 保存图片的目录
CAMERA_INDEX = 0                  # USB 摄像头编号
IMG_WIDTH = 680
IMG_HEIGHT = 480


# -----------------------------
# 从 0 开始寻找第一个缺失的编号
# -----------------------------
def find_next_index(path):
    index = 1
    while True:
        filename = f"3rd_img_{index:03d}.jpg"
        if not os.path.exists(os.path.join(path, filename)):
            return index
        index += 1


START_INDEX = find_next_index(SAVE_DIR)


# -----------------------------
# 创建保存目录
# -----------------------------
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)


# -----------------------------
# 打开摄像头
# -----------------------------
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_HEIGHT)

if not cap.isOpened():
    print("无法打开摄像头，请检查连接！")
    exit()

cv2.namedWindow("USB Camera", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("USB Camera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

print("摄像头打开成功。按 Enter 拍照保存，按 'q' 退出。")

count = START_INDEX

while True:
    ret, frame = cap.read()
    if not ret:
        print("读取视频帧失败！")
        break

    cv2.imshow("USB Camera", frame)

    key = cv2.waitKey(1)

    # 强制窗口保持激活，避免切回桌面后按键失效
    cv2.setWindowProperty("USB Camera", cv2.WND_PROP_TOPMOST, 1)

    # Enter
    if key in [13, 10]:
        img_name = f"3rd_img_{count:03d}.jpg"
        save_path = os.path.join(SAVE_DIR, img_name)
        cv2.imwrite(save_path, frame)
        print(f"[INFO] 已保存第 {count + 1} 张照片: {img_name}")

        # 保存一张后，继续寻找下一个未使用编号
        count = find_next_index(SAVE_DIR)

    # q 退出
    elif key == ord('q'):
        print("退出拍照程序。")
        break

cap.release()
cv2.destroyAllWindows()

