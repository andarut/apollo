#!../.venv/bin/python3

import sys
import json
sys.path.append("..")

from apollo.engine.engine import *
from apollo.downloader.video import download_chunks

Apollo.debug = True

def download_url(URL: str):
	Apollo.exec([
		GET(URL),

		ZOOM(20),

		# download from hrefs
		CUSTOM_COMMAND(lambda engine: download_manga(engine))
	])

ANIME_KEY = "Demon_Slayer"

URL = json.load(open("manga-chan_config.json", "r"))["data"][ANIME_KEY]

def download_manga(engine: Engine):
	if not engine: return
	hrefs = engine.find_elements("HREFS", By.PARTIAL_HREF_TEXT, "download.php")

	if len(hrefs) == 0:
		print_error("hrefs not found")
		return

	paths = []

	print_info("download started")

	for href in hrefs:
		zip_path = f"{href.text().replace(".zip", "")}_manga-chan.me.zip"
		folder = zip_path.split("ch")[1].replace("iy-demonov-", "").split(".zip")[0].replace("_manga-", "")
		result_path = f"{folder}/{folder}.pdf"
		zip_exist = os.path.exists(zip_path)
		folder_exist = os.path.exists(folder)
		print_info(f"{zip_exist} {zip_path}")
		
		if not zip_exist:
			href.selenium_element.click()
			zip_url = [request for request in engine.driver.requests if ".zip" in request.url][-1]
			os.system(f'wget -O "{zip_path}" "{zip_url}"')

		if not folder_exist or not os.path.exists(result_path):
			os.system(f"unzip {zip_path} -d {folder}")
			os.system(f"magick mogrify -format png {folder}/*.avif")
			os.system(f"magick mogrify -format png {folder}/*.jpeg")
			os.system(f"magick mogrify -format png {folder}/*.jpg")
			os.system(f"magick {folder}/*.png {result_path}")
			
		paths.append(result_path)

	print_info("starting concating")

	paths.sort(key=lambda x: float(x.split('/')[0]) )
	print(paths)
	string = ""
	for path in paths:
		string += f"{path} "
	os.system(f"pdfunite {string} {ANIME_KEY}.pdf")

	print_info("download finished")

download_url(URL)