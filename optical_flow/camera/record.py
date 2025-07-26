import pyaudio
import wave
import numpy as np


def record_audio(device_index=0, sample_rate=16000, channels=1, chunk_size=1600, duration=5, output_file="ds_e12_output.wav"):
    """使用指定设备录制音频并保存为 WAV 文件"""
    p = pyaudio.PyAudio()
    
    # 打印设备信息以验证
    print("可用音频输入设备：")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:
            print(f"索引 {i}: {dev_info['name']}, 通道: {dev_info['maxInputChannels']}, 采样率: {dev_info['defaultSampleRate']}")
    try:
        dev_info = p.get_device_info_by_index(device_index)
        print(f"使用设备: 索引 {device_index}, 名称: {dev_info['name']}")
    except Exception as e:
        print(f"无法获取索引 {device_index} 的设备信息: {e}")
        p.terminate()
        return

    # 打开音频流
    try:
        stream = p.open(
            format=pyaudio.paInt16,  # 16-bit 采样，与 C++ 的 SND_PCM_FORMAT_S16_LE 一致
            channels=channels,       # 单声道
            rate=sample_rate,        # 采样率 16000 Hz
            input=True,
            input_device_index=device_index,  # 指定 DS-E12 麦克风（索引 0）
            frames_per_buffer=chunk_size      # 帧大小 1600
        )
    except Exception as e:
        print(f"无法打开设备索引 {device_index}: {e}")
        p.terminate()
        return

    # 录制音频
    print(f"录音 {duration} 秒...")
    frames = []
    for _ in range(int(sample_rate / chunk_size * duration)):
        try:
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print(f"读取音频数据时出错: {e}")
            break

    # 保存为 WAV 文件
    try:
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        print(f"音频已保存到 {output_file}")
    except Exception as e:
        print(f"保存 WAV 文件失败: {e}")

    # 处理音频数据（转换为浮点数，供后续 ASR/VAD 使用）
    if frames:
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        float_data = audio_data.astype(np.float32) / 32768.0  # 与 C++ 的 buffer[i] / 32768.0f 一致
        print(f"处理后的音频数据长度: {len(float_data)}")
    else:
        print("没有录制音频数据")

    # 清理资源
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("音频资源已清理")

if __name__ == "__main__":
    record_audio(device_index=25)  # 指定 DS-E12 麦克风（索引 25）