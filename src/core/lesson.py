from enum import Enum
from typing import Optional

from src.core.constants import TypingLocators
from src.core.typing_keyboard import TypingKeyboard
from playwright.sync_api import Page, Locator

from src.utils.browser_utils import locator_exists


class LessonState(Enum):
    BLOCKED = 0
    ACTIVE = 1
    COMPLETE = 2
    UNKNOWN = 3

class ExerciseState(Enum):
    INCOMPLETE = 0
    COMPLETE = 1

class LessonExercise:
    def __init__(self, exercise_box:Locator, lesson_title:str):
        self._lesson_title:str = lesson_title
        self._exercise_box:Locator = exercise_box
        self._state:ExerciseState = self._get_exercise_state(exercise_box)
        self._index:int = int(exercise_box.get_attribute("data-display-order"))

    def start(self):
        print("Clicked exercise box")
        self._exercise_box.click()

    @property
    def lesson_title(self) -> str:
        return self._lesson_title

    @property
    def state(self) -> ExerciseState:
        return self._state

    @property
    def index(self) -> int:
        return self._index

    @staticmethod
    def _get_exercise_state(exercise_box:Locator):
        exercise_state = exercise_box.get_attribute("class").split()
        result = ExerciseState.INCOMPLETE

        if "is-complete" in exercise_state:
            result = ExerciseState.COMPLETE

        return result

    def __repr__(self):
        return f"exercise of lesson: [{self._lesson_title}] -> index: [{self._index}], state: [{self._state.name}]"

class Lesson:
    def __init__(self,category:str, lesson_container:Locator, typing_page:Page):
        """
        Represents a single lesson from the typing website.
        :param category: The lesson category (beginner, intermediate, advance,...)
        :param lesson_container: The div containing the lesson data
        :param typing_page: The Page class containing the typing website.
        """
        self._typing_page:Page = typing_page
        self._category:str = category
        self._title:str = lesson_container.locator(TypingLocators.LESSON_TITLE).inner_text()
        # check if the button exists (Premium lessons might not show the button if the user is on a free plan)
        button = lesson_container.locator(TypingLocators.LESSON_BUTTON)
        self._button:Optional[Locator] = button if locator_exists(button) else None
        self._lesson_state:LessonState = self._get_button_state(self._button)
        self._exercises = [LessonExercise(exercise_box, self.title) for exercise_box in
                           lesson_container.locator("div.chunks div").all()]

        self._keyboard = TypingKeyboard(self._typing_page)

    def __repr__(self):
        button_id = self._button.get_attribute('data-id') if self._button else "Unknown"
        return f"{self.category} -> {self.title} state: [{self._lesson_state.name}], button id: [{button_id}]"

    @staticmethod
    def _get_button_state(button:Locator) -> LessonState:
        if not button:
            return LessonState.UNKNOWN

        result = LessonState.UNKNOWN
        button_state = button.get_attribute("class").split()
        if "btn--c" in button_state:
            result = LessonState.COMPLETE
        if "btn--a" in button_state:
            result = LessonState.ACTIVE
        if "btn--b" in button_state:
            result = LessonState.BLOCKED

        return result

    def start(self):
        self._button.click()
        self._keyboard.start_typing()

    def start_from_exercise(self, number:int):
        exercise = self._exercises[number - 1]
        if exercise.state.value != ExerciseState.COMPLETE.value:
            raise IndexError(f"The Lesson exercise must be Completed to start from it. Lesson title [{exercise.lesson_title}], exercise number: [{exercise.index}]")

        self._typing_page.wait_for_load_state()
        self._exercises[number - 1].start()
        self._keyboard.start_typing()

    @property
    def state(self) -> LessonState:
        return self._lesson_state

    @property
    def category(self) -> str:
        return self._category

    @property
    def exercises(self) -> int:
        return len(self._exercises)

    @property
    def completed_exercises(self) -> int:
        total = 0
        for exercise in self._exercises:
            if exercise.state == exercise.state.COMPLETE:
                total +=1

        return total

    @property
    def title(self) -> str:
        return self._title


