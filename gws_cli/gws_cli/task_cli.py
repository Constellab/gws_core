
import typer
from typing_extensions import Annotated

from gws_cli.create_task.create_task import create_task

app = typer.Typer()


@app.command("generate")
def generate(
        name: Annotated[str, typer.Argument(help="Name of the task class to create (Pascal case).")],
        human_name: Annotated[str, typer.Option("--human-name", help="Human name of the task.")] = None,
        short_description:
        Annotated[str, typer.Option("--short-description", help="Short description of the task.")] = None):
    print(f"Creating task: '{name}'")
    task_file = create_task(name, human_name=human_name, short_description=short_description)
    print(f"Task '{name}' created successfully in '{task_file}'.")
