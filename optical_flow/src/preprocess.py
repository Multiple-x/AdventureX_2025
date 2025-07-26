import cv2
import time

import numpy as np


def create_clahe():
    """创建并返回CLAHE对象用于对比度增强"""
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

def preprocess_frame(frame, scale, clahe):
    """预处理帧: 缩放并应用CLAHE"""
    frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return clahe.apply(gray), frame

def compute_optical_flow(prev_gray, gray, dis_flow):
    """计算光流并返回幅值和角度"""
    flow = dis_flow.calc(prev_gray, gray, None)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    return mag, ang, flow

def visualize_flow(frame, mag, ang, scale):
    """将光流可视化为HSV图像"""
    hsv = np.zeros_like(frame)
    hsv[..., 1] = 255
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    flow_rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return cv2.resize(flow_rgb, (0, 0), fx=1/scale, fy=1/scale)

def detect_water_jet_fast_loop(camera_index=0, scale=0.5, max_history=5, fps=30):
    """检测水柱在水池中的落点并输出坐标"""
    # cap = cv2.VideoCapture(video_path)
    print(2222222222222)
    cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("无法读取视频文件")
        return
    else:
        print("摄像头已打开")

    # 设置 MJPG 格式（更适合高帧率）
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    # 设置分辨率和帧率（根据摄像头支持）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, fps)
    
    # 初始化
    ret, first_frame = cap.read()
    if not ret:
        print("无法读取首帧")
        cap.release()
        return

    clahe = create_clahe()
    prev_gray, _ = preprocess_frame(first_frame, scale, clahe)
    dis_flow = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    history_points = []
    frame_delay = 1.0 / fps
    frame_count = 0

    # 计算中心区域
    region_x, region_y =  465, 242
    region_width, region_height = 119, 215
    center_point = (region_x + region_width // 2, region_y + region_height // 2)
    # print(f"中央区域坐标 (x, y): {center_point}, 区域大小: {region_width}x{region_height}")
    # 定义中心点附近区域（5% x 5%）
    frame_height, frame_width = first_frame.shape[:2]
    center_region_width = int(frame_width * 0.05)
    center_region_height = int(frame_height * 0.05)
    center_region_x = center_point[0] - center_region_width // 2
    center_region_y = center_point[1] - center_region_height // 2
    # 定义边缘区域（距边界 10% 宽度/高度）
    edge_margin_x = int(region_width * 0.1)
    edge_margin_y = int(region_height * 0.1)
    
    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame_count += 1
            
        gray, resized_frame = preprocess_frame(frame, scale, clahe) # 预处理
        mag, ang, flow = compute_optical_flow(prev_gray, gray, dis_flow) # 计算光流
        flow_rgb_display = visualize_flow(resized_frame, mag, ang, scale) # 可视化光流
        motion_mask = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8) # 运动掩膜
        _, motion_mask = cv2.threshold(motion_mask, 25, 255, cv2.THRESH_BINARY)

        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        motion_mask = cv2.bitwise_and(motion_mask, edges)

        # 过滤高速运动区域（水柱）
        jet_mask = mag > np.percentile(mag[mag > 0], 95) if np.any(mag > 0) else np.zeros_like(mag, dtype=bool)
        jet_mask = jet_mask & (motion_mask.astype(bool))

        detection_result = resized_frame.copy()

        # 检测落点
        if np.sum(jet_mask) > 50:
            coords = np.column_stack(np.where(jet_mask))
            # print(f"Jet mask pixels: {np.sum(jet_mask)}, Valid coords: {len(coords)}")  # 调试输出

            if len(coords) > 10:
                # 选择最下方的点（y坐标最大）
                lowest_point = coords[np.argmax(coords[:, 0])][::-1]  # 转换为(x, y)
                
                # 平滑处理
                history_points.append(lowest_point)
                if len(history_points) > max_history:
                    history_points.pop(0)
                smoothed_point = np.mean(history_points, axis=0).astype(int)

                # 输出落点坐标（原始分辨率）
                display_point = (smoothed_point / scale).astype(int)
                # print(f"Water Jet Landing Point (x, y)v: {tuple(display_point)}")

                # 判断落点与中央区域关系
                if (region_x <= display_point[0] <= region_x + region_width) and \
                   (region_y <= display_point[1] <= region_y + region_height):
                    # 在中央区域内
                    if (center_region_x <= display_point[0] <= center_region_x + center_region_width) and \
                       (center_region_y <= display_point[1] <= center_region_y + center_region_height):
                        text = "落点在正中央"
                    elif (display_point[0] <= region_x + edge_margin_x or \
                          display_point[0] >= region_x + region_width - edge_margin_x or \
                          display_point[1] <= region_y + edge_margin_y or \
                          display_point[1] >= region_y + region_height - edge_margin_y):
                        text = "落点差点出去了"
                    else:
                        text = "落点在区域中，但不是很好"
                else:
                    # 在中央区域外
                    text = "落点不在区域中"
                
                # print(f"Text: {text}")

                if text and frame_count % 30 == 0:  # 每30帧输出一次
                    yield text

                # 绘制落点
                cv2.circle(detection_result, tuple(smoothed_point), 6, (0, 0, 255), -1)
                cv2.putText(detection_result, 'Jet Landing',
                            tuple(smoothed_point + np.array([10, -10])),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        # 绘制中央区域和中心点（缩放分辨率）
        region_top_left_scaled = (int(region_x * scale), int(region_y * scale))
        region_bottom_right_scaled = (int((region_x + region_width) * scale), int((region_y + region_height) * scale))
        center_point_scaled = (np.array(center_point) * scale).astype(int)
        # cv2.rectangle(detection_result, region_top_left_scaled, region_bottom_right_scaled, (0, 255, 0), 2)
        # cv2.circle(detection_result, center_point_scaled, 6, (0, 255, 0), -1)
        # cv2.putText(detection_result, 'Center',
                    # (center_point_scaled + np.array([10, -10])).astype(int),
                    # cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 显示结果
        # display_result = cv2.resize(detection_result, (0, 0), fx=1/scale, fy=1/scale)
        # edges_display = cv2.resize(edges, (0, 0), fx=1/scale, fy=1/scale)

        # cv2.imshow("Detection Result", display_result)
        # cv2.imshow("Optical Flow", flow_rgb_display)
        # cv2.imshow("Edges (Canny)", edges_display)

        prev_gray = gray.copy()

        # 帧率控制
        elapsed = time.time() - start_time
        remaining = frame_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC退出
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # detect_water_jet_fast_loop('./demo/normal.mp4')
    # detect_water_jet_fast_loop('./demo/long.mp4')
    detect_water_jet_fast_loop()
    # detect_water_jet_fast_loop('./demo/move_sudden.mp4')