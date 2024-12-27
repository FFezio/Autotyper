from typing import Optional
from playwright.sync_api import Page, Locator
from src.core.constants import TypingLessonLocators, TYPING_URL
from src.core.errors import URLChangedError
from src.utils.browser_utils import locator_exists, retries
from src.core.constants import SPECIAL_KEYS

def _is_special_key(key:str) -> bool:
    """
    Returns ``True`` if the key is special.
    :param key: The string representing the keyboard key.
    :return:
    """
    return key in SPECIAL_KEYS

def _get_actual_key(key:str) -> str:
    """
    Returns the actual key that the special keyboard key represents.

    Raises a ``ValueError`` if the key doesn't match a special keyboard key.
    :param key: The string representing the keyboard key.
    :raise ValueError:
    :return:
    """
    if key not in SPECIAL_KEYS:
        message = "The key: " + key, " is not a special key or is not registered as it."
        raise ValueError(message)
    return SPECIAL_KEYS[key]

def _get_special_key(key:str) -> str:
    """
    Returns the special key of the current key.
    Raises a ``ValueError`` if the key doesn't match a special keyboard key.
    :param key: The string representing the keyboard key.
    :raise ValueError:
    :return:
    """
    if key not in SPECIAL_KEYS.values():
        message = "The key: " + key, " doesn't contain a special key."
        raise ValueError(message)

    special_key_values = list(SPECIAL_KEYS.values())
    special_key_keys = list(SPECIAL_KEYS.keys())
    return special_key_keys[special_key_values.index(key)]


class KeyboardKey:
    def __init__(self, *, main_key:str, secondary_key:Optional[str]):
        """
        Represents a single key from the typing keyboard.
        :param main_key: The character that is displayed when the keyboard key is pressed. e.g: `0`
        :param secondary_key: The character that is displayed when the keyboard key is pressed alongside with `Shift`. e.g `)`
        """
        self._is_special:bool = _is_special_key(main_key)
        self._main_key:str = main_key if not self._is_special else _get_actual_key(main_key)
        self._secondary_key:Optional[str] = secondary_key
        self._shifted = False

    def __str__(self):
        return self.key

    def __repr__(self):
        return (
            f"KeyboardKey: Main key -> [{self.main_key}], Secondary key -> [{self._secondary_key}],"
                f" is special: [{self._is_special}], is shifted -> [{self.shift}]"
        )

    @property
    def shift(self) -> bool:
        return self._shifted

    @shift.setter
    def shift(self, value:bool):
        self._shifted = value

    @property
    def key(self) -> str:
        if self._shifted and self._secondary_key:
            return self._secondary_key.capitalize()

        elif self._shifted and not self._secondary_key:
            return self._main_key.capitalize()

        elif self._is_special:
            return self._main_key

        return self._main_key.lower()

    @property
    def is_special(self) -> bool:
        return self._is_special

    @property
    def main_key(self) -> str:
        return self._main_key

    @property
    def secondary(self) -> str:
        return self._secondary_key

class TypingKeyboard:
    def __init__(self, typing_page:Page):
        """
        Represents the typing keyboard of the lessons.
        :param typing_page: The typing page pointing to the exercise url.
        """
        self._typing_page = typing_page

    @staticmethod
    def _extract_key_labels(active_keys_locator: Locator) -> Optional[list[list[str]]]:
        """
        Helper method that extract every active key on the typing website
        And returns them as a list of lists containing the raw keyboard key representation.

        Example:
            html keyboard keys:

                [SHIFT] KEY:
                <div class="keyboard-key ...">
                  <div class="key-label">
                    <span class="key-label--0">Shift</span>
                    <span class="key-label--1">⇧</span>
                  </div>
                </div>

                [Z] KEY:
                <div class="keyboard-key ...">
                  <div class="key-label">z</div>
                </div>

            This method extract the string inside the spans and convert them into a list like ["Shift", "⇧"]
            and the string inside the key-label div is converted into: ["Z"] and append both list into a single list
            outputting something like this: [["Shift", "⇧"], ["Z"]]

        :param active_keys_locator: The playwright locator containing the list of divs of class "keyboard-key"
        :return:
        """
        raw_keys: list[list[str]] = []
        # Iterates through the list of divs containing the keyboard key characters
        for key in active_keys_locator.all():
            keys = []

            # Iterates over every character inside the keyboard key.
            for characters in key.locator(TypingLessonLocators.KEY_LABEL).all():
                # checks if there are spans inside the keyboard key and extract each character.
                # If no spans are found then it will extract every string inside the divs with the class "keyboard-key"
                # In any case the resulting characters will be appended into a list like this: ["main key", "secondary"]
                inner_keys = characters.locator("span")
                if locator_exists(inner_keys):
                    keys.extend(
                        character.inner_text() for character in inner_keys.all())
                else:
                    keys.extend(
                        character.inner_text() for character in characters.all())
            raw_keys.append(keys)

        out_keys = raw_keys if any(inner_list for inner_list in raw_keys) else None
        return out_keys

    @staticmethod
    def _process_raw_keys(raw_keys:list[list[str]]) -> list[KeyboardKey]:
        """
        Helper method used to process the list of raw keys [[str, str], [str, str] [...]] and convert them
        into a list of ``KeyboardKey`` objects.
        :param raw_keys: A list of lists containing strings representing a character of a keyboard key. e.g: [["Shift", "⇧"], ["A"]]
        :return:
        """

        processed_keys = []
        # key group represents the div that acts as a keyboard key on the typing page.
        # something like this:
        # <div clas="is-active ...">
        #   <div class="keyboard-key">
        #   <...>
        #   </div>
        # </div>
        # So we are effectively looping into each inner div with the class "keyboard-key"
        # and extract each character to create a keyboard key representation using
        # the ``KeyboardKey`` class
        # after that all the keys are appended onto a list and returned.
        for key_group in raw_keys:
            main_key = None
            secondary_key = None

            if len(key_group) == 3:
                # When there are 3 positions on the key group that means that inner spans are inside a single div
                # with the class ".key-label" like this:
                #
                # <div class="key-label">
                #   <span class="key-label--0">Caps</span>
                #   <span class="key-label--1">Lock</span>
                #   <span class="key-label--2">⇪</span>
                # </div>
                # Since we only want the special key we extract the key at index 2.
                # This is possible because the ``ray_keys`` list contains the keys on the same order as they are on the
                # html page. like this:
                #   [["Caps","Lock", "⇪"], [...]]
                #
                main_key = key_group[2]  # Third element is likely the main key

            elif len(key_group) == 2:
                # When the key group takes 2 positions, the special key might be flipped.
                # So we check if the key at position 0 is not the special key
                # at if it isn't then it means that the key at position 1 is the special key.
                # Note that this is true for keys like SHIFT that are placed twice on the keyboard (left and right)
                # When the key is pressed on the right we want to get the special key that is at index 0
                # When the key is pressed on the left we want to get the special key that is at index 1!
                # a visual representation could be:
                # special key = [⇧]
                #
                # [idx=0 ,idx=1]                   [idx=0 ,idx=1] <- index on the list
                # [shift,  [⇧]] [][][][][][][][][] [[⇧],   shift] <- Keyboard representation
                #
                main_key = key_group[1] if not _is_special_key(key_group[0]) else key_group[0]
                secondary_key = key_group[0]

            elif len(key_group) == 1:
                # When the key group just contains one index that means that a single div
                # with the class "key-label" contains the raw key.
                # so the list ``raw_keys`` just returns it as is, like this:
                # [["A"],[...]] <- A represents the [A] keyboard key which just contains a single character.
                main_key = key_group[0]


            processed_keys.append(KeyboardKey(main_key=main_key, secondary_key=secondary_key))
        return processed_keys

    @staticmethod
    def _apply_shift_effect(keys: list[KeyboardKey]) -> list[KeyboardKey]:
        """
        Helper method that returns a list of ``KeyboardKey`` objects with the shift effect applied
        if the ``keys`` list contains a "Shift" or "CapsLock" key.
        **Note** that the ``KeyboardKey`` with the "Shift" or "CapsLock" main key is removed from the output list.
        :param keys: A list of ``KeyboardKey`` objects
        :return: A list of ``KeyboardKey`` objects with the shift effect applied
        """

        # Check if Shift or CapsLock is active
        shift_active = any(key.main_key.lower() in {"shift", "capslock"} for key in keys)

        if shift_active:
            # Remove Shift and CapsLock keys from the list
            keys = [key for key in keys if key.main_key.lower() not in {"shift", "capslock"}]
            for key in keys:
                key.shift = True  # Apply shift effect to remaining keys

        return keys

    @retries()
    def _type(self, keys: list[KeyboardKey], delay:float):
        """
        Presses a list of Keyboard keys on the typing exercise.
        :param keys: A list of ``KeyboardKeys``
        :return:
        """
        self._typing_page.wait_for_load_state("load")
        page = self._typing_page.locator("html")
        for key in keys:
            page.press(key.key, delay=delay)

    @retries()
    def _press(self, key:KeyboardKey):
        """
        Presses a single ``KeyboardKey`` into the typing exercise.
        :param key: A single ``KeyboardKey``
        :return:
        """
        self._typing_page.wait_for_load_state("load")
        page = self._typing_page.locator("html")
        page.press(key.key)

    @retries()
    def _get_exercise_main_key(self) -> Optional[KeyboardKey]:
        """
        Returns the exercise's main key (if exists)

        The main key is the one that appears first at the beginning of every exercise.
        It looks something like this:
            "Press the key [A] on your keyboard" <- [A] is the main key.
        :return:
        """
        self._typing_page.wait_for_load_state("load")
        main_key = self._typing_page.get_by_role(TypingLessonLocators.MAIN_KEY_CONTAINER_ROLE).locator(TypingLessonLocators.KEY_LABEL)
        result:Optional[KeyboardKey] = None

        if locator_exists(main_key):
            result = KeyboardKey(main_key=main_key.inner_text(), secondary_key=None)

        return result

    @retries()
    def _is_lesson_complete(self) -> bool:
        """
        Returns ``True`` if the end of the lesson is reached.
        :return:
        """
        self._typing_page.wait_for_load_state("load")
        return locator_exists(self._typing_page.locator(TypingLessonLocators.BADGE))

    @retries()
    def _get_active_keys(self) -> Optional[list[KeyboardKey]]:
        """
        Returns the active keys on the typing keyboard if exists.
        :return:
        """
        # Locate all active keys
        self._typing_page.wait_for_load_state("load")
        active_keys = (self._typing_page.locator(TypingLessonLocators.KEYBOARD_CONTAINER)
                       .locator(TypingLessonLocators.ACTIVE_KEY))

        if not locator_exists(active_keys):
            return
        raw_keys = self._extract_key_labels(active_keys)
        if not raw_keys:
            return None

        keyboard_keys: list[KeyboardKey] = self._process_raw_keys(raw_keys)
        return self._apply_shift_effect(keyboard_keys)

    @retries()
    def _get_next_exercise_button(self) -> Optional[Locator]:
        """
        Returns the "Continue" button of the typing page if exists.
        :return:
        """
        self._typing_page.wait_for_load_state("load")
        button:Locator = self._typing_page.locator(TypingLessonLocators.NEXT_EXERCISE_BUTTON)

        if locator_exists(button):
            return button
        return None

    @retries()
    def _get_next_lesson_button(self) -> Optional[Locator]:
        """
        Returns the "Continue to next lesson" button at the end of the lesson if exists.
        :return:
        """
        button:Locator = self._typing_page.locator(TypingLessonLocators.NEXT_LESSON_BUTTON)
        if locator_exists(button):
            return button

        return None

    @retries()
    def _go_back_to_lessons(self):
        """
        Returns to the lessons dashboard.
        :return:
        """
        self._typing_page.goto(TYPING_URL)
        self._typing_page.wait_for_load_state()

    @retries
    def _get_lesson_achievement_button(self) -> Optional[Locator]:
        # TODO: This must return the goal button "Continue" when the goal screens appears
        ...

    @retries()
    def start_typing(self, delay:float):
        """
        Waits for the lesson page to load before starting to type until the end of the lesson is found.
        :raises playwright.sync_api.TimeOutError, playwright.sync_api.Error:
        :return:
        """
        # we assume that the keyboard is started on the exercise page
        self._typing_page.wait_for_load_state("load")
        exercise_page_url = self._typing_page.url
        while not self._is_lesson_complete():
            # Gets each element after every loop
            self._typing_page.wait_for_load_state("networkidle")
            next_exercise_button = self._get_next_exercise_button()
            exercise_main_key = self._get_exercise_main_key()
            exercise_active_keys = self._get_active_keys()

            # checks if the current url is the same as the exercise page.
            if self._typing_page.url != exercise_page_url:
                message = f"URL: {exercise_page_url} changed while performing an exercise."
                raise URLChangedError(message)
            if next_exercise_button:
                next_exercise_button.wait_for(timeout=30000.0)
                next_exercise_button.click(force=True)
            if exercise_main_key:
                self._press(exercise_main_key)
                self._press(KeyboardKey(main_key=_get_special_key("Enter"), secondary_key=None))
            if exercise_active_keys:
                self._type(exercise_active_keys, delay)

        self._go_back_to_lessons()
