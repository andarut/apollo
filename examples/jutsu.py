#!../.venv/bin/python3

import json, time, os, sys, multiprocessing, re

sys.path.append("..")

from apollo.downloader.video import download_file, download_files, download_m3u8, download_video
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By
from bs4 import BeautifulSoup
import curlify

from enum import StrEnum

import re



"""

curl 'https://r610201.yandexwebcache.org/berserk/1/1.1080.94b2b18e988f0dee.mp4?hash1=7fdd39c2fa713b42fc50fb18ee1c3d85&hash2=f269acf2fbaedab761d0dded13ea6ff6' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'Referer: https://jut.su/' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"' \
  -H 'Range: bytes=0-' \
  -H 'sec-ch-ua-mobile: ?0'

curl 'https://r610201.yandexwebcache.org/berserk/1/1.1080.94b2b18e988f0dee.mp4?hash1=7fdd39c2fa713b42fc50fb18ee1c3d85&hash2=f269acf2fbaedab761d0dded13ea6ff6' -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -e "https://jut.su" --output 'test.mp4'


"""

DEBUG = True

class Downloader:

	@staticmethod
	def download_url(url, path):
		os.system(f"""
		curl '{url}' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Range: bytes=0-' \
  -H 'Referer: https://jut.su/' \
  -H 'Sec-Fetch-Dest: video' \
  -H 'Sec-Fetch-Mode: no-cors' \
  -H 'Sec-Fetch-Site: cross-site' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
--output '{path}'
""")

	# TODO: support films
	@staticmethod
	def download(URL, DIR):
		engine = Engine(URL, headless=False)
		soup = BeautifulSoup(engine.driver.page_source, features="html.parser")
		urls = []
		for a in soup.find_all('a', href=True):
			href = a['href']
			if ("episode" in href) and "html" in href and href not in urls:
				urls.append(f"https://jut.su{href}")

		print(f"FOUND {len(urls)} episods")

		for url in urls:
			print(url)

		video_urls = []
		paths = []
		for url in urls:
			engine.driver.get(url)
			path = os.path.basename(url)
			soup = BeautifulSoup(engine.driver.page_source, features="html.parser")
			video_urls.append(soup.find_all('source')[0]['src'])

			_, season, _, episode, _ = engine.find_element("TITLE", '//*[@id="dle-content"]/div/h1/span').text().split(" ")
			paths.append(f"./Berserk_S{int(season):02d}_E{int(episode):02d}.mp4")
			
		engine.quit()

		i = 1
		for video_url in video_urls:
			path = paths[i-1]
			print(video_url, path)
			Downloader.download_url(video_url, path)
			i += 1
			



#  TODO: check for banned content and auto enable vpn
LIST = [

	# onepiece
	{
		"URL": "https://jut.su/berserk/"
	},

]

DIR = "."
for anime in list(LIST):
	Downloader.download(anime['URL'], DIR)

# engine = Engine("https://jut.su/berserk/", headless=False)

# _ = input("ready?")
# for request in engine.driver.requests:
# 	if ".mp4" in request:
# 		print(request.url)
# 		curl_command = curlify.to_curl(request)
# 		print(curl_command)

# """
# curl 'https://r310201.yandexwebcache.org/berserk/1/1.480.fbb8808a9377d021.mp4?hash1=92539789af24c22f7d22d9acaec40757&hash2=07c6f660141ae9d15591cc188bc650e9' \
#   -H 'Accept: */*' \
#   -H 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'Connection: keep-alive' \
#   -H 'Range: bytes=0-' \
#   -H 'Referer: https://jut.su/' \
#   -H 'Sec-Fetch-Dest: video' \
#   -H 'Sec-Fetch-Mode: no-cors' \
#   -H 'Sec-Fetch-Site: cross-site' \
#   -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36' \
#   -H 'sec-ch-ua: "Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "macOS"'

# """