import os
import time
import subprocess
from preprocess import detect_water_jet_fast_loop
from llm import load_config, get_kimi_response, call_tts_stream, audio_play

OUTPUT_FILE = "./audio/output.mp3"

file_format = "mp3"
output_dir = "./audio"
video_path = './demo/normal.mp4'
config = load_config()

def main():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for text in detect_water_jet_fast_loop(video_path):
        if text:
            print(f"Processing text: {text}")
            text_gen = config["model_settings"]["qwen"]
            if not text_gen:
                text = get_kimi_response(text)
            audio_chunk_iterator = call_tts_stream(text)
            if audio_chunk_iterator:
                audio = audio_play(audio_chunk_iterator)
                timestamp = int(time.time())
                file_name = f"./audio/{OUTPUT_FILE.split('.')[0]}_{timestamp}.{file_format}"
                with open(file_name, 'wb') as file:
                    file.write(audio)
                print(f"Audio saved to {file_name}")
                mpv_command = ["mpv", "--no-cache", "--no-terminal", file_name]
                mpv_process = subprocess.Popen(
                    mpv_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                mpv_process.wait()
                
            else:
                print("Failed to generate audio from MiniMax TTS.")
                
if __name__ == "__main__":
    main()