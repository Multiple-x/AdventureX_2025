import os
import time
import json
import yaml
import random
import requests
import readline
import subprocess
from PIL import Image
from openai import OpenAI
from typing import Iterator
from dotenv import load_dotenv
# from accelerate import Accelerator
# from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

CONFIG = "./config/config_customize.yaml"
OUTPUT_FILE = "./audio/output.mp3"
IMITATE_AUDIO = "./audio/demo/imitate_audio.mp3"

load_dotenv(dotenv_path="./config/.env")
kimi_api_key = os.getenv("kimi")
mini_api_key = os.getenv("mini")
group_id = os.getenv('group_id')
if not all([kimi_api_key, mini_api_key, group_id]):
    raise ValueError("Missing required environment variables: kimi, mini, or group_id")


file_format = "mp3"
url = f"https://api.minimaxi.com/v1/t2a_v2?GroupId={group_id}"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {mini_api_key}"
}

# --- Load configuration from YAML file ---
def load_config():
    with open(CONFIG, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)
config = load_config()
     
# --- Kimi VLM/LLM ---
def get_kimi_response(text="水柱落在区域中间") -> str:
    start_time = time.time()
    client = OpenAI(
        api_key=kimi_api_key,
        base_url = "https://api.moonshot.cn/v1"
    )
    data = [
        {"role": "system", "content": "你是一个幽默风趣的助手, \
          根据水柱落点生成20字以内的中文俏皮评论, 风格类似“你射的好歪啊, 行不行啊老铁”。开头需要有如“唉~咱就是说”“于谦你瞅瞅”等郭德纲的语气词"},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(
        # model="kimi-k2-0711-preview",
        model="moonshot-v1-8k",
        messages=data,
        temperature=0.6,
        stream=True
    )
    content = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content
    kimi_time = time.time() - start_time
    print(f"Kimi response time: {kimi_time:.2f} seconds")

    return content

# def get_qwen_response(image_path: str) -> str:
#     start_time = time.time()
#     accelerator = Accelerator
#     model = Qwen2VLForConditionalGeneration.from_pretrained(
#         "./models/Qwen2.5-VL-3B-Instruct", torch_dtype="auto", device_map="cuda")
#     processor = AutoProcessor.from_pretrained("./models/Qwen2.5-VL-3B-Instruct")
#     text_prompt = "水柱的落点离区域中心的远近"
#     messages = [{
#             "role": "system",
#             "content": "你是一个幽默风趣的助手, 根据图片内容和水柱落点生成20字以内的中文俏皮评论, 风格类似'你射的好歪啊，行不行啊老铁’或‘瞄这么准，奥运会等着你！’"
#         },
#         {
#             "role": "user",
#             "content": [
#                 {"type": "image", "image": Image.open(image_path)},
#                 {"type": "text", "text": text_prompt}
#             ]
#         }]
#     inputs = processor.apply_chat_template(messages, return_tensors="pt").to(accelerator.device)
#     outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.6)
#     reponse = processor.decode(outputs[0], skip_special_tokens=True)
#     print(f"Qwen response: {reponse}")
#     qwen_time = time.time() - start_time
#     print(f"Qwen response time: {qwen_time:.2f} seconds")
    
#     return reponse


# --- Mini TTS ---
def build_tts_stream_headers() -> dict:
    """构建TTS请求头"""
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'authorization': f'Bearer {mini_api_key}',
    }
    return headers

def build_tts_stream_body(text: str) -> dict:
    """构建TTS请求体"""
    if not config["tts_change"]:
        voices = config["tts_settings"]["default"]
        voice_id = list(voices.keys())[0]
        voice_params = voices[voice_id]
    else:
        voices = config["tts_settings"]["voices"]
        voice_id = random.choice(list(voices.keys()))
        voice_params = voices.get(voice_id, voices['male-qn-qingse'])
    print(voice_id, voice_params)
    body = json.dumps({
        "model": "speech-02-turbo",
        "text": text,
        "stream":True,
        # "voice_setting":{
        #     "voice_id":voice_id,
        #     "speed":voice_params["speed"],
        #     "vol":voice_params["vol"],
        #     "pitch":voice_params["pitch"],
        #     "emotion":voice_params["emotion"],
        # },
        "voice_setting":{
            "voice_id":voice_id,
            "speed":1,
            "vol":1,
            "pitch":0,
            "emotion":voice_params["emotion"],
        },
        "pronunciation_dict":config["tts_settings"]["pronunciation_dict"],
        "audio_setting":config["tts_settings"]["audio_setting"]
    })
    return body

def call_tts_stream(text: str) -> Iterator[bytes]:
    """调用TTS流式API"""
    start_time = time.time()
    tts_url = url
    tts_headers = build_tts_stream_headers()
    tts_body = build_tts_stream_body(text)
    response = requests.post(tts_url,  stream=True, headers=headers, data=tts_body)
    minimax_time = time.time() - start_time
    print(f"MiniMax TTS response time: {minimax_time:.2f} seconds")
    
    for chunk in (response.raw):
        if chunk:
            if chunk[:5] == b'data:':
                data = json.loads(chunk[5:])
                if "data" in data and "extra_info" not in data:
                    if "audio" in data["data"]:
                        audio = data["data"]['audio']
                        yield audio

def audio_play(audio_stream: Iterator[bytes]) -> bytes:
    # mpv_command = ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"]
    # mpv_process = subprocess.Popen(
        # mpv_command,
        # stdin=subprocess.PIPE,
        # stdout=subprocess.DEVNULL,
        # stderr=subprocess.DEVNULL,
    # )
    audio = b""
    try:
        for chunk in audio_stream:
            if chunk is not None and chunk != '\n':
                decoded_hex = bytes.fromhex(chunk)
                # mpv_process.stdin.write(decoded_hex)  # type: ignore
                # mpv_process.stdin.flush()
                
                audio += decoded_hex
        # with open(file=OUTPUT_FILE, mode='wb') as f:
        #     f.write(audio)
    finally:
        pass
        # mpv_process.stdin.close()
        # mpv_process.wait()  
    return audio

def upload_audio(audio_path: str) -> str:
    # 复刻郭德纲音频上传
    headers_up = {
        "authority": "api.minimaxi.com",
        "Authorization": f"Bearer {mini_api_key}"
    }
    data = {"purpose":"voice_clone"}
    files = {"file": open(audio_path, "rb")}
    response = requests.post(url=url, headers=headers_up, data=data, files=files)
    if response.status_code != 200:
        raise RuntimeError(f"上传失败: {response.status_code} - {response.text}")
    json_response = response.json()
    print(f"API 响应: {json_response}")
    print("Trace-ID:", response.headers.get("Trace-Id"))
    # file_id = response.json().get("file").get("file_id")
    # print(file_id)


if __name__ == "__main__":
    text_gen = config["model_settings"]["qwen"]
    if not text_gen:
        text = get_kimi_response()
    # else:
    #     image_path = "./demo/image00.png" 
    #     text = get_qwen_response(image_path)
    print(text)
    # Call MiniMax TTS with the text from Kimi
    audio_chunk_iterator = call_tts_stream(text)
    if audio_chunk_iterator:
        audio = audio_play(audio_chunk_iterator)
        timestamp = int(time.time())
        file_name = f"./audio/{OUTPUT_FILE.split('.')[0]}_{timestamp}.{file_format}"
        with open(file_name, 'wb') as file:
            file.write(audio)
        print(f"Audio saved to {file_name}")
    else:
        print("Failed to generate audio from MiniMax TTS.")