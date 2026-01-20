import yt_dlp
import subprocess
import threading
import 

def get_url_stream(url):
	ydl_opts = {
		'format' : 'm4a/bestaudio/best',
		'quite': True,
		'no_warnings': True,
		'cookiesfrombrowser':('firefox',),
	}
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=false)
		return info['url']
stream_url = get_url_stream('https://youtu.be/EhF0X3fQTwY?si=I4V0kygAdSh5GkOQ')

def 
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

process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
