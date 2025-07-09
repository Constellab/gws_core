
import typer
from typing_extensions import Annotated

from gws_cli.generate_brick.generate_brick import generate_brick

app = typer.Typer(help="Generate and manage bricks - reusable components for data processing")


@app.command("generate", help="Generate a new brick with boilerplate code and structure")
def generate(name: Annotated[str, typer.Argument(help="Name of the brick to create (snake_case recommended).")]):
    print(f"Creating brick: '{name}'")
    generate_brick(name)
    print(f"Brick '{name}' created successfully")
