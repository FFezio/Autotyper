from typing import Union


class AutotyperError(Exception):
    pass

class CategoryError(AutotyperError):
    pass

class URLChangedError(AutotyperError):
    pass

class CategoryNotFoundError(CategoryError):
    def __init__(self, category:str, expected_categories:Union[list, tuple, set]):
        message = f"The category: {category} is not a valid category. expected one of these: {expected_categories}"
        super().__init__(message)

class UserNotLoggedError(AutotyperError):
    def __init__(self, page_url:str):
        message = f"User was not found to be logged in on page: {page_url}"
        super().__init__(message)

class BrowserNotFoundError(AutotyperError):
    def __init__(self, browser_path:str):
        message = f"Could not find a browser executable in path: {browser_path}"
        super().__init__(message)

class DefaultBrowserNotFoundError(AutotyperError):
    def __init__(self):
        message = f"Could not find a default browser"
        super().__init__(message)


