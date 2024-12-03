#!../.venv/bin/python3

import json, time, os, sys, multiprocessing

sys.path.append("..")

from apollo.downloader.video import download_files, download_m3u8
from apollo.engine.logging import print_error, print_info, print_ok, print_warning
from apollo.engine.engine import Engine, By

DEBUG = True

# URL = "https://manga-chan.me/manga/148063-chainsaw-man-2.html"
# URL = "https://manga-chan.me/download/95944-jujutsu-kaisen.html"
URL = "https://manga-chan.me/download/92565-jigokuraku.html"

def parse_chapter(link, i, urls):
    engine = Engine(URL, False)
    try:
        href = engine.find_elements("href", By.PARTIAL_LINK_TEXT, link)[0]
    except IndexError:
        engine.quit()
        print(f"retry {link}")
        parse_chapter(link, i, urls)
    engine.click(href)
    for request in engine.driver.requests:
        if ".zip" in request.url:
            urls[i] = request.url
            break
    engine.quit()

def download_url(url, link):
    os.system(f'wget -O "{link}" "{url}"')

def download():
    engine = Engine(URL, DEBUG)
    hrefs = engine.find_elements("hrefs", By.TAG_NAME, "a")
    links = []
    for href in hrefs:
        link = href.get("href")
        if "download.php" in link:
        # if "online" in link:
            links.append(href.selenium_element.text)
    engine.quit()
    
    manager = multiprocessing.Manager()
    urls = manager.dict()

    for i in range(len(links)):
        link = links[i]
        print(f"parse {link}")
        parse_chapter(link, i, urls)


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
        os.system(f"magick convert {folder}/*.png {folder}.pdf")

    os.system(f"pdfunite *.pdf JJK.pdf")

if __name__ == '__main__':
    download()