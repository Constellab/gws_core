from typing import Annotated

import typer

from gws_cli.generate_task.generate_task import generate_task

app = typer.Typer(help="Generate task classes for data processing workflows")


@app.command("generate", help="Generate a new task class with boilerplate code")
def generate(
    name: Annotated[str, typer.Argument(help="Name of the task class to create (PascalCase).")],
    human_name: Annotated[
        str, typer.Option("--human-name", help="Human-readable name of the task.")
    ]
    | None = None,
    short_description: Annotated[
        str, typer.Option("--short-description", help="Short description of what the task does.")
    ]
    | None = None,
):
    typer.echo(f"Creating task: '{name}'")
    task_file = generate_task(name, human_name=human_name, short_description=short_description)
    typer.echo(f"Task '{name}' created successfully in '{task_file}'.")
