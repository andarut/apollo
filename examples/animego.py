#!../.venv/bin/python3

import sys
import json
sys.path.append("..")

from apollo.engine.engine import *
from apollo.downloader.video import download_chunks

Apollo.debug = True

def download_url(URL: str, i):
    if os.path.exists(episode_template(i)): return
    Apollo.exec([
        GET(URL),
        ZOOM(40),

        # 18+
        # CLICK_TEXT("Мне есть 18+"),

        # click watch button
        # CLICK_XPATH("/html/body/div[4]/div/div[1]/div/div[1]/main/div/div[1]/div[1]/div[2]/a/span[2]"),
        CLICK_TEXT("Смотреть онлайн"),

        WAIT(2),

        # select audio
        CLICK_TEXT_AND_CLASS("Озвучка", "cursor-pointer"),
        CLICK_TEXT_AND_CLASS(VOICES, "video-player-toggle-item-name"),

        # switch player
        # CLICK_TEXT("Плеер"),
        # CLICK_TEXT_AND_CLASS("Kodik", "video-player-toggle-item-name"),

        # select episode
        TYPE('//*[@id="video-series-number-input"]', f"{i}", enter=True),
        WAIT(2),

        # switch to player frame
        SWITCH_TO_FRAME("/html/body/div[4]/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/iframe"),
        
        # click play
        # TODO: check for avaliable players
        CLICK_CLASS("play_button"),
        # CLICK_CLASS("vjs-big-play-button"),

        # wait for ads
        # WAIT(120),

        # wait for requests
        WAIT(3),
        SAVE_REQUESTS(),
        QUIT(),

        # download from requests
        CUSTOM_COMMAND(lambda engine: download_episode(i, engine))
    ])

ANIME_KEY = "Lazarus"

config = json.load(open("animego_config.json", "r"))["data"][ANIME_KEY]

VOICES = config["VOICES"]

def episode_template(num):
    return f"{ANIME_KEY}.E{num:02}.mp4"

def download_episode(i: int, engine: Engine):
    if not engine: return
    for request in Apollo.requests:
        if ".m3u8" in request.url and ".mp4" in request.url:
            DOWNLOAD_FILE(
                request.url.replace("360.mp4", "720.mp4").replace(":hls:manifest.m3u8", ""),
                episode_template(i),
                request
            )(engine)
            break
        if "init_1" in request.url:
            # example: https://grace.ya-ligh.com/gr/GradwoRd89Y/5edd56a836463_init_1.m4s
            base_url = request.url.split('_')[0]
            download_chunks(base_url, episode_template(i), False)


URL = config["URL"]
download_url(URL, 11)

# download_chunks(base_url="https://grace.ya-ligh.com/gr/GradwoRd89Y/5edd56a836463", filename="test.mp4", debug=True)