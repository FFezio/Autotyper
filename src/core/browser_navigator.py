import subprocess
import time
from pathlib import Path
from typing import Optional, Union
import playwright.sync_api
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class BrowserNavigator:
    def __init__(self):
        """
        A wrapper around the Playwright Browser class.
        """
        self._connection = sync_playwright().start()
        self._browser: Optional[Browser] = None
        self._active_window: Optional[BrowserContext] = None
        self._active_tab: Optional[Page] = None

    def setup(self, browser_path: Union[str, Path] = ""):
        """
        Sets up or connects to a new browser session
        :param browser_path: The path to the browser (optional)
        :raises playwright.sync_api.TimeoutError, playwright.sync_api.Error:
        :return:
        """
        try:
            self._browser = self._connection.chromium.connect_over_cdp("http://localhost:9222")
            self._active_window = self._browser.contexts[0]
            self._active_tab = self._active_window.new_page() if not self.active_window.pages else self.active_window.pages[0]

        except playwright.sync_api.Error:
            subprocess.Popen([browser_path, "--disable-logging", "--remote-debugging-port=9222"])
            time.sleep(4)
            self._browser = self._connection.chromium.connect_over_cdp("http://localhost:9222")
            self._active_window = self._browser.contexts[0]
            self._active_tab = self._active_window.new_page() if not self.active_window.pages else self.active_window.pages[0]

    def close(self):
        """
        Closes the browser session
        :return:
        """
        self._browser.close()
        self._connection.stop()

    def find_tab(self, value:str) -> Optional[int]:
        """
        Finds a tab from the current active window based on its url or page title.
        Returns ``None`` if no tab was found.
        :param value: The url or page title of the tab to search.
        :return:
        """

        for page in self._active_window.pages:
            if page.url == value:
                return self._active_window.pages.index(page)
            elif page.title() == value:
                return self._active_window

        return None

    def new_tab(self) -> int:
        """
        Creates a new tab for the active window and returns its index.

        **NOTE**: The new tab is not automatically focused!, for that you will need to do as follows:

            ``
            tab_index = navigator.new_tab()
            navigator.active_tab = tab_index`
            ``
        :return:
        """
        page = self._active_window.new_page()
        return self._active_window.pages.index(page)

    @property
    def active_tab(self) -> Page:
        """
        Returns the active tab
        :return:
        """
        return self._active_tab

    @active_tab.setter
    def active_tab(self, tab_index: int):
        """
        Sets the new active tab.
        :param tab_index: The index of the tab to set active.
        :return:
        """
        self._active_tab = self._active_window.pages[tab_index]

    @property
    def active_window_tabs_count(self) -> int:
        """
        Returns the total opened tabs on the active window.
        :return:
        """
        return len(self._active_window.pages)

    @property
    def windows_count(self) -> int:
        """
        Returns the total opened windows.
        :return:
        """
        return len(self._browser.contexts)

    @property
    def active_window(self) -> BrowserContext:
        """
        Returns the current active window,
        :return:
        """
        return self._active_window

    @active_window.setter
    def active_window(self, window_index: int):
        """
        Sets the new active window.
        :param window_index: The index of the window to be set active.
        :return:
        """
        self.active_tab = self._browser.contexts[window_index]
