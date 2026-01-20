import yt_dlp
import ffmpeg
import subprocess
import threading
import queue
import numpy as np
import os
import soundfile as sf
import requests
import json

url = 'https://archive.org/details/shepherdwhostayed_2512.poem_librivox/shepherdwhostayed_garrison_bk_128kb.mp3'

hasab = 'https://hasab.co/api/v1/upload-audio'
HASAB_API = os.getenv('HASAB_API')
headers = {
    "Authorization": f"Bearer {HASAB_API}",
}

config = {
    "transcribe": True,
    "translate": False,
    "summarize": False,
    "language": "auto",
    "timestamps": True
}

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
CHUNK_SECONDS = 15

CHUNK_LIMIT = SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS * CHUNK_SECONDS

def get_stream_url(url):
    yt_output = {
        'format':'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(yt_output) as ytdlp:
        info = ytdlp.extract_info(url, download=False)
        return info['url']
stream_url = get_stream_url(url)
def listen_to_error(process):
    if process.stderr:
        print(f"Error in process ffmpeg {process.stderr.read().decode}")

def ffmpeg_thread(process, q):
    buffer = b''
    print("reading bytes...")
    while True:
        try:
            raw_bytes = process.stdout.read(1024*16)
            if not raw_bytes:
                
                continue
            buffer += raw_bytes
            while len(buffer) >= CHUNK_LIMIT:
                chunk = buffer[:CHUNK_LIMIT]
                buffer = buffer[CHUNK_LIMIT:]
                np_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                q.put(np_array)
                print(np_array)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in ffmpeg thread: {e}")

def asr_thread(q):   
    while True:
        try:
            data = q.get()
            if data is None:
                
                continue
            print("Data found..")
            sf.write(
                "chunk_01.wav",
                data,
                samplerate=16000,
                subtype="PCM_16"
            )
            print(">WAV formed...")
            files = {
                "file": ("chunk_01.wav", open("chunk_01.wav", "rb"), "audio/wav"),
                "config": (None, json.dumps(config))
            }
            response = requests.post(hasab, headers=headers, files=files)
            print(response.status_code)
            print(response.text)

            ans = response.json()
            print(ans['transcription'])
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in asr thread: {e}")
            


ffmpeg_cmd = [
    'ffmpeg',
    '-reconnect', '1',
    '-reconnect_streamed', '1',
    '-reconnect_delay_max', '5',
    '-i', stream_url,
    '-f', 's16le',
    '-ac', '1',
    '-ar', '16000',
    '-'
]

process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
q = queue.Queue()

thread_ffmpeg = threading.Thread(target=ffmpeg_thread, args=(process, q))
thread_asr = threading.Thread(target=asr_thread, args=(q,))

thread_ffmpeg.start()
thread_asr.start()
thread_ffmpeg.join()
thread_asr.join()
