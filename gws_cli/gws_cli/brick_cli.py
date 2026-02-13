import os
import subprocess
from typing import Annotated

import typer
from gws_core.brick.brick_service import BrickService

from gws_cli.brick_configure_service import BrickConfigureService
from gws_cli.generate_brick.generate_brick import generate_brick
from gws_cli.utils.brick_cli_service import BrickCliService
from gws_cli.utils.cli_utils import CLIUtils

app = typer.Typer(help="Generate and manage bricks - reusable components for data processing")


@app.command("generate", help="Generate a new brick with boilerplate code and structure")
def generate(
    name: Annotated[
        str, typer.Argument(help="Name of the brick to create (snake_case recommended).")
    ],
):
    generate_brick(name)


@app.command("install-deps", help="Install pip dependencies from a brick's settings.json file")
def install_deps(
    settings_path: Annotated[
        str, typer.Argument(help="Path to the settings.json file or brick directory")
    ],
):
    """Install pip dependencies from a brick's settings.json file."""

    # Convert to absolute path before searching for parent brick folder
    absolute_path = os.path.abspath(settings_path)

    # Get the parent brick folder from the provided path
    brick_folder = BrickService.get_parent_brick_folder(absolute_path)

    if not brick_folder:
        typer.echo(f"Error: {settings_path} is not inside a valid brick directory", err=True)
        raise typer.Exit(1)

    # Use BrickCliService to read settings
    settings = BrickCliService.get_brick_settings(brick_folder)

    if not settings:
        typer.echo(f"Error: Could not read settings.json from {settings_path}", err=True)
        raise typer.Exit(1)

    total_packages = settings.count_pip_packages()
    if total_packages == 0:
        typer.echo("No pip dependencies found in settings.json")
        return

    typer.echo(f"Found {total_packages} pip packages to install from {settings.name} brick")

    # Get all pip sources from settings
    pip_sources = settings.get_pip_sources()

    has_errors = False
    for source in pip_sources:
        pip_cmd = source.get_pip_install_command()
        if not pip_cmd:
            continue

        package_specs = source.get_package_specs()
        typer.echo(f"\nInstalling {len(package_specs)} packages from {source.get_source_url()}")
        typer.echo(f"Executing: {' '.join(pip_cmd)}")

        try:
            subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
            typer.echo(
                f"✓ Successfully installed {len(package_specs)} packages: {', '.join(package_specs)}"
            )
        except subprocess.CalledProcessError as e:
            has_errors = True
            typer.echo(f"✗ Failed to install packages: {e.stderr}", err=True)
            typer.echo(f"Command: {' '.join(pip_cmd)}", err=True)
        except Exception as e:
            has_errors = True
            typer.echo(f"✗ Error installing packages: {e}", err=True)

    if has_errors:
        typer.echo("\nDependency installation completed with errors", err=True)
        raise typer.Exit(1)

    typer.echo("\nDependency installation completed successfully")


@app.command("configure", help="Configure a brick with GitHub Copilot instruction files")
def configure(
    brick_path: Annotated[
        str, typer.Argument(help="Path to the brick folder. If not provided, uses the current directory.")
    ] = None,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing generated files",
    ),
):
    """Configure the current brick with GitHub Copilot instruction files in .github/."""

    if brick_path:
        absolute_path = os.path.abspath(brick_path)
        brick_dir = BrickService.get_parent_brick_folder(absolute_path)
        if not brick_dir:
            typer.echo(f"Error: {brick_path} is not inside a valid brick directory", err=True)
            raise typer.Exit(1)
    else:
        brick_dir = CLIUtils.get_and_check_current_brick_dir()

    BrickConfigureService.configure_brick(brick_dir, force=force)
