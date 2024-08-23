
import typer
from gws_cli.generate_brick.create_brick import create_brick
from typing_extensions import Annotated

app = typer.Typer()


@app.command("generate")
def generate(name: Annotated[str, typer.Argument(help="Name of the brick to create.")]):
    print(f"Creating brick: '{name}'")
    create_brick(name)
    print(f"Brick '{name}' created successfully")
