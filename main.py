import time
from pathlib import Path
from typing import Optional, Literal, Iterable, Union
from tkinter.filedialog import askopenfilename
from rich.console import Console, ScreenContext
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import playwright.sync_api
from src.core.config_loader import ConfigLoader
from src.autotyper.autotyper import Autotyper
from src.core.errors import UserNotLoggedError, URLChangedError
from src.utils.browser_utils import get_default_browser

__version__ = "0.2"

# Helper function to create a styled list
def create_list(
    iterable: Iterable,
    tabs: int = 0,
    bullet_type: int = 0,
    ordered: bool = False,
    bullet_style: str = "bold blue",
    number_style: str = "bold green",
) -> Text:
    bullets = ["•", "○", "⁃", "‣"]  # Bullets for unordered lists
    bullet = bullets[bullet_type % len(bullets)]
    base_text = Text()

    for index, item in enumerate(iterable, start=1):
        if isinstance(item, Iterable) and not isinstance(item, (str, Text)):
            base_text.append(
                create_list(item, tabs + 1, bullet_type + 1, ordered, bullet_style, number_style)
            )
            continue

        marker = Text(f"{index}. " if ordered else f"{bullet} ", style=number_style if ordered else bullet_style)
        base_text.append(Text("\t" * tabs))
        base_text.append(marker)
        base_text.append(Text(f"{item}\n"))

    return base_text[:-1]

# Helper function to display options and get user input
def option_picker(
    console: Console,
    options: list[str],
    prompt_message: Union[Text, str] = "select >",
    title: Optional[str] = None,
    title_align: Literal["left", "center", "right"] = "center",
    bullet_style: str = "bold blue",
) -> tuple[int, int]:
    console.print(
        Panel(
            create_list(options, ordered=True, number_style=bullet_style),
            title=title,
            title_align=title_align,
        )
    )
    choices = [str(i + 1) for i in range(len(options))]
    user_answer = int(Prompt.ask(prompt=prompt_message, choices=choices, console=console))
    return len(options), user_answer

# Display lessons menu
def display_lessons(screen: ScreenContext, typer: Autotyper):
    while True:
        screen.update()
        categories_options = typer.categories + ["Back"]

        category_count, category_choice = option_picker(
            console=screen.console,
            options=categories_options,
            title="Categories",
        )
        if category_choice == category_count:
            break

        selected_category = typer.categories[category_choice - 1]
        with screen.console.status(f"Loading lessons from category: {selected_category}"):
            lessons = typer.get_lessons(selected_category)

        while True:
            screen.update()
            lessons_options = [lesson.title for lesson in lessons] + ["Back"]

            lesson_count, lesson_choice = option_picker(
                console=screen.console,
                options=lessons_options,
                title=selected_category,
            )
            if lesson_choice == lesson_count:
                break

            lesson_indices = Prompt.ask(
                "Enter lesson numbers (comma-separated, e.g., 1,2,3) or a single number",
                default=str(lesson_choice),
            )
            lesson_indices = [int(idx.strip()) - 1 for idx in lesson_indices.split(",") if idx.strip().isdigit()]

            for lesson_index in lesson_indices:
                if 0 <= lesson_index < len(lessons):
                    try:
                        screen.update()
                        with screen.console.status(f"Starting lesson: {lessons[lesson_index].title}"):
                            lessons[lesson_index].start()
                    except playwright.sync_api.Error:
                        screen.console.print(
                            "[bold red]An error occurred while doing a lesson. Browser or tab might have been closed."
                        )
                    except URLChangedError:
                        screen.console.print(
                            "[bold red]An error occurred while doing a lesson. URL changed mid-exercise."
                        )
                    except playwright.sync_api.TimeoutError:
                        screen.console.print(
                            "[bold red]Timeout reached. Check your internet connection and try again."
                        )

# Display settings menu
def display_settings(screen: ScreenContext, settings: ConfigLoader.ConfigFile, typer: Autotyper):
    while True:
        screen.update()
        options = [
            f"Typing delay: {Text(str(settings.typing_delay), style='blue')}ms",
            f"Browser path: {Text(str(settings.browser_path), style='blue')}",
            "Reset to defaults",
            "Back",
        ]
        option_count, option_choice = option_picker(
            console=screen.console, options=options, title="Settings - Select an option to update"
        )

        match option_choice:
            case 1:
                delay = Prompt.ask("Typing delay (in ms, leave empty to skip)")
                if delay.strip():
                    settings.typing_delay = float(delay)
                    typer.typing_delay = float(delay)

            case 2:
                browser_executable_path = askopenfilename(
                    title="Select browser executable",
                    defaultextension="*.exe",
                    initialdir=Path.home(),
                    filetypes=[("Executable files", "*.exe")],
                )
                if browser_executable_path:
                    settings.browser_path = browser_executable_path
                    screen.console.print("[bold yellow]Restart the program to use the new browser.")

            case 3:
                settings = ConfigLoader.ConfigFile()

            case 4:
                break

    ConfigLoader.update(settings)
    screen.console.print("[bold green]Settings saved.")

# Main function
def main():
    config = ConfigLoader.load()
    console = Console()
    console.set_window_title("Autotyper")
    typer = Autotyper()
    running = True

    while running:
        with console.screen() as screen:
            screen.update()
            option_count, option_choice = option_picker(
                console=console,
                options=["Connect", "Start Lesson(s)", "Settings", "Exit"],
                title=f"Autotyper v{__version__}",
            )

            match option_choice:
                case 1:
                    try:
                        with console.status("Opening browser and connecting..."):
                            typer.start(config.browser_path or get_default_browser(), config.typing_delay)
                    except UserNotLoggedError:
                        console.print("[bold yellow]Please log in and try again.")
                    except playwright.sync_api.TimeoutError:
                        console.print(
                            "[bold yellow]Connection error. Try closing the browser and not reopening it."
                        )
                    except playwright.sync_api.Error:
                        console.print(
                            "[bold red]Unexpected error during connection. Try restarting the browser."
                        )

                case 2:
                    display_lessons(screen, typer)

                case 3:
                    display_settings(screen, config, typer)

                case 4:
                    screen.update()
                    console.print("[yellow]Closing...")
                    running = False

    with console.status("Closing connection..."):
        typer.close()

if __name__ == "__main__":
    main()
