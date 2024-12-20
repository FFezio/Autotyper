from dataclasses import dataclass

SPECIAL_KEYS = {
    "": "Space",
    "␣": "Space",
    "⏎": "Enter",
    "⇧": "Shift",
    "⇪": "CapsLock",
    "↹": "Tab",
    "⌫": "BackSpace"
}
TYPING_URL = "https://www.typing.com/student/lessons"

@dataclass()
class GoogleLoginLocators:
    EMAIL_INPUT = "input[type='email']"
    PASSWORD_INPUT = "input[type='password']"
    LOGIN_BUTTON = "button.btn--google"
    ACCOUNTS_LIST_CONTAINER = "ul li"
    ACCOUNTS_LIST = "[data-email]"


@dataclass()
class TypingLocators:
    LOGIN_BUTTON_CONTAINER = ".list--hero .list-item"
    LOGIN_BUTTON = "li a[href='/student/login']"
    TAB_LIST_CONTAINER = "tablist"
    TAB_LIST = "tab"
    LESSON_CONTAINER = "div.lesson"
    LESSON_TITLE = "p.lesson-title"
    LESSON_BUTTON = "a.lesson-btn"
    LESSON_EXERCISES_CONTAINER = "div.chunks"
    LESSON_EXERCISE = "div.lesson-chunk"
    CARD_SURVEY_CONTAINER = "form[class='survey'] div.card--survey"
    ACHIEVEMENT_CONTAINER = ".growl-achievementOuterWrap"
    CONTAINERS_CLOSE_BUTTON = ".js-close"


class TypingLessonLocators:
    NEXT_EXERCISE_BUTTON = "button.js-continue-button"
    NEXT_LESSON_BUTTON = "a.js-continue.btn"
    MAIN_KEY_CONTAINER_ROLE = "alert"
    KEY_LABEL = ".key-label"
    ACTIVE_KEY = "div.keyboard-key.is-active"
    KEYBOARD_CONTAINER = "div.js-keyboard-holder"
    BADGE = ".badge"