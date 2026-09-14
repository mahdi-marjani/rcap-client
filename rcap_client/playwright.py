from playwright.sync_api import Page, Locator

from .browser import Browser
from .solver import RecaptchaSolver
from .detector import Detector

class PlaywrightBrowser(Browser):

    def __init__(self, page: Page):
        self.main_page = page
        self.current_frame = page

    def switch_to_frame(self, selector: str):
        self.switch_to_main_frame()

        iframe = self.main_page.locator(f"xpath={selector}")
        iframe.wait_for(state="attached")

        self.current_frame = iframe.element_handle().content_frame()

    def switch_to_main_frame(self):
        self.current_frame = self.main_page

    def click(self, selector: str, timeout: float):
        self.current_frame.locator(f"xpath={selector}").click(timeout=timeout * 1000)

    def wait_for(self, selector: str, timeout: float, status: str):
        _STATES = {
            'clickable': 'visible',
            'present': 'attached',
        }
        state = _STATES[status]
        self.current_frame.locator(f"xpath={selector}").wait_for(
            state=state, timeout=timeout * 1000
        )

    def get_attribute(self, element: Locator, name: str):
        return element.get_attribute(name)

    def find_element(self, selector: str, timeout: float, status: str):
        _STATES = {
            'present': 'attached',
        }
        state = _STATES[status]
        locator = self.current_frame.locator(f"xpath={selector}")
        locator.wait_for(state=state, timeout=timeout * 1000)
        return locator

    def find_elements(self, selector: str, timeout: float, status: str):
        _STATES = {
            'present': 'attached',
        }
        state = _STATES[status]
        locator = self.current_frame.locator(f"xpath={selector}")
        locator.first.wait_for(state=state, timeout=timeout * 1000)
        return locator.all()

    def find_element_inside_element(self, element: Locator, selector: str):
        return element.locator(f"xpath={selector}").first

    def get_element_text(self, element: Locator):
        return element.inner_text()

class PlaywrightRecaptchaSolver(RecaptchaSolver):

    def __init__(self, page):
        super().__init__(
            browser=PlaywrightBrowser(page),
            detector=Detector(),
        )