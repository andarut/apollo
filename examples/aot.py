#!../.venv/bin/python3

import json, time, os, sys, multiprocessing

# TODO: fix later
sys.path.append("..")

from downloader.video import download_files, download_m3u8
from engine.logging import print_error, print_info, print_ok, print_warning
from engine.engine import Engine

DEBUG = True

with open("aot_config.json") as config_file:
    config = json.loads(config_file.read())

STARTUP_TIMEOUT = config["startup_timeout"]
ACTION_TIMEOUT = config["action_timeout"]
VIDEO_LOADING_TIMEOUT = config["video_loading_timeout"]

def download_episode(href, urls: dict):
    if DEBUG:
        print_info(f"downloading {href}")

    engine = Engine(href)

    PLAYER_FRAME = engine.find_element(
        "PLAYER_FRAME",
        '//*[@id="iframe-player"]'
    )
    engine.driver.switch_to.frame(PLAYER_FRAME.selenium_element)

    PLAY_BUTTON = engine.find_element(
        "PLAY_BUTTON",
        '/html/body/div[1]/div[5]/a'
    )
    engine.click(PLAY_BUTTON)
    time.sleep(VIDEO_LOADING_TIMEOUT)

    for request in engine.driver.requests:
        if request.response:
            if ".m3u8" in request.url:
                m3u8_url = request.url.replace('360.mp4', '720.mp4')
                urls[href] = m3u8_url
                if DEBUG:
                    print_ok(f"found url={m3u8_url}")
                break

    engine.quit()

def download(dir, url):
    global VIDEO_LOADING_TIMEOUT

    if not os.path.isdir(dir):
        os.mkdir(dir)

    engine = Engine(url, debug=DEBUG)
    engine.STARTUP_TIMEOUT = STARTUP_TIMEOUT
    engine.ACTION_TIMEOUT = ACTION_TIMEOUT
    engine.zoom(30)
    hrefs = [a.get("href") for a in engine.find_elements("EPISODE_i", "one-series")]
    engine.quit()

    if DEBUG:
        print_ok(f"parsed {len(hrefs)} episods")

    manager = multiprocessing.Manager()
    urls = manager.dict()

    processes = []
    for href in hrefs:
        if DEBUG:
            print_info(f"create process for href={href}")
        process = multiprocessing.Process(target=download_episode, args=(href, urls,))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    if len(hrefs) != len(urls.values()):
        print_warning("not all urls parsed, maybe increase timeouts")
        VIDEO_LOADING_TIMEOUT += 10
        download(dir, url)
    else:
        if DEBUG:
            print_info(f"found {len(urls.values())} urls")

    for i in range(len(hrefs)):
        path = f"{dir}/{dir}.E{(i+1):02}.mp4"
        url = urls[hrefs[i]]
        download_m3u8(url, path, DEBUG)


# for season in config["data"].keys():
#     download(season, config["data"][season]["URL"])

if __name__ == '__main__':
    season = "Attack.on.Titan.S02"
    download(season, config["data"][season]["URL"])
