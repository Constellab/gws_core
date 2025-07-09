
import typer
from typing_extensions import Annotated

from gws_cli.app_cli import AppCli
from gws_cli.generate_reflex_app.generate_reflex_app import generate_reflex_app
from gws_core.apps.reflex.reflex_app import ReflexApp

app = typer.Typer(help="Generate and run Reflex applications")


@app.command("run-dev", help="Run a Reflex app in development mode")
def run_dev(config_file_path: Annotated[str, typer.Argument(help="Path to the JSON config file for the app to run.")]):

    app_cli = AppCli(config_file_path)
    shell_proxy = app_cli.build_shell_proxy()

    streamit_app = ReflexApp("main", "main", shell_proxy)
    streamit_app.set_dev_mode(config_file_path)
    streamit_app.set_app_folder(app_cli.get_app_dir_path())

    app_cli.start_app(streamit_app)


@app.command("generate", help="Generate a new Reflex app")
def generate(
        name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")]):
    app_folder = generate_reflex_app(name)
    print(f"Reflex app '{name}' created successfully in '{app_folder}'.")


@app.command("init", help="Generate a new Reflex app (alias for generate)")
def init(
        name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")]):
    app_folder = generate_reflex_app(name)
    print(f"Reflex app '{name}' created successfully in '{app_folder}'.")
