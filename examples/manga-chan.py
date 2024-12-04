#!../.venv/bin/python3

import json, time, os, sys, multiprocessing

sys.path.append("..")

from apollo.downloader.video import download_files, download_m3u8
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By

DEBUG = True

with open("manga-chan_config.json") as config_file:
	config = json.loads(config_file.read())

STARTUP_TIMEOUT = config["startup_timeout"]
ACTION_TIMEOUT = config["action_timeout"]

def parse_chapter(url, link, i, urls):
    engine = Engine(url, False)
    try:
        href = engine.find_elements("href", By.PARTIAL_LINK_TEXT, link)[0]
    except IndexError:
        engine.quit()
        print(f"retry {link}")
        parse_chapter(url, link, i, urls)
    engine.click(href)
    for request in engine.driver.requests:
        if ".zip" in request.url:
            urls[i] = request.url
            break
    engine.quit()

def download_url(url, link):
    os.system(f'wget -O "{link}" "{url}"')

def download(filename, url):
    engine = Engine(url, DEBUG)
    hrefs = engine.find_elements("hrefs", By.TAG_NAME, "a")
    links = []
    for href in hrefs:
        link = href.get("href")
        if "download.php" in link:
            links.append(href.selenium_element.text)
    engine.quit()

    manager = multiprocessing.Manager()
    urls = manager.dict()

    for i in range(len(links)):
        link = links[i]
        print(f"parse {link}")
        parse_chapter(url, link, i, urls)


    processes = []
    for key, value in urls.items():
        link = links[key]
        if DEBUG:
            print_info(f"create process for href={value}")
        process = multiprocessing.Process(target=download_url, args=(value, link, ))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    for link in links:
        folder = link.replace(".zip", "")
        os.system(f"unzip {link} -d {folder}")
        os.system(f"magick mogrify -format png {folder}/*.avif")
        os.system(f"magick mogrify -format png {folder}/*.jpg")
        os.system(f"magick {folder}/*.png {folder}.pdf")

    os.system(f"pdfunite *.pdf {filename}.pdf")

if __name__ == '__main__':
	anime = "Hells_paradise"
	download(anime, config["data"][anime])