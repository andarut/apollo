#!../.venv/bin/python3

import json, time, os, sys, multiprocessing, re

sys.path.append("..")

from apollo.downloader.video import download_file, download_files, download_m3u8, download_video
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By

DEBUG = True

with open("animego_config.json") as config_file:
	config = json.loads(config_file.read())

STARTUP_TIMEOUT = config["startup_timeout"]
ACTION_TIMEOUT = config["action_timeout"]
ADS_TIMEOUT = config["ads_timeout"]

URL = "https://animego.ac/anime/lazar-2762"

CONTENT_TIMEOUT = 20

def download_ts_chunks(base_url, path, debug=False):
	if debug:
		print_info(f"download_m4s_chunks {base_url} {path}")

	paths = []
	i = 1
	while True:
		chunk_url = base_url.split(':seg-')[0].replace("360.mp4", "720.mp4") + f":seg-{i}-v1-a1.ts"
		chunk_path = f"720.mp4:hls:seg-{i}-v1-a1.ts"
		download_file(url=chunk_url, path=chunk_path)
		chunk_size = os.stat(chunk_path).st_size
		if chunk_size == 0:
			os.system(f"rm -f {chunk_path}")
			break
		paths.append(chunk_path)
		i += 1

	cmd = "cat "
	for _path in paths:
		cmd += f" {_path}"
	cmd += f" > {path}"
	print(cmd)
	os.system(cmd)
	os.system("rm -f *.ts")


# def download_m4s_chunks(j, base_url: str, path: str, debug=False):

# 	if debug:
# 		print_info(f"download_m4s_chunks {base_url} {path}")

# 	# chunk_type = 6 -> video type
# 	# chunk_type = 1 -> video type
# 	def download_chunk(chunk_url: str, chunk_path: str):
# 		if debug:
# 			print_info(f"download_chunk {chunk_url} {chunk_path}")
# 		os.system(f"""curl '{chunk_url}' \
# 		-s \
# 		-H 'Accept: */*' \
# 		-H 'Accept-Language: ru,en;q=0.9' \
# 		-H 'Connection: keep-alive' \
# 		-H 'Origin: https://aniboom.one' \
# 		-H 'Referer: https://aniboom.one/' \
# 		-H 'Sec-Fetch-Dest: empty' \
# 		-H 'Sec-Fetch-Mode: cors' \
# 		-H 'Sec-Fetch-Site: cross-site' \
# 		-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36' \
# 		-H 'sec-ch-ua: "Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"' \
# 		-H 'sec-ch-ua-mobile: ?0' \
# 		-H 'sec-ch-ua-platform: "macOS"' \
# 		--compressed \
# 		-o {chunk_path} > /dev/null""")
# 		try:
# 			chunk_size = os.stat(chunk_path).st_size
# 		except FileNotFoundError:
# 			print_error("curl error, redownloading chunk")
# 			download_chunk(chunk_url, chunk_path)

# 	download_chunk(f"{base_url}_init.mp4", f"init_{j}.mp4")

# 	i = 0

# 	chunks_downloaded = 1

# 	while True:

# 		download_chunk(f"{base_url}_{i:04}.m4s", f"chunk_{j}_{i}.m4s")
# 		video_chunk_size = os.stat(f"chunk_{j}_{i}.m4s").st_size
# 		if video_chunk_size == 548:
# 			os.system(f"rm -f chunk_{j}_{i}.m4s")
# 			break

# 		i += 1
# 		chunks_downloaded += 1

# 	if debug:
# 		print_info(f"downloaded {chunks_downloaded} chunks")


# 	chunks_list = ""
# 	for i in range(chunks_downloaded-1):
# 		chunks_list += f"chunk_{j}_{i}.m4s "

# 	# concat chunks
# 	os.system(f"cat {chunks_list} >> chunk_{j}.m4s")

# 	# convert from chunks to video
# 	os.system(f"ffmpeg -hide_banner -loglevel error -y -i chunk_{j}.m4s -c copy chunk_{j}.mp4")

# 	# merge video and init
# 	os.system(f"ffmpeg -hide_banner -loglevel error -y -i init_{j}.mp4 -i chunk_{j}.mp4 -c copy {path}")

# 	# cleanup
# 	# os.system(f"rm -f {chunks_list} chunk_{j}.m4s chunk_{j}.mp4")

# 	if debug:
# 		print_ok(f"downloaded {path}")


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
	engine = Engine(url, debug=True, headless=False)
	engine.STARTUP_TIMEOUT = STARTUP_TIMEOUT
	engine.ACTION_TIMEOUT = ACTION_TIMEOUT

	# REGECT = engine.find_element(
	# 	"REGECT",
	# 	'//*[@id="W0wltc"]/div'
	# )
	# engine.click(REGECT)

	# CLICK = engine.find_element(
	# 	"CLICK",
	# 	"//*[contains(text(), 'Тетрадь')]"
	# )
	# engine.click(CLICK)


	BUTTON = engine.find_element(
		"BUTTON",
		'//*[@id="content"]/div[1]/div/div[2]/button[2]'
	)
	if not BUTTON.is_none():
		engine.click(BUTTON)

	time.sleep(2)

	# click watch
	WATCH_BUTTON = engine.find_element(
		"WATCH_BUTTON",
		'//*[@id="content"]/div/div[1]/div[1]/div[2]/a/span[2]'
	)
	if WATCH_BUTTON.is_none():
		retry()
		return
	engine.click(WATCH_BUTTON)

	# engine.zoom(30)

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
		AUDIO_BUTTON = [el for el in engine.find_elements("audio", By.CLASS_NAME,"video-player-toggle-item-name") if el.text() in VOICE][0]
		engine.click(AUDIO_BUTTON)
	except IndexError:
		print_warning("VOICES not found, retrying")
		retry()
		return
	
	# select player
	PLAYER_SELECT = engine.find_element("PLAYER_SELECT", '//*[@id="video-players-tab"]')
	engine.click(PLAYER_SELECT)

	time.sleep(2)

	# TODO: add easy search for text in element
	KODIK_PLAYER = engine.find_element("KODIK_PLAYER", '//*[@id="video-players"]/span[8]/span')
	engine.click(KODIK_PLAYER)

	time.sleep(5)

	if not single_episode:
		EPISODE_INPUT = engine.find_element(
			"EPISODE_INPUT",
			'//*[@id="video-series-number-input"]'
		)

		if EPISODE_INPUT.is_none():
			retry()
			return

		engine.type(EPISODE_INPUT, str(i), clear=True, enter=True)

	time.sleep(2)

	PLAYER_FRAME = engine.find_element(
		"PLAYER_FRAME",
	# 	# '//*[@id="video-player"]/div[2]/div[1]/div[1]/iframe'
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
		if "yandex" not in request.url:
			if ".mp4" in request.url:
				base_urls[i] = request.url.split(":")[0].replace("360.mp4", "720.mp4")
				base_url_found = True
			if request.url.endswith(".m4s"):
				print(request.url)
				base_urls[i] = request.url.split("_")[0]
				base_url_found = True
			if request.url.endswith(".m3u8"):
				print(request.url)
				base_urls[i] = request.url.replace('360.mp4', '720.mp4')
				base_url_found = True
				break
			

	if not base_url_found:
		retry()
		return


def download(dir, url, VOICE):
	global ADS_TIMEOUT

	if not os.path.isdir(dir):
		os.mkdir(dir)

	engine = Engine(url, debug=DEBUG, headless=True)
	engine.STARTUP_TIMEOUT = STARTUP_TIMEOUT
	engine.ACTION_TIMEOUT = ACTION_TIMEOUT

	BUTTON = engine.find_element(
		"BUTTON",
		'//*[@id="content"]/div[1]/div/div[2]/button[2]'
	)
	if not BUTTON.is_none():
		engine.click(BUTTON)

	# _ = input("ready?")

	# REGECT = engine.find_element(
	# 	"REGECT",
	# 	'//*[@id="W0wltc"]/div'
	# )
	# engine.click(REGECT)

	# CLICK = engine.find_element(
	# 	"CLICK",
	# 	"//*[contains(text(), 'Тетрадь')]"
	# )
	# CLICK = engine.find_elements(
	# 	"CLICK",
	# 	By.
	# 	"Тетрадь смерти"
	# )
	# engine.click(CLICK)

	# POSTER_IMAGE = engine.find_element(
	# 	"POSTER_IMAGE",
	# 	'//*[@id="content"]/div/div[1]/div[1]/div[1]/div[2]/img'
	# )
	# if POSTER_IMAGE.is_none():
	# 	download(dir, url, VOICE)
	# 	return

	# image_url = POSTER_IMAGE.get("src")
	# download_file(image_url, f"{dir}/{dir}.jpg")

	EPISODS_COUNT_TEXT = engine.find_element(
		"EPISODS_COUNT_TEXT",
		'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[2]'
	)

	try:
		epidods_count = int(EPISODS_COUNT_TEXT.text())
	except ValueError:
		try:
			print(EPISODS_COUNT_TEXT.text())
			epidods_count = int(EPISODS_COUNT_TEXT.text().split('/')[0].replace(' ', ''))
		except ValueError:
			epidods_count = 12

	print(f"epidods_count = {epidods_count}")

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
	epidods_count = 13
	i = 13
	while i <= epidods_count:
		if DEBUG:
			print_info(f"create process for i={i}")
		# process = multiprocessing.Process(target=download_episode,
		# 	args=(base_urls, url, VOICE, i, True, epidods_count == 1)
		# )
		# processes.append(process)
		# process.start()
		download_episode(base_urls, url, VOICE, i, False, epidods_count == 1)
		i += 1

	for process in processes:
		process.join()

	def download_urls():
		processes = []
		for i, base_url in base_urls.items():
			if DEBUG:
				print_info(f"create downloading process for i={i} base_url={base_url}")
			if ".mp4" in base_url:
				if ".ts" in base_url:
					download_ts_chunks(base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
				else:
					process = multiprocessing.Process(target=download_file,
						args=(base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
					)
			elif ".m3u8" in base_url:
				base_url = base_url.replace(".m3u8", "_1080p.m3u8")
				download_m3u8(base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)	
			else:
				process = multiprocessing.Process(target=download_m4s_chunks,
					args=(i, base_url, f"{dir}/{dir}.E{i:02}.mp4", DEBUG)
				)
			# processes.append(process)
			# process.start()

		for process in processes:
			process.join()

	download_urls()

if __name__ == '__main__':
	season = "Solo.Leveling.S02"
	download(season, config["data"][season]["URL"], config["data"][season]["VOICE"])
