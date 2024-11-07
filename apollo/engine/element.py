from __future__ import annotations

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

from engine.logging import print_info, print_ok, print_error, print_warning

class Element:

	def __init__(self, name: str|None, xpath: str|None):
		self.name = name
		self.xpath = xpath
		self.selenium_element: WebElement = WebElement(None, None)

	def text(self):
		return self.selenium_element.text

	def clear(self):
		self.selenium_element.clear()

	def type(self, text: str, clear=False, enter=False):
		if clear: self.clear()
		self.selenium_element.send_keys(text)
		if enter: self.selenium_element.send_keys(Keys.ENTER)

	def get(self, attr: str) -> str:
		res = self.selenium_element.get_attribute(attr)
		if res is None:
			print_error(f"{self.name} do not have attribute {attr}")
			return ""
		return res

	@staticmethod
	def none():
		return Element(None, None)

	def is_none(self):
		return self.name == None and self.xpath == None