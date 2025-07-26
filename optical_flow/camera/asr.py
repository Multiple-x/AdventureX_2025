import whisper
import os
import time

def convert_audio_to_text(input_file="ds_e12_output.wav", model_name="base"):
    """使用 Whisper 将 WAV 音频文件转换为文本"""
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：音频文件 {input_file} 不存在")
        return

    # 加载 Whisper 模型
    try:
        print(f"加载 Whisper 模型: {model_name}")
        model = whisper.load_model(model_name)  # 可选模型: tiny, base, small, medium, large
    except Exception as e:
        print(f"加载 Whisper 模型失败: {e}")
        return

    start_time = time.time()
    # 进行语音转文本
    try:
        print("正在转录音频...")
        result = model.transcribe(input_file, language="zh")  # 假设是中文，修改 language 参数以匹配你的语言
        print("识别的文本：")
        print(result["text"])
    except Exception as e:
        print(f"转录音频时出错: {e}")
    convert_time = time.time() - start_time
    print("转录完成，耗时: {:.2f} 秒".format(convert_time))

if __name__ == "__main__":
    convert_audio_to_text()