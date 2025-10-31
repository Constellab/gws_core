
import typer
from gws_cli.app_cli import AppCli
from gws_cli.generate_reflex_app.generate_reflex_app import generate_reflex_app
from gws_core.apps.reflex.reflex_app import ReflexApp
from typing_extensions import Annotated

app = typer.Typer(help="Generate and run Reflex applications")


@app.command("run", help="Run a Reflex app in development mode")
def run_dev(
    ctx: typer.Context,
    config_file_path: Annotated[str, typer.Argument(help="Path to the JSON config file for the app to run.")]
):

    app_cli = AppCli(config_file_path)
    shell_proxy = app_cli.build_shell_proxy()

    reflex_app = ReflexApp(ReflexApp.DEV_MODE_APP_ID, "main", shell_proxy)
    reflex_app.set_dev_mode(config_file_path)
    reflex_app.set_app_static_folder(app_cli.get_app_dir_path(), None)
    reflex_app.set_is_enterprise(app_cli.is_reflex_enterprise())

    app_cli.start_app(reflex_app, ctx)


@app.command("generate", help="Generate a new Reflex app")
def generate(
        name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")],
        is_enterprise: Annotated[bool, typer.Option("--enterprise", help="Generate an enterprise Reflex app.", is_flag=True)] = False):
    app_folder = generate_reflex_app(name, is_enterprise=is_enterprise)
    print(f"Reflex app '{name}' created successfully in '{app_folder}'.")


@app.command("init", help="Generate a new Reflex app (alias for generate)")
def init(
        name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")],
        is_enterprise: Annotated[bool, typer.Option("--enterprise", help="Generate an enterprise Reflex app.", is_flag=True)] = False):
    app_folder = generate_reflex_app(name, is_enterprise=is_enterprise)
    print(f"Reflex app '{name}' created successfully in '{app_folder}'.")
