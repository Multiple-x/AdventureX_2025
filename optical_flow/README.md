# Environment
在 Ubuntu 系统上, 使用 Anaconda/miniconda 创建并激活虚拟环境：
```
sudo apt install mpv
mpv --version # 验证安装
```

```
conda create -n advx2025 python==3.11
conda activate advx2025
pip install -r requirements.txt
```
# 演示效果
![Video](demo/example.mp4)

# preprocess.py
本代码用于从视频中检测挤压矿泉水瓶产生的水柱在水池中的落点（首次接触水池的点），并输出落点的 (x, y) 坐标。

## Function
- 通过光流（DISOpticalFlow）和边缘检测（Canny）识别快速运动的水柱区域。
- 从检测到的水柱区域中选择最下方的点作为落点，并进行平滑处理以提高稳定性。
- 显示检测结果、光流图像和边缘图像，标记落点和中心区域。

## 摄像头配置(Optional)
格式：推荐使用 MJPG 格式以支持高帧率（例如 1280x720@30FPS）。
分辨率：支持 640x480、1280x720、1920x1080 等，具体见摄像头支持格式（运行 v4l2-ctl --device=/dev/video0 --list-formats-ext）。
调试：若摄像头无法打开，尝试更改 camera_index（例如 camera_index=1）：

# llm.py
## API 调用
通过 kimi 和 minimax 实现根据前述水柱落点形成个性化语音
```
mkdir config && cd config
touch .env
```
在 `.env` 文件中 (可采用`vim .env`)添加
`kimi="YOUR_API_KEY"`、`mini="YOUR_API_KEY"`和`group_id="YOUR_GROUP_ID"`
api-key 以及 group_id 访问 [kimi](https://platform.moonshot.cn/console) 和 [minimax](https://platform.minimaxi.com/) 的 api 平台

- 在 `config.yaml` 中配置语速、音色、情绪等参数，详见 `build_tts_stream_headers()` 函数。
- 默认使用 Minimax 的郭德纲音色（音调和情绪），仅限个人使用，未公开音色 ID。
- 参考 [Minimax API]((https://platform.minimaxi.com/document)) 文档 进行音色定制，上传自定义音频请查看 src/llm.py/upload_audio。


# Qwen2-VL-2B-Instruct(Optional)
下载模型：`modelscope download --model qwen/Qwen2-VL-2B-Instruct`

## AutoAwq
```
mkdir third_parties && cd third_parties
git clone https://github.com/casper-hansen/AutoAWQ.git
cd AutoAWQ-main && pip install -e .
```


# Reference
1. https://platform.moonshot.cn/docs/api/chat
2. https://platform.minimaxi.com