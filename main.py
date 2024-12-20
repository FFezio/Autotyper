from pprint import pprint
import src.utils.logutil
from src.core.autotyper import Autotyper

pprint("Autotyper CLI (Press enter to skip entering your personal data)")

email = input("enter your email -> ")
password = input("enter your password ->")


typer = Autotyper()
typer.start(email or "", password or "")
pprint("Select a category")

# displays the categories
for index, lesson in enumerate(typer.categories):
    pprint(f"[{index}] - {lesson}")

category_index = int(input("Select a category -> "))
lessons = typer.get_lessons(typer.categories[category_index])

# displays the lessons
for index, lesson in enumerate(lessons):
    pprint(f"[{index + 1}] - {lesson}")

lesson_index = int(input("Select a lesson -> "))
lessons[lesson_index].start()