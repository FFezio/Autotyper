import time
from importlib.metadata import metadata
from pathlib import Path
from typing import Optional, Literal
from tkinter.filedialog import askopenfilename
import playwright.sync_api
from rich.console import Console, ScreenContext
from rich.panel import Panel
from rich.prompt import Prompt
from src.core.config_loader import ConfigLoader
from src.autotyper.autotyper import Autotyper
from src.core.errors import UserNotLoggedError, URLChangedError
from src.utils.browser_utils import get_default_browser
from rich.text import Text
from typing import Iterable, Union

__version__ = "0.1"

def create_list(
        iterable: Iterable,
        tabs: int = 0,
        bullet_type: int = 0,
        ordered: bool = False,
        bullet_style: str = "bold blue",
        number_style: str = "bold green"
    ) -> Text:
    """
    Creates list from an iterable object
    :param iterable: The iterable object
    :param tabs: The number of tabs to make before each bullet point
    :param bullet_type: The type of bullet
    :param ordered: If true the list will be ordered (unordered by default)
    :param bullet_style: The style of unordered bullets
    :param number_style: The style of ordered bullets
    :return:
    """
    bullets = ["•", "○", "⁃", "‣"]  # Bullets for unordered lists
    selected_bullet_index = bullet_type if bullet_type < len(bullets) else 0
    base_text = Text()

    for index, item in enumerate(iterable, start=1):
        if isinstance(item, Iterable) and not isinstance(item, (str, Text)):  # Avoid treating strings as iterables
            base_text.append(
                create_list(item, tabs + 1, selected_bullet_index + 1, ordered, bullet_style, number_style)
            )
            continue
        if ordered:
            marker = Text(f"{index}. ", style=number_style)
        else:
            marker = Text(f"{bullets[selected_bullet_index]} ", style=bullet_style)

        # Add indentation, marker (bullet/number), and content
        base_text.append(Text("\t" * tabs))  # Add indentation
        base_text.append(marker)  # Add marker (bullet/number)
        base_text.append(Text(f"{item}\n"))  # Add content (un styled)
    return base_text[:-1]

def option_picker(
        console:Console,
        options:Iterable[str],
        prompt_message:Union[Text, str]="select >",
        title:Optional[str]=None, title_align:Literal["left", "center", "right"]="center",
        bullet_style:str="bold blue"
    ) -> tuple[int, int]:
    """
    Creates a list of options and prompts the user to select one.
    Returns a ``tuple`` with the following values: (options_count, user_answer)

    **Note** The returned option is indexed at position ``1``
    :param console: The console that will be used to print and prompt to the user.
    :param options: A list of options to pick from
    :param prompt_message: The message that will be prompted to the user. Default to ``select >``
    :param title: The title of the panel
    :param title_align: The alignment of the panel title
    :param bullet_style: The style of the bullet.
    :return:
    """
    console.print(
        Panel(
            create_list(
                iterable=options,
                ordered=True,
                number_style=bullet_style
            ),
            title=title,
            title_align=title_align
        )
    )
    choices = [str(index[0]+1) for index in enumerate(options)]
    choices_count = int(choices[-1])
    user_answer = int(Prompt.ask(prompt=prompt_message, choices=choices, console=console))
    return choices_count, user_answer


def display_lessons(screen:ScreenContext, typer:Autotyper):
    while True:
        screen.update()
        categories_options = typer.categories
        categories_options.append("Back")

        option = option_picker(
            console=screen.console,
            options=categories_options,
            title="Categories"
        )
        if option[1] == option[0]:
            break
        selected_category = typer.categories[option[1] - 1]
        with screen.console.status(f"Loading lessons from category: {selected_category}"):
            lessons = typer.get_lessons(selected_category)

        while True:
            screen.update()
            lessons_options = [lesson.title for lesson in lessons]
            lessons_options.append("Back")
            selected_lesson = option_picker(
                screen.console,
                lessons_options,
                title=selected_category
            )

            if selected_lesson[0] == selected_lesson[1]:
                break
            lesson_index = selected_lesson[1] - 1
            screen.update()

            try:
                with screen.console.status(f"doing lesson: {lessons[lesson_index].title}"):
                    lessons[lesson_index].start()
            except playwright.sync_api.Error:
                screen.console.print("[bold red]An error occurred while doing a lesson, browser or tab were probably closed.")
                screen.console.input("press enter to continue")
            except URLChangedError:
                screen.console.print("[bold red]An error occurred while doing a lesson, url was changed in the middle of an exercise")
                screen.console.input("press enter to continue")
            except playwright.sync_api.TimeoutError:
                screen.console.print("[bold red]Time out reached while doing a lesson, check your internet connection and try again.")

def display_settings(screen: ScreenContext, settings: ConfigLoader.ConfigFile, typer:Autotyper):
    while True:
        screen.update()
        option = option_picker(
            console=screen.console,
            options=[
                f"typing delay: {Text(str(settings.typing_delay), style='blue')}ms",
                f"browser path: {Text(str(settings.browser_path), style='blue')}",
                "reset to defaults",
                "Back"
            ],
            title="Settings - select an option to update"
        )

        match option[1]:
            case 1:
                screen.update()
                delay = float(Prompt.ask("typing delay (left empty to ignore)"))
                if delay:
                    settings.typing_delay = delay
                    typer.typing_delay = delay
            case 2:
                screen.update()
                browser_executable_path = askopenfilename(
                    title="autotyper - search browser executable",
                    defaultextension="*.exe",
                    initialdir=Path.home(),
                    filetypes=[("Executable files", "*.exe")]
                )
                if not browser_executable_path:
                    continue
                else:
                    settings.browser_path = browser_executable_path
                    screen.console.print("[bold yellow] Restart the program to launch with the new browser")
                    screen.console.input("Press enter to continue")

            case 3:
                settings = ConfigLoader.ConfigFile()
            case 4:
                break
    screen.console.print("[bold green] saving...")
    time.sleep(1)
    ConfigLoader.update(settings)

def main():
    config = ConfigLoader.load()
    console = Console()
    console.set_window_title("Autotyper")
    typer = Autotyper()
    running = True
    while running:
        with console.screen() as screen:
            screen.update()
            option = option_picker(
                console=console,
                options=[
                    "Connect",
                    "Start Lesson(s)",
                    "Settings",
                    "Exit"
                ],
                title=f"Autotyper v{__version__}"
            )
            match option[1]:
                case 1:
                    try:
                        with console.status("Opening browser & connecting."):
                            typer.start(config.browser_path or get_default_browser(), config.typing_delay)
                    except UserNotLoggedError:
                        console.print("[bold yellow]Please login and try again")
                        console.input("press enter to continue")
                    except playwright.sync_api.TimeoutError:
                        console.print("[bold yellow]There was an error while connecting to the browser, try closing it (and don't open it back).")
                        console.input("press enter to continue")
                    except playwright.sync_api.Error:
                        console.print("[bold red]An unexpected error occurred while connecting to the browser. if this keep occurring try closing the browser (and don't open it back).")
                        console.input("press enter to continue")
                case 2:
                    display_lessons(screen, typer)
                    time.sleep(2)
                case 3:
                    display_settings(screen, config, typer)
                case 4:
                    screen.update()
                    console.print("[yellow] closing...")
                    running = False
    with console.status("Closing connection"):
        typer.close()

if __name__ == '__main__':
    main()
