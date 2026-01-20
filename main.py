import yt_dlp
import subprocess
import threading
import queue
import ffmpeg
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
CHUNK_SECONDS = 2

CHUNK_LIMIT = SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS * CHUNK_SECONDS

def get_url_stream(url):
	print("get_url_stream running")
	ydl_opts = {
		'format' : 'm4a/bestaudio/best',
		'quite': True,
		'no_warnings': True,
	}
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=False)
		return info['url']
stream_url = get_url_stream('https://youtu.be/EhF0X3fQTwY?si=I4V0kygAdSh5GkOQ')

def ffmpeg_thread(stream, q):
	buffer = b''
	print("ffmpeg thread running")
	while True:
		try:
			raw_bytes = stream.stdout.read(1024*2)
			if not raw_bytes:
				print("Stream ended")
				break
			buffer += raw_bytes
			while len(buffer) >= CHUNK_LIMIT:
				chunk = buffer[:CHUNK_LIMIT]
				buffer = buffer[CHUNK_LIMIT:]
				np_array = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
				q.put(np_array)
				print(f"Chunk a size of ${len(np_array)} added to queue")
		except KeyboardInterrupt:
			break
		except Exception as err:
			print("Error in ffmpeg_thread: ", err)
			break
	q.put(None)
def asr_thread(q):
	print("asr_thread running")
	while True:
		try:
			data = q.get()
			if data is None:
				print("The stream ended, no more data")
				break
			print("Streming...")
		except KeyboardInterrupt:
			break
		except Exception as err:
			print(f"Error in asr_thread: {err}")

ffmpeg_cmd = [
    'ffmpeg',
    '-reconnect', '1',
    '-reconnect_streamed', '1',
    '-reconnect_delay_max', '5',
    '-i', stream_url,  # Input is the URL, not a pipe
    '-f', 's16le',
    '-ac', '1',
    '-ar', '16000',
    '-'
]

process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
q = queue.Queue()
thread_ffmpeg = threading.Thread(target=ffmpeg_thread, args=(process, q))
thread_asr = threading.Thread(target=asr_thread, args=(q,))

thread_ffmpeg.start()
thread_asr.start()

thread_ffmpeg.join()
thread_asr.join()
