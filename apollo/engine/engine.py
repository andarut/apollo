from __future__ import annotations
import time, os, json
from typing import List
from collections.abc import Callable
from functools import partial
import functools

from seleniumwire import webdriver  # not just selenium to support local drivers
from seleniumwire.request import Request

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select



from .element import Element
from .logging import print_info, print_error, print_ok, print_warning
from ..downloader.video import download_file, download_m3u8


# chain should have state (to store variables) to support if else
# also user can have own block for chain (for example when downloading is exotic)
# also add saving state to file for reloading, so in case of crash we not must start all over

# TODO: add debug parameter (same as engine)
# TODO: rewrite commands without wrapper so intelli sense could wor

def command(func: Callable) -> Callable:
	@functools.wraps(func)
	def wrapper(*args, **kwargs) -> Callable[[Engine], None]:
		return lambda engine: func(*args, engine=engine, **kwargs)
	return wrapper

@command
def GET(url: str, engine: Engine | None = None):
	if not engine:
		return
	engine.get(url)

@command
def CLICK_XPATH(xpath: str, engine: Engine | None = None):
	if not engine:
		return
	element = engine.find_element("", xpath)
	engine.click(element)

@command
def CLICK_TEXT(text: str, engine: Engine | None = None):
	if not engine:
		return
	elements = engine.find_elements("", By.XPATH, f"//*[contains(text(), '{text}')]")
	engine.click(elements[0])

@command
def CLICK_CLASS(class_name: str, engine: Engine | None = None):
	if not engine:
		return
	elements = engine.find_elements("", By.XPATH, f"//*[contains(@class, '{class_name}')]")
	engine.click(elements[0])

@command
def TYPE(xpath: str, text: str, clear=False, enter=False, engine: Engine | None = None):
	if not engine:
		return
	element = engine.find_element("", xpath)
	engine.type(element, text, clear, enter)


@command
def SWITCH_TO_FRAME(xpath: str, engine: Engine | None = None):
	if not engine:
		return
	frame = engine.find_element("", xpath)
	if frame.is_none():
		exit(1)
	engine.driver.switch_to.frame(frame.selenium_element)

@command
def ZOOM(percent: int, engine: Engine | None = None):
	if not engine:
		return
	engine.zoom(percent)

@command
def FOUND(xpath: str, engine: Engine | None = None):
	if not engine:
		return
	return engine.find_element("", xpath) is not Element.none()

@command
def IF_ELSE(condition, if_chain: List[Callable[[Engine], None]], else_chain: List[Callable[[Engine], None]], engine: Engine | None = None):
	if not engine:
		return
	for command in if_chain if condition else else_chain:
		command(engine)

@command
def DOWNLOAD_REQUEST(request: Request, path: str, engine: Engine | None = None):
	if not engine:
		return
	download_file(request.url, path, request.headers.items())

@command
def DOWNLOAD_FILE(url: str, path: str, request: Request, engine: Engine | None = None):
	print_info(f"{url} -> {path}")
	if not engine:
		return
	download_file(url, path, request.headers.items())

@command
def DOWNLOAD_FROM_M3U8(m3u8_url: str, path: str, prefix="", engine: Engine | None = None):
	if not engine:
		return
	download_m3u8(m3u8_url=m3u8_url, path=path, prefix=prefix)

@command
def WAIT(seconds: int, engine: Engine | None = None):
	if not engine:
		return
	time.sleep(seconds)

@command
def SAVE_REQUESTS(engine: Engine | None = None):
	if not engine:
		return
	Apollo.requests = engine.driver.requests

@command
def CUSTOM_COMMAND(action: Callable[[Engine], None], engine: Engine | None = None):
	if not engine:
		return
	action(engine)

@command
def QUIT(engine: Engine | None = None):
	if not engine:
		return
	engine.quit()

class Apollo:

	debug = False
	engine: Engine | None = None
	requests: List[Request] = []

	@staticmethod
	def exec(blocks: List[Callable[[Engine], None]]):
		Apollo.engine = Engine(url="", debug=Apollo.debug, headless=False)
		for block in blocks:
			block(Apollo.engine)
		if Apollo.engine.working:
			Apollo.engine.quit()


os.environ["PYTHONTRACEMALLOC"] = '1'

class By:
	"""Set of supported locator strategies."""
	ID = "id"
	XPATH = "xpath"
	LINK_TEXT = "link text"
	PARTIAL_LINK_TEXT = "partial link text"
	NAME = "name"
	TAG_NAME = "tag name"
	CLASS_NAME = "class name"
	CSS_SELECTOR = "css selector"

class Engine:
	ACTION_TIMEOUT = 10
	STARTUP_TIMEOUT = 10

	@property
	def requests(self):
		return self.driver.requests

	def __init__(self, url: str, debug=False, headless=True):
		options = webdriver.ChromeOptions()
		options.add_argument("--mute-audio")
		options.page_load_strategy = 'eager'
		if headless:
			options.add_argument("--headless")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-blink-features=AutomationControlled")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36")
		self.DEBUG = debug
		self.working = True
		self.driver = webdriver.Chrome(options=options)
		self.driver.maximize_window()
		self.driver.set_page_load_timeout(300)

		if self.DEBUG:
			print_ok(f"init engine with url={url} and debug={debug}")

	def get(self, url: str):
		while True:
			try:
				if self.DEBUG:
					print_info(f"get {url}")
				self.driver.get(url)
				break
			except TimeoutException:
				print_warning(f"timeout for url={url}")
		if self.DEBUG:
			print_ok(f"get loaded {url}")
		time.sleep(self.STARTUP_TIMEOUT)

	def load_cookies(self, cookies_file: str = "cookies.txt"):
		"""
		Load cookies from a Netscape-formatted cookies file (cookies.txt) into the current driver.
		Make sure you have already navigated to a URL matching the cookies' domain.
		"""
		if not os.path.exists(cookies_file):
			print_error(f"Cookie file {cookies_file} does not exist")
			return

		with open(cookies_file, 'r') as f:
			for line in f:
				line = line.strip()
				# Skip comments and empty lines
				if not line or line.startswith('#'):
					continue
				# Expected format: domain, flag, path, secure, expiry, name, value
				parts = line.split('\t')
				if len(parts) != 7:
					print_warning(f"Skipping invalid cookie line: {line}")
					continue

				domain, flag, path, secure, expiry, name, value = parts
				cookie = {
					"domain": domain,
					"name": name,
					"value": value,
					"path": path,
					"secure": secure.lower() == "true"
				}
				if expiry.isdigit():
					cookie["expiry"] = int(expiry)
				try:
					self.driver.add_cookie(cookie)
					if self.DEBUG:
						print_ok(f"Loaded cookie: {name}")
				except Exception as e:
					print_error(f"Failed to add cookie {name}: {str(e)}")
		# Refresh to ensure cookies are applied
		self.driver.refresh()
		if self.DEBUG:
			print_ok("Cookies loaded and page refreshed.")

	def zoom(self, zoom: int):
		self.driver.execute_script(f"document.body.style.zoom='{zoom}%'")
		if self.DEBUG:
			print_ok(f"zoom {zoom} %")

	def find_element(self, name: str, xpath: str) -> Element:
		if self.DEBUG:
			print_info(f"find element name={name} by xpath={xpath}")
		try:
			wait = WebDriverWait(self.driver, self.ACTION_TIMEOUT)
			element = Element(name, xpath)
			element.selenium_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
		except TimeoutException:
			print_error(f"{name} not found")
			return Element.none()
		return element

	def find_elements(self, name: str, by=By.CLASS_NAME, value="") -> List[Element]:
		if self.DEBUG:
			print_info(f"find elements name={name} by={by} value={value}")
		elements = []
		try:
			for el in self.driver.find_elements(by, value):
				element = Element(name, "")
				element.selenium_element = el
				elements.append(element)
		except NoSuchElementException:
			print_error(f"{name} not found")
			return []
		if self.DEBUG:
			print_ok(f"{name} found {len(elements)} times")
		return elements

	def click(self, element: Element):
		if self.DEBUG:
			print_info(f"{element.name} clicked")
		try:
			# ActionChains(self.driver).move_to_element(element.selenium_element).click().perform()
			element.selenium_element.click()
			
		except TimeoutException:
			print_warning("Timeout when click, trying again")
			self.click(element)
		except ElementClickInterceptedException:
			print_warning("Other element would receive the click")
			print_info("Trying click with JS")
			self.driver.execute_script("arguments[0].click();", element.selenium_element)
		time.sleep(self.ACTION_TIMEOUT)

	def type(self, element: Element, text: str, clear=False, enter=False) -> bool:
		if self.DEBUG:
			print_info(f"{element.name} type text={text} with clear={clear}, enter={enter}")
		try:
			element.type(text, clear, enter)
		except ElementNotInteractableException:
			print_error(f"{element.name} not interactable")
			return False
		time.sleep(self.ACTION_TIMEOUT)
		if self.DEBUG:
			print_ok(f"{element.name} typed text={text}")
		return True

	def quit(self):
		if self.DEBUG:
			print_info(f"quit driver")
		self.driver.quit()
		self.working = False
