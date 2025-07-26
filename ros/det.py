# cd python
# python det.py

#!/usr/bin/env python3
import requests
import json
import rclpy
from rclpy.node import Node
from ai_msgs.msg import PerceptionTargets

import time
import sys, os

base_url = "http://192.168.144.251"

# 设置舵机角度
def set_servo_angle(angle):
    url = f"{base_url}/api/servo?angle={angle}"
    response = requests.get(url)
    return response.json()

# 舵机回中
def center_servo():
    url = f"{base_url}/api/servo/center"
    response = requests.get(url)
    return response.json()

# 获取状态
def get_status():
    url = f"{base_url}/api/status"
    response = requests.get(url)
    return response.json()

# 示例并行函数：模拟水流检测循环
def detect_water_jet_fast_loop():
    for _ in range(5):  # 运行 5 次
        print("Detecting water jet...")
        time.sleep(1)  # 模拟处理时间
    print("Water jet detection completed.")

class BodyDetectionSubscriber(Node):
    def __init__(self):
        super().__init__('body_detection_subscriber')
        self.max_area = 180000
        self.max_rect = None
        self.subscription = self.create_subscription(
            PerceptionTargets,
            '/hobot_mono2d_body_detection',
            self.callback,
            10
        )
        self.get_logger().info('Subscribed to /hobot_mono2d_body_detection topic.')

    def callback(self, msg):
        max_area = 0
        max_rect = None
        for target in msg.targets:
            for roi in target.rois:
                if roi.type == 'body':
                    area = roi.rect.height * roi.rect.width
                    if area > max_area:
                        max_area = area
                        max_rect = roi.rect
        if max_area > self.max_area:
            # self.max_area = max_area  # 注释掉以保持原始阈值
            self.max_rect = max_rect
            self.get_logger().info(
                f'New max area: {max_area}, '
                f'height: {self.max_rect.height}, width: {self.max_rect.width}'
            )
            set_servo_angle(80)
        else:
            status = get_status()
            print(status)
            if status['data']['current_angle'] > 0:
                set_servo_angle(0)

def main_det(args=None):
    status = get_status()
    if status['data']['current_angle'] != 0:
        set_servo_angle(0)

    rclpy.init(args=args)
    node = BodyDetectionSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down subscriber.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main_det()