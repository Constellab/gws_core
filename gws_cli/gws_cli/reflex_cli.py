from enum import Enum
from typing import Annotated

import typer
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.apps.reflex.reflex_process import ReflexProcess

from gws_cli.app_cli import AppCli
from gws_cli.generate_reflex_app.generate_reflex_app import generate_reflex_app

app = typer.Typer(help="Generate and run Reflex applications")


class ReflexEnvType(str, Enum):
    """Virtual environment types supported when generating a Reflex app."""

    NONE = "NONE"
    PIP = "PIP"
    CONDA = "CONDA"
    MAMBA = "MAMBA"


@app.command("run", help="Run a Reflex app in development mode")
def run_dev(
    ctx: typer.Context,
    config_file_path: Annotated[
        str, typer.Argument(help="Path to the JSON config file for the app to run.")
    ],
):
    app_cli = AppCli(config_file_path)
    shell_proxy = app_cli.build_shell_proxy()

    reflex_app = ReflexApp(ReflexProcess.DEV_MODE_APP_ID, "main", shell_proxy)
    reflex_app.set_dev_mode()
    reflex_app.set_app_static_folder(app_cli.get_app_dir_path(), None)
    reflex_app.set_is_enterprise(app_cli.is_reflex_enterprise())

    app_cli.start_app(reflex_app, ctx)


def _generate(name: str, is_enterprise: bool, env: "ReflexEnvType") -> None:
    """Shared implementation for the ``generate`` and ``init`` commands."""
    app_folder = generate_reflex_app(name, is_enterprise=is_enterprise, env_type=env.value)
    if env != ReflexEnvType.NONE:
        typer.echo(f"App configured to run in a '{env.value}' virtual environment.")
    typer.echo(f"Reflex app '{name}' created successfully in '{app_folder}'.")


@app.command("generate", help="Generate a new Reflex app")
def generate(
    name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")],
    is_enterprise: Annotated[
        bool, typer.Option("--enterprise", help="Generate an enterprise Reflex app.", is_flag=True)
    ] = False,
    env: Annotated[
        ReflexEnvType,
        typer.Option(
            "--env",
            help="Virtual environment to run the app in (PIP for pipenv, CONDA or MAMBA).",
            case_sensitive=False,
        ),
    ] = ReflexEnvType.NONE,
):
    _generate(name, is_enterprise, env)


@app.command("init", help="Generate a new Reflex app (alias for generate)")
def init(
    name: Annotated[str, typer.Argument(help="Name of the Reflex app (snake_case).")],
    is_enterprise: Annotated[
        bool, typer.Option("--enterprise", help="Generate an enterprise Reflex app.", is_flag=True)
    ] = False,
    env: Annotated[
        ReflexEnvType,
        typer.Option(
            "--env",
            help="Virtual environment to run the app in (PIP for pipenv, CONDA or MAMBA).",
            case_sensitive=False,
        ),
    ] = ReflexEnvType.NONE,
):
    _generate(name, is_enterprise, env)
