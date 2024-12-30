from pathlib import Path
from typing import Union
from playwright.sync_api import Locator
from src.core.browser_navigator import BrowserNavigator
from src.core.errors import UserNotLoggedError, CategoryNotFoundError, CategoryError
from src.autotyper.lesson import Lesson
from src.utils.browser_utils import locator_exists
from src.core.constants import TypingLocators, TYPING_URL


class Autotyper:
    def __init__(self):
        self._browser_path:Union[str, Path] = ""
        self._browser:BrowserNavigator = BrowserNavigator()
        self._lessons_categories:dict[str, Locator] = {}
        self._lessons:dict[str,list[Lesson]] = {}
        self._typing_delay:float = 0.0

    @staticmethod
    def _get_typing_page(browser:BrowserNavigator):
        """
        Sets the browser active tab to be the typing page.
        :param browser:
        :return:
        """
        tab_index = browser.find_tab(TYPING_URL)
        if tab_index is None:
            browser.active_tab = browser.new_tab()
            browser.active_tab.goto(TYPING_URL)
            return

        browser.active_tab = tab_index
        browser.active_tab.wait_for_load_state("load")

    def _is_user_logged(self) -> bool:
        """
        Returns ``True`` if the user is logged in.
        :return:
        """
        typing_login_button = (
            self._browser.active_tab.locator(
                TypingLocators.LOGIN_BUTTON_CONTAINER
            ).locator(
                TypingLocators.LOGIN_BUTTON
            )
        )
        return not locator_exists(typing_login_button)

    def _get_categories(self):
        """
        Retrieves the available categories in the typing dashboard.
        :return:
        """
        self._browser.active_tab.wait_for_url(TYPING_URL)
        lessons_categories_tabs = self._browser.active_tab.get_by_role(TypingLocators.TAB_LIST_CONTAINER).get_by_role(TypingLocators.TAB_LIST).all()
        self._lessons_categories = {category.inner_text().split("\n\n")[0]:category for category in lessons_categories_tabs}

    def start(self, browser_path:Union[str, Path], typing_delay:float):
        """
        Starts the connection with the typing website
        :param browser_path: The browser path
        :param typing_delay: The delay of the keyboard in milliseconds
        :raises UserNotLoggedError playwright.sync_api.Error, playwright.sync_api.TimeOutError:
        :return:
        """
        self._browser_path = browser_path
        self._typing_delay = typing_delay

        self._browser.setup(self._browser_path)
        self._get_typing_page(self._browser)

        if not self._is_user_logged():
            raise UserNotLoggedError(TYPING_URL)
        self._get_categories()

    def close(self):
        """
        Closes the browser connection
        :return:
        """
        self._browser.close()

    def get_lessons(self, category:str) -> list[Lesson]:
        """
        Returns the lessons of the specified category
        :param category: The category of the lessons.
        :return:
        """
        self._get_categories()
        if self._browser.active_tab.url != TYPING_URL:
            self._get_typing_page(self._browser)
        if category not in self._lessons_categories:
            raise CategoryNotFoundError(category, list(self._lessons_categories.keys()))

        picked_category:Locator = self._lessons_categories[category]
        if not locator_exists(picked_category):
            raise CategoryError("Could not get the specified category. Probably the locator doesn't exists anymore")

        picked_category.click()
        lessons:list[Lesson] = []
        lessons_containers = self._browser.active_tab.locator(TypingLocators.LESSON_CONTAINER)

        for container in lessons_containers.all():
            new_lesson = Lesson(category, container, self._browser.active_tab, self._typing_delay)
            lessons.append(new_lesson)
        return lessons

    @property
    def typing_delay(self) -> float:
        return self._typing_delay

    @typing_delay.setter
    def typing_delay(self, value:float):
        self._typing_delay = value

    @property
    def categories(self) -> list[str]:
        """
        Returns a list with the names of the available categories
        :return:
        """
        return [category for category in self._lessons_categories.keys()]



