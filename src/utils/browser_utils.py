import winreg
import platform
import os
import subprocess
from logging import getLogger
from typing import Any
from functools import wraps
from pathlib import Path
from typing import Optional
from winreg import HKEY_CURRENT_USER, HKEY_CLASSES_ROOT, OpenKey, QueryValueEx
import playwright.sync_api
from playwright.sync_api import Locator

logger = getLogger("autotyper")

def _win_get_default_browser_path() -> Optional[Path]:
    """
    Retrieves the full executable path of the default browser on Windows.

    Returns:
        Optional[Path]: Path to the browser executable, or None if not found.
    """
    logger.info("Trying to get default browser")
    path: Optional[Path] = None
    try:
        # Get the ProgId of the default browser
        user_choice_key = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
        with OpenKey(HKEY_CURRENT_USER, user_choice_key) as key:
            browser_name = QueryValueEx(key, "ProgId")[0]

        # Get the browser executable path
        command_key = rf"{browser_name}\shell\open\command"
        with OpenKey(HKEY_CLASSES_ROOT, command_key) as key:
            command = QueryValueEx(key, "")[0]

        # Extract and clean the executable path
        executable = command.split('"')[1] if '"' in command else command.split()[0]
        path = Path(executable)

    except (FileNotFoundError, IndexError, winreg.error) as e:
        logger.exception(f"Error retrieving default browser path: {e}")

    return path

def _posix_get_default_browser_path() -> Optional[Path]:
    path:Optional[Path] = None
    try:
        # Try xdg-settings
        browser_desktop = subprocess.check_output(
            ["xdg-settings", "get", "default-web-browser"],
            text=True
        ).strip()

        # Find the desktop file path
        desktop_file = f"/usr/share/applications/{browser_desktop}"
        if os.path.exists(desktop_file):
            with open(desktop_file) as f:
                for line in f:
                    if line.startswith("Exec="):

                        path = Path(line.split("=", 1)[1].strip().split()[0])
        return None

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print("xdg-command not supported")

    return  path

def get_default_browser() -> Optional[Path]:
    logger.info("Trying to get default browser")
    path: Optional[Path] = None

    match platform.system():
        case "Linux":
            path = Path(_posix_get_default_browser_path())
        case "Windows":
            path = Path(_win_get_default_browser_path())

    return path

def locator_exists(locator:Locator) -> bool:
    """
    Returns True if the locator count is greater than 0 (locator.count > 0).
    :param locator: The locator to check.
    :return:
    """
    return locator.count() > 0

def retries(tries:int=3):
    """
    A decorator function that retries the execution of the given function a specified number of times
    if a playwright.sync_api.TimeoutError is raised. If the function fails after the specified number of retries,
    it returns None.

    :param tries: The maximum number of retry attempts. Defaults to 3 retries.
    :return: The decorated function that retries on failure.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:  # Include 'self' in the wrapper's signature
            inner_tries = tries
            while inner_tries > 0:
                try:
                    return func(self, *args, **kwargs)  # Pass 'self' explicitly to the function
                except playwright.sync_api.TimeoutError as timeout_error:
                    inner_tries -= 1
                    if inner_tries <= 0:
                        raise timeout_error
        return wrapper

    return decorator
