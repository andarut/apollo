#!../.venv/bin/python3

import json, time, os, sys, multiprocessing
sys.path.append("..")

from apollo.downloader.video import download_files, download_m3u8
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By

DEBUG = True

URL = "https://appstorrent.ru"
FOLDER = "appstorrent" # TODO: generate from url

def download(url, folder):

	engine = Engine(url, DEBUG, headless=False)
	time.sleep(2)

	_ = input("READY? ")

	print(engine.driver.page_source)

	engine.quit()

if __name__ == '__main__':
	download(URL, FOLDER)
