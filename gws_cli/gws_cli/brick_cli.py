
import typer
from typing_extensions import Annotated

from gws_cli.generate_brick.generate_brick import generate_brick

app = typer.Typer()


@app.command("generate")
def generate(name: Annotated[str, typer.Argument(help="Name of the brick to create.")]):
    print(f"Creating brick: '{name}'")
    generate_brick(name)
    print(f"Brick '{name}' created successfully")
