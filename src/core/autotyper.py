from logging import getLogger
from pathlib import Path
from typing import Union
from playwright.sync_api import Locator, Page
from src.core.browser_navigator import BrowserNavigator
from src.core.lesson import Lesson
from src.utils.browser_utils import locator_exists, get_default_browser
from src.core.constants import TypingLocators, GoogleLoginLocators, TYPING_URL

logger = getLogger("autotyper")

class Autotyper:
    def __init__(self):
        self._browser:BrowserNavigator = BrowserNavigator()
        self._lessons_categories:dict[str, Locator] = {}
        self._lessons:dict[str,list[Lesson]] = {}

    def _is_user_logged(self) -> bool:
        typing_login_button = (self._browser.active_tab.locator(TypingLocators.LOGIN_BUTTON_CONTAINER)
                               .locator(TypingLocators.LOGIN_BUTTON))

        if not locator_exists(typing_login_button):
            return True

        typing_login_button.click()
        self._browser.active_tab.wait_for_load_state()

        return False

    def _google_login(self, email:str, password:str):
        self._browser.active_tab.wait_for_load_state()
        self._click_google_login_button()

        google_accounts_list = (self._browser.active_tab.locator(GoogleLoginLocators.ACCOUNTS_LIST_CONTAINER)
                                .locator(GoogleLoginLocators.ACCOUNTS_LIST))

        if locator_exists(google_accounts_list):
            self._select_google_account(google_accounts_list, email)

        self._google_manual_login(email, password)
        self._browser.active_tab.wait_for_load_state()

    def _click_google_login_button(self):
        self._browser.active_tab.wait_for_load_state()
        google_login_button = self._browser.active_tab.locator(GoogleLoginLocators.LOGIN_BUTTON)
        if locator_exists(google_login_button):
            logger.info("Found google login button")
            google_login_button.click()
            self._browser.active_tab.wait_for_load_state()

    def _select_google_account(self, accounts_list:Locator, email:str):
        self._browser.active_tab.wait_for_load_state()
        if locator_exists(accounts_list):
            matched_account = accounts_list.locator(f"text={email}")
            logger.info("Found google accounts")

            if locator_exists(matched_account):
                matched_account.click()
                self._browser.active_tab.wait_for_load_state()
                logger.info("Account matched with the provided email")
            else:
                logger.exception("No account matched the specified email")
                raise ValueError("No account matched the specified email")
        self._browser.active_tab.wait_for_load_state()

    def _google_manual_login(self, email:str, password:str):
        self._browser.active_tab.wait_for_load_state()
        google_email_input = self._browser.active_tab.locator(GoogleLoginLocators.EMAIL_INPUT)
        if locator_exists(google_email_input):
            print("Found email input")
            google_email_input.type(email)
            google_email_input.press("Enter")


        google_password_input = self._browser.active_tab.locator(GoogleLoginLocators.PASSWORD_INPUT)
        if locator_exists(google_password_input):
            print("Found password input")
            google_password_input.type(password)
            google_password_input.press("Enter")


        self._browser.active_tab.wait_for_load_state()

    def _login(self, email:str, password:str,):
        """
        Logs in into *www.typing.com*
        :param email: The email of the user to be logged in
        :param password: The password of the account
        :return:
        """

        if self._is_user_logged():
            logger.info("User already logged in")
            return
        logger.info("User not logged, login in.")
        self._google_login(email, password)

    def _get_categories(self):
        self._browser.active_tab.wait_for_url(TYPING_URL)
        logger.info("Getting categories list")
        lessons_categories_tabs = self._browser.active_tab.get_by_role(TypingLocators.TAB_LIST_CONTAINER).get_by_role(TypingLocators.TAB_LIST).all()
        self._lessons_categories = {category.inner_text():category for category in lessons_categories_tabs}
        logger.info(f"Found categories {self._lessons_categories.keys()}")

    def start(self, email:str, password:str,  browser_path:Union[Path, str] = None):
        """
        Starts the connection with the typing website
        :param email: The email address of the account
        :param password: The password of the account
        :param browser_path: The path containing the executable of your browser (optional)
        :return:
        """
        self._browser.setup(browser_path or get_default_browser())
        self._browser.active_tab.goto(TYPING_URL)
        self._browser.active_tab.wait_for_load_state()

        logger.info("Autotyper class started.")
        self._login(email, password)
        self._browser.active_tab.wait_for_load_state()
        self._get_categories()

    def get_lessons(self, category:str) -> list[Lesson]:
        """
        Returns the lessons of the specified category
        :param category: The category of the lessons.
        :return:
        """

        if self._browser.active_tab.url != TYPING_URL:
            logger.info("Redirecting to url: ", TYPING_URL, "To be able to retrieve lessons")
            self._browser.active_tab.goto(TYPING_URL)
            self._browser.active_tab.wait_for_load_state()

        if category not in self._lessons_categories:
            logger.exception(f"{category} is not a real category. expected: {self._lessons_categories=}")
            error_msg = f"Category '{category}' does not exist. Available categories: {list(self._lessons_categories.keys())}"
            raise ValueError(error_msg)

        picked_category:Locator = self._lessons_categories[category]
        if not locator_exists(picked_category):
            logger.exception("An error occurred while trying to retrieve a category")
            raise ValueError("Could not get the specified category")

        picked_category.click()
        lessons:list[Lesson] = []
        lessons_containers = self._browser.active_tab.locator(TypingLocators.LESSON_CONTAINER)

        logger.info(f"loading lessons of category: {category}")
        for container in lessons_containers.all():
            new_lesson = Lesson(category, container, self._browser.active_tab)
            lessons.append(new_lesson)

        return lessons

    @property
    def categories(self) -> list[str]:
        """
        Returns a list with the names of the available categories
        :return:
        """
        return [category for category in self._lessons_categories.keys()]



