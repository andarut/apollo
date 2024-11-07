	@staticmethod
	def download_animego(URL, AUDIO, SEASON, DIR, VPN):

		if VPN:
			print("STARTING VPN...")
			os.system('./vpn_on.sh')
			time.sleep(3)


		engine = Engine(URL)

		EPISODS_COUNT_TEXT = engine.find_element(
			"EPISODS_COUNT_TEXT",
			'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[2]'
		)
		if EPISODS_COUNT_TEXT.is_none():
			return Downloader.download_animego(URL, AUDIO, SEASON, DIR, VPN)

		TITLE_TEXT = engine.find_element(
			"TITLE_TEXT",
			'//*[@id="content"]/div/div[1]/div[2]/div[2]/div/div/div[1]/ul/li[1]'
		)
		if TITLE_TEXT.is_none() or re.search('[a-zA-Z]', TITLE_TEXT.text()) is None:
			TITLE_TEXT = engine.find_element(
				"TITLE_TEXT",
				'//*[@id="content"]/div/div[1]/div[2]/div[2]/div/div/div[1]/ul/li[2]'
			)
			if TITLE_TEXT.is_none() or re.search('[a-zA-Z]', str(TITLE_TEXT.text())) is None:
				Logger.error("TITLE not found, specify name manually")
				TITLE = str(input("TITLE: "))
				
		TITLE = ''.join(e for e in TITLE if e.isalnum() or e == ' ')
		TITLE = TITLE.replace(" ", ".")
		print(f"DOWNLOADING {TITLE}")
		try:
			epidods_count = int(EPISODS_COUNT_TEXT.text())
		except ValueError:
			epidods_count = 1
		print(f"epidods_count = {epidods_count}")

		AGING_TEXT = engine.find_element(
			"AGING_TEXT",
			'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[10]/span'
		)
		if AGING_TEXT.is_none():
			AGING_TEXT = engine.find_element(
				"AGING_TEXT",
				'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[8]/span'
			)
			if AGING_TEXT.is_none():
				AGING_TEXT = engine.find_element(
					"AGING_TEXT",
					'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[7]/span'
				)
				if AGING_TEXT.is_none():
					Downloader.download_animego(URL, AUDIO, SEASON, DIR, VPN)
					return

		AGING = str(AGING_TEXT.text())

		if "NC" in AGING:
			AGING_TEXT = engine.find_element(
				"AGING_TEXT",
				'//*[@id="content"]/div/div[1]/div[2]/div[3]/dl/dd[9]/span'
			)
			AGING = str(AGING_TEXT.text())

		print(f"AGING = {AGING}")

		engine.quit()
		base_urls = []

		i = 1
		while i <= epidods_count:

			print(i)

			if Downloader.url_exist(i):
				print(f"URL for {i} exist - skip")
				i += 1
				continue

			subengine = Engine(URL)

			WATCH_BUTTON = subengine.find_element(
				"WATCH_BUTTON",
				'//*[@id="content"]/div/div[1]/div[1]/div[2]/a/span[2]'
			)

			if WATCH_BUTTON.is_none():
				subengine.quit()
				continue

			subengine.click(WATCH_BUTTON)

			subengine.zoom(30)

			if "18" in AGING:

				BUTTON_18 = subengine.find_element(
					"BUTTON_18",
					'//*[@id="video-player"]/div[1]/div/div[2]/button[2]'
				)

				if BUTTON_18.is_none():
					subengine.quit()
					continue

				subengine.click(BUTTON_18)


			# доступные озвучки
			try:
				AUDIO_BUTTON = [el for el in subengine.find_elements("audio", "video-player-toggle-item") if el.text() == AUDIO][0]
			except IndexError:
				subengine.quit()
				continue

			subengine.click(AUDIO_BUTTON)

			if i != 1:
				EPISODE_INPUT = subengine.find_element(
					"EPISODE_INPUT",
					'//*[@id="video-series-number-input"]'
				)

				if EPISODE_INPUT.is_none():
					subengine.quit()
					continue

				if not subengine.type(EPISODE_INPUT, str(i), clear=True, enter=True):
					subengine.quit()
					continue

			PLAYER_FRAME = subengine.find_element(
				"PLAYER_FRAME",
				# '//*[@id="video-player"]/div[2]/div[1]/div[1]/iframe'
				"/html/body/div[4]/div/div[1]/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/iframe"
			)

			if PLAYER_FRAME.is_none():
				subengine.quit()
				continue

			ActionChains(subengine.driver).move_to_element(PLAYER_FRAME.selenium_element).click().perform()

			# wait for ads
			time.sleep(120)

			# wait for content
			time.sleep(10)

			# get base_url for future downloades
			base_url = ""
			for request in subengine.driver.requests:
				if request.response:
					if ".m4s" in request.url and "yandex" not in request.url:
						base_url = request.url.split("_")[0]
						print(f"FOUND BASE URL {base_url}")
						Downloader.write_url(base_url)
						base_urls.append(base_url)
						break

			if len(base_url) == 0:
				mp4_url = ""
				print("TRYING TO FIND M3U8 MANIFEST...")
				# find m3u8 manifest
				for request in subengine.driver.requests:
					if request.response:
						if ".m3u8" in request.url:
							m3u8_url = request.url.split('m3u8')[0] + "m3u8"
							mp4_url = m3u8_url.replace(':hls:manifest.m3u8', '')
							mp4_url = mp4_url.replace('360.mp4', '720.mp4')
							print(f"FOUND BASE URL {mp4_url}")
							base_urls.append(mp4_url)
							Downloader.write_url(mp4_url)
							break
				if len(mp4_url) == 0:
					mp4_url = ""
					print("TRYING TO FIND FULL MP4 ...")
					# find full mp4
					for request in subengine.driver.requests:
						if request.response:
							if ".mp4" in request.url and "noip" in request.url:
								mp4_url = request.url
								print(f"FOUND BASE URL {mp4_url}")
								base_urls.append(mp4_url)
								Downloader.write_url(mp4_url)
								break
					if len(mp4_url) == 0:
						Logger.error("BASE_URL NOT FOUND")
						subengine.quit()
						continue

			subengine.quit()
			i += 1

		if VPN:
			os.system('./vpn_off.sh')
			time.sleep(3)

		base_urls = []
		with open(URLS_PATH, "r") as f:
			for line in f.readlines():
				if line != "\n":
					base_urls.append(line.replace("\n", ""))

		if len(base_urls) != epidods_count:
			print(f"not enough urls {len(base_urls)}/{epidods_count}")
			exit(1)

		print(f"BASE_URLS = {base_urls}")

		for i in range(1, len(base_urls)+1):
			base_url = base_urls[i-1]
			filename = f"{DIR}/{TITLE}.S{SEASON:02}.E{i:02}.mp4" if SEASON != 0 else f"{DIR}/{TITLE}.E{i:02}.mp4"
			Downloader.download_video(base_url, filename)
			if not os.path.isfile(filename):
				print("donwloading error")
				exit(1)

		os.system(f"rm -f {URLS_PATH} && touch {URLS_PATH}")


LIST = [

	# Гены AI
	# {
	# 	"URL": "https://animego.org/anime/geny-iskusstvennogo-intellekta-2340",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 0
	# },

	# Токоийский гуль (Пинто)
	# {
	# 	"URL": "https://animego.org/anime/tokiyskiy-gul-pinto-246",
	# 	"AUDIO": "AniDUB",
	# 	"SEASON": 0,
	# 	"VPN": False
	# },

	# # Токоийский гуль (Джек)
	# {
	# 	"URL": "https://animego.org/anime/tokiyskiy-gul-dzhek-247",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 0,
	# 	"VPN": False
	# },

	# # Токийский гуль (Сезон 1)
	# {
	# 	"URL": "https://animego.org/anime/tokyo-ghoul-sv1-243",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 1,
	# 	"VPN": True
	# },

	# # Токийский гуль (Сезон 2)
	# {
	# 	"URL": "https://animego.org/anime/tokiyskiy-gul-2-244",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 2,
	# 	"VPN": True
	# },

	# Токийский гуль (Сезон 3)
	# {
	# 	"URL": "https://animego.org/anime/tokyo-ghoul-re-245",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 3,
	# 	"VPN": False
	# },

	# # Токийский гуль (Сезон 4)
	# {
	# 	"URL": "https://animego.org/anime/tokyo-ghoul-re-2nd-season-709",
	# 	"AUDIO": "AniLibria",
	# 	"SEASON": 4,
	# 	"VPN": False
	# },

	# # Человек бензопила
	# {
	# 	"URL": "https://animego.org/anime/chelovek-benzopila-2119",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 0,
	# 	"VPN": False
	# }

	# Тетрадь смерти
	# {
	# 	"URL": "https://animego.org/anime/death-note-v2-95",
	# 	"AUDIO": "2x2",
	# 	"SEASON": 0,
	# 	"VPN": False
	# },

	# Тетрадь смерти (фильмы)
	# {
	# 	"URL": "https://animego.org/anime/tetrad-smerti-perezapis-glazami-boga-96",
	# 	"AUDIO": "AniDUB",
	# 	"SEASON": 0,
	# 	"VPN": False
	# }

	# Dr Stone (сезон 1)
	# {
	# 	"URL": "https://animego.org/anime/dr-stone-2v-1105",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 1,
	# 	"VPN": True
	# },

	# Dr Stone (сезон 2)
	# {
	# 	"URL": "https://animego.org/anime/doktor-stoun-kamennye-voyny-1698",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 2,
	# 	"VPN": True
	# }

	# Dr Stone (сезон 3)
	# ждем озвучку
	# {
	# 	"URL": "https://animego.org/anime/doktor-stoun-kamennye-voyny-1698",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 1,
	# 	"VPN": True
	# }

	# One Piece
	#

	# Наруто
	# {
	# 	"URL": "https://animego.org/anime/naruto-102",
	# 	"AUDIO": "2x2",
	# 	"SEASON": 0,
	# 	"VPN": False
	# }

	# # Наруто Ураганные хроники
	# {
	# 	"URL": "https://animego.org/anime/naruto-uragannye-hroniki-103",
	# 	"AUDIO": "2x2",
	# 	"SEASON": 0,
	# 	"VPN": False
	# }

	# Жизнь без оружия
	# {
	# 	"URL": "https://animego.org/anime/zhizn-bez-oruzhiya-1272",
	# 	"AUDIO": "Студийная Банда",
	# 	"SEASON": 1,
	# 	"VPN": False
	# },

	# Жизнь без оружия (сезон 2)
	# {
	# 	"URL": "https://animego.org/anime/zhizn-bez-oruzhiya-2-1583",
	# 	"AUDIO": "Студийная Банда",
	# 	"SEASON": 2,
	# 	"VPN": False
	# }

	# {
	# 	"URL": "https://animego.org/anime/magicheskaya-bitva-1635",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 1,
	# 	"VPN": False
	# },
	# {
	# 	"URL": "https://animego.org/anime/magicheskaya-bitva-0-film-2132",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 0,
	# 	"VPN": False
	# },
	# {
	# 	"URL": "https://animego.org/anime/magicheskaya-bitva-2-2332",
	# 	"AUDIO": "Профессиональный многоголосый",
	# 	"SEASON": 2,
	# 	"VPN": False
	# },
	
]

DIR = "."
for anime in LIST:
	URL, AUDIO, SEASON, VPN = anime.values()
	Downloader.download(URL, AUDIO, SEASON, DIR, VPN)
