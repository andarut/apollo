#!../.venv/bin/python3

import sys
sys.path.append("..")

from apollo.engine.engine import *

Apollo.debug = True

def download_film(engine: Engine):
    for request in engine.requests:
        if ".m3u8" in request.url and ".mp4" in request.url:
            DOWNLOAD_FILE(
                request.url.replace("360.mp4", "720.mp4").replace(":hls:manifest.m3u8", ""),
                "Psycho_Pass_Movie_Providence.mp4",
                request
            )
            break
        elif ".m3u8" in request.url and "index" in request.url:
            DOWNLOAD_FILE(
                request.url.replace("480", "720"),
                "master.m3u8",
                request
            )
            DOWNLOAD_FROM_M3U8("./master.m3u8", "Psycho_Pass_Movie_Providence.mp4", request.url.replace("480", "720"))
            break

# TODO: store xpaths in dict inside Apollo
Apollo.exec([
    GET("https://animego.online/26-vrata-shtejna.html"),
    WAIT(10),
    ZOOM(40),
    SWITCH_TO_FRAME("/html/body/div[1]/div/main/article/div[3]/div[7]/div[2]/iframe"),
    SWITCH_TO_FRAME("/html/body/iframe"),
    WAIT(5),
    IF_ELSE(FOUND('//*[@id="allplay"]/div[3]/div[2]/button/span'), [
        CLICK_XPATH('//*[@id="allplay"]/div[3]/div[2]/button/span'),
        # TODO: download episods
        # EPISODS_BUTTONS = engine.find_elements("EPISODS_BUTTONS", By.CLASS_NAME, "select__drop-item")
        # for button in EPISODS_BUTTONS:
        #     if "Серия" in button.get("text"):
        #         print(button.get("text"))
    ],
    [
        CLICK_XPATH('//*[@id="allplay"]/button[3]'),
        WAIT(7),
        SAVE_REQUESTS(),
        QUIT(),
        CUSTOM_COMMAND(lambda engine: download_film(engine))
    ]),
])
