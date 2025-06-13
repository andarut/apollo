import os, filecmp, multiprocessing, subprocess, requests, sys, re, time, threading
from rich.progress import Progress, BarColumn, TextColumn
import m3u8
from typing import Iterable, Tuple

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
import multiprocessing

from ..engine.logging import print_error, print_info, print_ok, print_warning, print_important

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


def download_file(url: str, path: str, headers: Iterable[Tuple[str, str]], debug=False):
	# curl_command = f"curl '{url}' " + " ".join([f"-H '{key}: {value}'" for key, value in headers]) + f" -o {path}"
	wget_command = f"wget '{url}' -O '{path}'"
	print_info(f'run "{wget_command}"')
	os.system(wget_command)
	
	try:
		_ = os.stat(path).st_size
	except FileNotFoundError:
		print_error(f"wgetcurl error for url={url} path={path}, headers={headers}, command={wget_command}")
	if debug:
		print_ok(f"downloaded path={path} url={url}")

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

# @measure
# def download_m3u8(m3u8_url: str, path: str, debug=False):
# 	if debug:
# 		print_info(f"download_m3u8 path={path}")

# 	# download m3u8 (need to download due to using headers and not be stuck on 403)
# 	m3u8_path = os.path.basename(m3u8_url)
# 	download_file(m3u8_url, m3u8_path)

# 	playlist = m3u8.load(m3u8_path)
# 	urls = []
# 	paths = []
# 	for segment in playlist.segments:
# 		url = segment.uri if segment.uri.startswith('http') else os.path.join(os.path.dirname(m3u8_url), segment.uri)
# 		urls.append(url)
# 		paths.append(os.path.basename(url.replace(".mp4:hls:", "")))

# 	if debug:
# 		print_info(f"downloading {len(paths)} chunks")

# 	init_chunk_path = path.replace(".mp4", "_init.mp4")

# 	# downloading chunks
# 	download_file(m3u8_url.replace(".m3u8", "_init.mp4"), init_chunk_path, debug)
# 	for i in range(len(urls)):
# 		download_file(urls[i], paths[i], debug)

# 	if debug:
# 		print_info(f"concating {len(paths)} chunks")

# 	# concating
# 	cat_command = f"cat {init_chunk_path} "
# 	for _path in paths:
# 		cat_command += f" {_path} "
# 	cat_command += f" > {path}"
# 	os.system(cat_command)

# 	if debug:
# 		print_info("cleanup")

# 	# cleanup
# 	os.system(f"rm -f {init_chunk_path}")
# 	for _path in paths:
# 		os.system(f"rm -f {_path}")

# 	if debug:
# 		print_ok(f"downloaded {path}")


@measure
def download_m3u8(m3u8_url: str, path: str, debug=False, prefix=""):
	if debug:
		print_info(f"download_m3u8 path={path}")
	playlist = m3u8.load(m3u8_url)
	urls = []
	paths = []
	for segment in playlist.segments:
		
		if segment.uri.startswith('http'):
			url = segment.uri 
		else:
			if len(prefix) > 0:
				url = os.path.join(os.path.dirname(prefix), segment.uri)
			else:
				url = os.path.join(os.path.dirname(m3u8_url), segment.uri)
		print(url)
		urls.append(url)
		# TODO: cat proper way
		segment_path = os.path.basename(url.split("?")[0].replace(".mp4:hls:", ""))
		paths.append(segment_path)

	if debug:
		print_info(f"downloading {len(paths)} chunks")

	# download_files(urls, paths, True)
	for i in range(len(urls)):
		_path = os.path.basename(paths[i]).split("?")[0]
		download_file(urls[i], _path, debug)

	with open('file_list.txt', 'w+') as f:
		for ts_path in paths:
			f.write(f"file '{ts_path}'\n")

	if debug:
		print_info(f"concating {len(paths)} chunks")
		print(f"ffmpeg -hide_banner -loglevel panic -y -f concat -safe 0 -i 'file_list.txt' -c copy '{path}'")
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

# chunks will be downloading until there are size is zero (that means that url is 404)
@measure
def download_chunks(base_url: str, filename: str, debug: bool=False):
	# https://grace.ya-ligh.com/9g/9G1MJ7ZNXV8/oy7o9yccdrdvm_init_6.m4s
	# https://grace.ya-ligh.com/9g/9G1MJ7ZNXV8/oy7o9yccdrdvm_init_1.m4s

	# base_url = "https://grace.ya-ligh.com/9g/9G1MJ7ZNXV8/oy7o9yccdrdvm"

	# for future parallization (to predermenied list of chunks)
	def check_url_404(url):
		if debug:
			print_info(f"check for 404 {url}")
		try:
			response = requests.head(url, allow_redirects=True, timeout=5)
			if response.status_code == 404:
				raise requests.RequestException
		except requests.RequestException:
			raise requests.RequestException

	def check_urls_404(urls, max_workers=None) -> int:
		if max_workers is None:
			max_workers = multiprocessing.cpu_count()

		url_to_future = {}
		with ThreadPoolExecutor(max_workers=max_workers) as executor:
			for i, url in enumerate(urls):
				future = executor.submit(check_url_404, url)
				url_to_future[future] = i

			done, not_done = wait(url_to_future.keys(), return_when=FIRST_EXCEPTION)

			for future in not_done:
				future.cancel()

			for future in done:
				exc = future.exception()
				if exc:
					failed_url = url_to_future[future]
					return failed_url
				
	def _download_chunks(urls, paths, max_workers=None) -> int:
		if max_workers is None:
			max_workers = multiprocessing.cpu_count()

		url_to_future = {}
		with ThreadPoolExecutor(max_workers=max_workers) as executor:
			for i, url in enumerate(urls):
				path = paths[i]
				future = executor.submit(download_chunk, url, path)
				url_to_future[future] = i

			done, not_done = wait(url_to_future.keys(), return_when=FIRST_EXCEPTION)

			for future in not_done:
				future.cancel()

			for future in done:
				exc = future.exception()
				if exc:
					failed_url = url_to_future[future]
					return failed_url


	def download_chunk(url, path):
		if debug:
			print_info(f"downlading chunk {path} from {url}")
		os.system(f"wget -qO {path} {url}")
		return os.path.getsize(path) == 0
	
	video_chunks = ["init_6.m4s"]
	audio_chunks = ["init_1.m4s"]

	video_urls = [f"{base_url}_init_6.m4s"]
	audio_urls = [f"{base_url}_init_1.m4s"]
	
	# collect video chunks
	video_i = 1
	while video_i < 1000:
		url = f"{base_url}_chunk_6_{video_i:05d}.m4s"
		path = f"chunk_6_{video_i:05d}.m4s"
		video_urls.append(url)
		video_chunks.append(path)
		video_i += 1

	# collect audio chunks
	audio_i = 1
	while audio_i < 1000:
		url = f"{base_url}_chunk_1_{audio_i:05d}.m4s"
		path = f"chunk_1_{audio_i:05d}.m4s"
		audio_urls.append(url)
		audio_chunks.append(path)
		audio_i += 1

	video_chunks_count = check_urls_404(video_urls)
	audio_chunks_count = check_urls_404(audio_urls)

	# sure about +1 ???

	video_urls = video_urls[:video_chunks_count + 1]
	audio_urls = audio_urls[:audio_chunks_count + 1]

	video_chunks = video_chunks[:video_chunks_count + 1]
	audio_chunks = audio_chunks[:audio_chunks_count + 1]

	if debug:
		print_info(f"video_chunks_count = {video_chunks_count}")
		print_info(f"video_urls = {len(video_urls)}")
		print_info(f"video_chunks = {len(video_chunks)}")

		print_info(f"audio_chunks_count = {audio_chunks_count}")
		print_info(f"audio_urls = {len(audio_urls)}")
		print_info(f"audio_chunks = {len(audio_chunks)}")

	# download video chunks
	if debug:
		print_info("download video chunks")
	_download_chunks(video_urls, video_chunks)
	
	# download audio chunks
	if debug:
		print_info("download audio chunks")
	_download_chunks(audio_urls, audio_chunks)

	# concat video chunks
	if debug:
		print_info("concat video chunks")
	cat_cmd = "cat "
	for path in video_chunks:
		cat_cmd += f" {path}"
	cat_cmd += " > video.mp4"
	os.system(cat_cmd)

	# concat audio chunks
	if debug:
		print_info("concat audio chunks")
	cat_cmd = "cat "
	for path in audio_chunks:
		cat_cmd += f" {path}"
	cat_cmd += " > audio.mp4"
	os.system(cat_cmd)

	# merge video and audio
	if debug:
		print_info("merge video and audio")
	merge_cmd = f"ffmpeg -i video.mp4 -i audio.mp4 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 {filename}"
	os.system(merge_cmd)

	# clear
	if debug:
		print_info("clear")
	os.system("rm -f *.m4s video.mp4 audio.mp4")