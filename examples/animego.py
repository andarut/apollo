#!../.venv/bin/python3

import json, time, os, sys, multiprocessing, re

sys.path.append("..")

from apollo.downloader.video import download_file, download_files, download_m3u8
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By

DEBUG = True

with open("animego_config.json") as config_file:
	config = json.loads(config_file.read())

STARTUP_TIMEOUT = config["startup_timeout"]
ACTION_TIMEOUT = config["action_timeout"]
ADS_TIMEOUT = config["ads_timeout"]

CONTENT_TIMEOUT = 20

def download_m4s_chunks(j, base_url: str, path: str, debug=False):

	if debug:
		print_info(f"download_m4s_chunks {base_url} {path}")

	# chunk_type = 6 -> video type
	# chunk_type = 1 -> video type
	def download_chunk(chunk_url: str, chunk_path: str):
		if debug:
			print_info(f"download_chunk {chunk_path}")
		os.system(f"""curl '{chunk_url}' \
		-s \
		-H 'Accept: */*' \
		-H 'Accept-Language: ru,en;q=0.9' \
		-H 'Connection: keep-alive' \
		-H 'Origin: https://aniboom.one' \
		-H 'Referer: https://aniboom.one/' \
		-H 'Sec-Fetch-Dest: empty' \
		-H 'Sec-Fetch-Mode: cors' \
		-H 'Sec-Fetch-Site: cross-site' \
		-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36' \
		-H 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"' \
		-H 'sec-ch-ua-mobile: ?0' \
		-H 'sec-ch-ua-platform: "macOS"' \
		--compressed \
		-o {chunk_path} > /dev/null""")
		try:
			chunk_size = os.stat(chunk_path).st_size
		except FileNotFoundError:
			print_error("curl error, redownloading chunk")
			download_chunk(chunk_url, chunk_path)

	download_chunk(f"{base_url}_init_6.m4s", f"video_{j}_0.m4s")
	download_chunk(f"{base_url}_init_1.m4s", f"audio_{j}_0.m4s")

	i = 1

	video_chunks_downloaded = 1
	audio_chunks_downloaded = 1

	while True:

		if video_chunks_downloaded > 0:
			download_chunk(f"{base_url}_chunk_6_{i:05}.m4s", f"video_{j}_{i}.m4s")
			video_chunk_size = os.stat(f"video_{j}_{i}.m4s").st_size
			if video_chunk_size == 548:
				os.system(f"rm -f video_{j}_{i}.m4s")
				video_chunks_downloaded *= -1
			else:
				video_chunks_downloaded += 1

		if audio_chunks_downloaded > 0:
			download_chunk(f"{base_url}_chunk_1_{i:05}.m4s", f"audio_{j}_{i}.m4s")
			audio_chunk_size = os.stat(f"audio_{j}_{i}.m4s").st_size
			if audio_chunk_size == 548:
				os.system(f"rm -f audio_{j}_{i}.m4s")
				audio_chunks_downloaded *= -1
			else:
				audio_chunks_downloaded += 1

		if video_chunks_downloaded < 0 and audio_chunks_downloaded < 0:
			break

		i += 1

	video_chunks_downloaded *= -1
	audio_chunks_downloaded *= -1

	if debug:
		print_info(f"downloaded {video_chunks_downloaded} video chunks")
		print_info(f"downloaded {audio_chunks_downloaded} audio chunks")


	video_chunks_list = ""
	for i in range(video_chunks_downloaded):
		video_chunks_list += f"video_{j}_{i}.m4s "

	audio_chunks_list = ""
	for i in range(audio_chunks_downloaded):
		audio_chunks_list += f"audio_{j}_{i}.m4s "

	# concat video chunks
	os.system(f"cat {video_chunks_list} >> video_{j}.m4s")

	# concat audio chunks
	os.system(f"cat {audio_chunks_list} >> audio_{j}.m4s")

	# convert from chunks to video
	os.system(f"ffmpeg -hide_banner -loglevel error -y -i video_{j}.m4s -c copy video_{j}.mp4")

	# convert from chunks to audio
	os.system(f"ffmpeg -hide_banner -loglevel error -y -i audio_{j}.m4s -c copy audio_{j}.mp4")

	# merge video and audio
	os.system(f"ffmpeg -hide_banner -loglevel error -y -i video_{j}.mp4 -i audio_{j}.mp4 -c copy {path}")

	# cleanup
	os.system(f"rm -f {video_chunks_list} {audio_chunks_list} video_{j}.m4s  audio_{j}.m4s video_{j}.mp4 audio-{j}.mp4")

	if debug:
		print_ok(f"downloaded {path}")


def download_episode(base_urls: dict, url, VOICE, i, button_18=False, single_episode=False):

	def retry():
		engine.quit()
		download_episode(base_urls, url, VOICE, i, button_18, single_episode)

	global CONTENT_TIMEOUT
	engine = Engine(url, debug=False)
	engine.STARTUP_TIMEOUT = 1
	engine.ACTION_TIMEOUT = 1
	engine.zoom(30)

	# click watch
	WATCH_BUTTON = engine.find_element(
		"WATCH_BUTTON",
		'//*[@id="content"]/div/div[1]/div[1]/div[2]/a/span[2]'
	)
	engine.click(WATCH_BUTTON)

	time.sleep(CONTENT_TIMEOUT)

	# click 18+ button if there is need
	if button_18:
		BUTTON_18 = engine.find_element(
			"BUTTON_18",
			'//*[@id="video-player"]/div[1]/div/div[2]/button[2]'
		)

		if BUTTON_18.is_none():
			retry()
			return

		engine.click(BUTTON_18)

	# select voice
	try:
		AUDIO_BUTTON = [el for el in engine.find_elements("audio", By.CLASS_NAME,"video-player-toggle-item") if el.text() == VOICE][0]
		engine.click(AUDIO_BUTTON)
	except IndexError:
		print_warning("VOICES not found, retrying")
		retry()
		return

	if not single_episode:
		EPISODE_INPUT = engine.find_element(
			"EPISODE_INPUT",
			'//*[@id="video-series-number-input"]'
		)

		if EPISODE_INPUT.is_none():
			retry()
			return

		engine.type(EPISODE_INPUT, str(i), clear=True, enter=True)

	PLAYER_FRAME = engine.find_element(
		"PLAYER_FRAME",
		'//*[@id="video-player"]/div[2]/div[1]/div[1]/iframe'
	)

	if PLAYER_FRAME.is_none():
		retry()
		return

	engine.click(PLAYER_FRAME)

	# wait for ads
	time.sleep(ADS_TIMEOUT)

	# wait for content
	time.sleep(10)

	base_url_found = False

	# get base_url for future downloades
	for request in engine.driver.requests:
		if request.response:
			if ".m4s" in request.url and "yandex" not in request.url:
				base_urls[i] = request.url.split("_")[0]
				base_url_found = True
			if ".m3u8" in request.url:
				base_urls[i] = request.url.replace('360.mp4', '720.mp4')
				base_url_found = True
			if ".mp4" in request.url:
				base_urls[i] = request.url
				base_url_found = True

	if not base_url_found:
		retry()
		return


def download(dir, url, VOICE):
	global ADS_TIMEOUT

	if not os.path.isdir(dir):
		os.mkdir(dir)

	engine = Engine(url, debug=DEBUG)
	engine.STARTUP_TIMEOUT = STARTUP_TIMEOUT
	engine.ACTION_TIMEOUT = ACTION_TIMEOUT

	EPISODS_COUNT_TEXT = engine.find_element(
		"EPISODS_COUNT_TEXT",
		'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[2]'
	)

	try:
		epidods_count = int(EPISODS_COUNT_TEXT.text())
	except ValueError:
		epidods_count = 7

	AGING_TEXT = engine.find_element(
		"AGING_TEXT",
		'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[10]/span'
	)

	AGING = str(AGING_TEXT.text())

	if "NC" in AGING:
		AGING_TEXT = engine.find_element(
			"AGING_TEXT",
			'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[9]/span'
		)
		AGING = str(AGING_TEXT.text())

	print(f"AGING = {AGING}")

	engine.quit()

	manager = multiprocessing.Manager()
	base_urls = manager.dict()

	processes = []
	i = 1
	while i <= epidods_count:
		if DEBUG:
			print_info(f"create process for i={i}")
		# process = multiprocessing.Process(target=download_episode,
		# 	args=(base_urls, url, VOICE, i, True, epidods_count == 1)
		# )
		# processes.append(process)
		# process.start()
		download_episode(base_urls, url, VOICE, i, True, epidods_count == 1)
		i += 1

	for process in processes:
		process.join()

	def download_urls():
		processes = []
		for i, base_url in base_urls.items():
			if DEBUG:
				print_info(f"create downloading process for i={i}")
			if ".m3u8" in base_url:
				process = multiprocessing.Process(target=download_m3u8,
					args=(base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
				)
			elif ".mp4" in base_url:
				process = multiprocessing.Process(target=download_file,
					args=(base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
				)
			else:
				process = multiprocessing.Process(target=download_m4s_chunks,
					args=(i, base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
				)
			processes.append(process)
			process.start()

		for process in processes:
			process.join()

	download_urls()

if __name__ == '__main__':
	season = "Hells.paradise"
	download(season, config["data"][season]["URL"], config["data"][season]["VOICE"])