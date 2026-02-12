import typer
from gws_core.manage import AppManager

from .dev_env.dev_env_cli_service import DevEnvCliService

app = typer.Typer(help="Manage development environment data and settings")


@app.command("reset", help="Reset development environment data (WARNING: irreversible)")
def reset_dev_env():
    delete = typer.confirm(
        "Are you sure you want to delete all the data of the dev environment? The production data will not be affected. This action is irreversible."
    )

    if not delete:
        typer.echo("The data was not deleted.")
        raise typer.Abort()

    AppManager.reset_environment()
    typer.echo("Development environment has been reset successfully.")


@app.command("configure", help="Configure VsCode and AI tools for development environment")
def configure(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Delete all generated files before configuring VSCode",
    ),
    configure_bricks: bool = typer.Option(
        False,
        "--configure-bricks",
        "-b",
        help="Configure user bricks with AI code instruction files (.github/)",
    ),
):
    """Configure VS Code with recommended settings, extensions, and Python paths for all bricks."""
    DevEnvCliService.configure_dev_env(force=force, configure_bricks=configure_bricks)
