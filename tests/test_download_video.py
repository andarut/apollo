import unittest, sys, os

# TODO: fix later
sys.path.append("..")

from downloader.video import download_m3u8

class TestDownloadVideo(unittest.TestCase):

    def test_m3u8(self):
        download_m3u8("https://cloud.kodik-cdn.com/animetvseries/98417f17eb06640a202c0dbc01e0b10baa3c9b04/55e2bfeacc5202e845cb0932a7de2c9b:2024110711/360.mp4:hls:manifest.m3u8", "test.mp4", True)
        os.system("rm -f test.mp4")

if __name__ == "__main__":
    unittest.main()
