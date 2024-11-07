import os, filecmp, multiprocessing, subprocess, requests, sys, re, time, threading
from rich.progress import Progress, BarColumn, TextColumn
import m3u8

from engine.logging import print_error, print_info, print_ok, print_warning, print_important

from functools import wraps

def measure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the original function
        end_time = time.time()  # Record the end time
        elapsed_time = round(end_time - start_time, 2)  # Calculate elapsed time
        print_important(f"Elapsed time for '{func.__name__}': {elapsed_time} seconds")
        return result  # Return the result of the original function
    return wrapper


def download_file(url: str, path: str, debug=False):
	# os.system(f"""curl '{url}' \
	# -s \
	# -H 'Accept: */*' \
	# -H 'Accept-Language: ru,en;q=0.9' \
	# -H 'Connection: keep-alive' \
	# -H 'Origin: https://aniboom.one' \
	# -H 'Referer: https://aniboom.one/' \
	# -H 'Sec-Fetch-Dest: empty' \
	# -H 'Sec-Fetch-Mode: cors' \
	# -H 'Sec-Fetch-Site: cross-site' \
	# -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36' \
	# -H 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"' \
	# -H 'sec-ch-ua-mobile: ?0' \
	# -H 'sec-ch-ua-platform: "macOS"' \
	# --compressed \
	# -o {path} > /dev/null""")
	os.system(f"wget -qO {path} {url}")
	try:
		_ = os.stat(path).st_size
	except FileNotFoundError:
		print_error("curl error")
		download_file(url, path)
	# if debug:
	# 	print_ok(f"downloaded path={path} url={url}")

def print_progress(url: str, path: str, progress, task):
	response = requests.head(url, allow_redirects=True)
	file_size = int(response.headers.get('Content-Length', -1))
	while True:
		size_before = os.stat(path).st_size
		time.sleep(1)
		size_after = os.stat(path).st_size
		size_diff = size_after - size_before
		diff_percent = (size_diff / file_size) * 100
		if size_after == file_size: break
		progress.update(task, advance=diff_percent)
		

def download_files(urls, paths, debug=False):

	processes = []
	progress_threads = []
	for i in range(len(urls)):
		url = urls[i]
		path = paths[i]
		if debug:
			print_info(f"create process for url={url} and path={path}")
		process = multiprocessing.Process(target=download_file, args=(url, path, debug, ))
		processes.append(process)

	for process in processes:
		process.start()

	if debug:
		with Progress(TextColumn("[progress.description]{task.description}"), BarColumn()) as progress:
			tasks = [progress.add_task(f"{paths[i-1]}", total=100) for i in range(1, len(paths)+1)]
			progress_threads = []
			for i in range(len(urls)):
				progress_thread = threading.Thread(target=print_progress, args=(urls[i], paths[i], progress, tasks[i], ))
				progress_thread.start()
				progress_threads.append(progress_thread)


			for progress_thread in progress_threads:
				progress_thread.join()

	for process in processes:
		process.join()

@measure
def download_m3u8(m3u8_url: str, path: str, debug=False):
	if debug:
		print_info(f"download_m3u8 path={path}")
	playlist = m3u8.load(m3u8_url)
	urls = []
	paths = []
	for segment in playlist.segments:
		url = segment.uri if segment.uri.startswith('http') else os.path.join(os.path.dirname(m3u8_url), segment.uri)
		urls.append(url)
		# TODO: cat proper way
		paths.append(os.path.basename(url.replace(".mp4:hls:", "")))

	if debug:
		print_info(f"downloading {len(paths)} chunks")
	download_files(urls, paths, False)
	
	with open('file_list.txt', 'w+') as f:
		for ts_path in paths:
			f.write(f"file '{ts_path}'\n")
	
	if debug:
		print_info(f"concating {len(paths)} chunks")
	os.system(f"ffmpeg -hide_banner -loglevel panic -y -f concat -safe 0 -i 'file_list.txt' -c copy '{path}'")
	if debug:
		print_info("cleanup")
	os.system(f"rm -f *.ts file_list.txt")
	if debug:
		print_ok(f"downloaded {path}")

def download_video(base_url: str, filename: str, debug=False):
	
	if debug:
		print_info(f"download_video filename={filename} base_url={base_url}")

	download_file(f"{base_url}_init_6.m4s", f"video_0.m4s")
	download_file(f"{base_url}_init_1.m4s", f"audio_0.m4s")

	i = 1

	video_chunks_downloaded = 1
	audio_chunks_downloaded = 1

	while True:

		if video_chunks_downloaded > 0:
			download_file(f"{base_url}_chunk_6_{i:05}.m4s", f"video_{i}.m4s")
			video_chunk_size = os.stat(f"video_{i}.m4s").st_size
			if video_chunk_size == 548:
				os.system(f"rm -f video_{i}.m4s")
				video_chunks_downloaded *= -1
			else:
				video_chunks_downloaded += 1

		if audio_chunks_downloaded > 0:
			download_file(f"{base_url}_chunk_1_{i:05}.m4s", f"audio_{i}.m4s")
			audio_chunk_size = os.stat(f"audio_{i}.m4s").st_size
			if audio_chunk_size == 548:
				os.system(f"rm -f audio_{i}.m4s")
				audio_chunks_downloaded *= -1
			else:
				audio_chunks_downloaded += 1

		if video_chunks_downloaded < 0 and audio_chunks_downloaded < 0:
			break

		i += 1

	video_chunks_downloaded *= -1
	audio_chunks_downloaded *= -1

	if debug:
		print_ok(f"downloaded {video_chunks_downloaded} video chunks")
		print_ok(f"downloaded {audio_chunks_downloaded} audio chunks")

	if debug:
		print_info(f"check for chunk diff")

	for i in range(video_chunks_downloaded):
		for j in range(video_chunks_downloaded):
			if i != j and filecmp.cmp(f"video_{i}.m4s", f"video_{j}.m4s"):
				print_error(f"equal video chunks {i} {j}")
				return

	for i in range(audio_chunks_downloaded):
		for j in range(audio_chunks_downloaded):
			if i != j and filecmp.cmp(f"audio_{i}.m4s", f"audio_{j}.m4s"):
				print_error(f"equal audio chunks {i} {j}")
				return

	video_chunks_list = ""
	for i in range(video_chunks_downloaded):
		video_chunks_list += f"video_{i}.m4s "

	audio_chunks_list = ""
	for i in range(audio_chunks_downloaded):
		audio_chunks_list += f"audio_{i}.m4s "

	if debug:
		print_info("concat video chunks")
	os.system(f"cat {video_chunks_list} >> video.m4s")

	if debug:
		print_info("concat audio chunks")
	os.system(f"cat {audio_chunks_list} >> audio.m4s")

	if debug:
		print_info("convert from chunks to video")
	os.system("ffmpeg -i video.m4s -c copy video.mp4")

	if debug:
		print_info("convert from chunks to audio")
	os.system("ffmpeg -i audio.m4s -c copy audio.mp4")

	if debug:
		print_info("merge video and audio")
	os.system(f"ffmpeg -i video.mp4 -i audio.mp4 -c copy {filename}")

	if debug:
		print_info("cleanup")
	os.system("rm -f *.m4s video.mp4 audio.mp4")
