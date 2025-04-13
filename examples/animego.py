#!../.venv/bin/python3

import sys
import json
sys.path.append("..")

from apollo.engine.engine import *

Apollo.debug = True

ANIME_KEY = "Lazarus"

config = json.load(open("animego_config.json", "r"))["data"][ANIME_KEY]
URL = config["URL"]
VOICES = config["VOICES"]
start_episode = 1 # set -1 to download all avaliable episods

def episode_template(num):
    return f"Lazarus.E{num:02}.mp4"

current_episode = start_episode if start_episode != -1 else 1

def download_episode(engine: Engine):
    if not engine: return
    for request in Apollo.requests:
        print(request.url)
        if ".m3u8" in request.url and ".mp4" in request.url:
            DOWNLOAD_FILE(
                request.url.replace("360.mp4", "720.mp4").replace(":hls:manifest.m3u8", ""),
                episode_template(current_episode),
                request
            )(engine)
            break

Apollo.exec([
    GET(URL),
    WAIT(2),
    ZOOM(40),

    # click watch button
    # CLICK_XPATH("/html/body/div[4]/div/div[1]/div/div[1]/main/div/div[1]/div[1]/div[2]/a/span[2]"),
    CLICK_TEXT("Смотреть онлайн"),

    # select episode
    TYPE('//*[@id="video-series-number-input"]', f"{current_episode}", enter=True),
    WAIT(2),

    # select audio
    # CLICK_XPATH("/html/body/div[4]/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div[2]/div/div/div[1]/span[2]/span"),
    CLICK_TEXT(VOICES),

    # switch to player frame
	SWITCH_TO_FRAME("/html/body/div[4]/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/iframe"),
	WAIT(2),
	
    # click play
    CLICK_CLASS("play_button"),

    # wait for requests
    WAIT(10),
    SAVE_REQUESTS(),
    WAIT(2),
    QUIT(),

    # download from requests
    CUSTOM_COMMAND(lambda engine: download_episode(engine))
])