from __future__ import annotations
import time, os, json
from typing import List

from seleniumwire import webdriver # not just selenium to support local drivers
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .element import Element
from .logging import print_info, print_error, print_ok, print_warning

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

	ACTION_TIMEOUT = 0
	STARTUP_TIMEOUT = 0

	def __init__(self, url: str, debug=False):
		service = Service(executable_path='./../drivers/yandexdriver')
		options = webdriver.ChromeOptions()
		options.add_argument("--mute-audio")
		options.page_load_strategy = 'eager'
		options.add_argument("--headless")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-blink-features=AutomationControlled")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36")
		self.DEBUG = debug
		self.driver = webdriver.Chrome(options=options, service=service)
		self.driver.maximize_window()
		self.driver.set_page_load_timeout(300)
		self.get(url)

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

	def zoom(self, zoom: int):
		self.driver.execute_script(f"document.body.style.zoom='{zoom}%'")
		if self.DEBUG:
			print_ok(f"zoom {zoom} %")

	def find_element(self, name: str, xpath: str) -> Element:
		if self.DEBUG:
			print_info(f"find element name={name} by xpath={xpath}")

		# element = Element(name, xpath)
		try:
			wait = WebDriverWait(self.driver, self.ACTION_TIMEOUT)
			element = Element(None, None)
			element.name = name
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
		# self.driver.execute_script("arguments[0].click();", element.selenium_element)
		ActionChains(self.driver).move_to_element(element.selenium_element).click().perform()
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
