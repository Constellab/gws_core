import subprocess

import typer
from gws_cli.generate_brick.generate_brick import generate_brick
from gws_cli.utils.brick_cli_service import BrickCliService
from gws_core.brick.brick_service import BrickService
from typing_extensions import Annotated

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

    if not BrickService.folder_is_brick(settings_path):
        typer.echo(
            f"Error: {settings_path} is not a valid brick directory or settings.json file", err=True
        )
        raise typer.Exit(1)

    # Use BrickCliService to read settings
    settings = BrickCliService.get_brick_settings(settings_path)

    if not settings:
        typer.echo(f"Error: Could not read settings.json from {settings_path}", err=True)
        raise typer.Exit(1)

    # Extract pip sources from settings DTO
    if not settings.environment or not settings.environment.pip:
        typer.echo("No pip dependencies found in settings.json")
        return

    pip_sources = settings.environment.pip

    total_packages = sum(len(source.packages) if source.packages else 0 for source in pip_sources)
    if total_packages == 0:
        typer.echo("No pip packages found in settings.json")
        return

    typer.echo(f"Found {total_packages} pip packages to install from {settings.name} brick")
    _install_packages_from_settings(pip_sources)
    typer.echo("\nDependency installation completed")


def _install_packages_from_settings(pip_sources) -> None:
    """Install packages from all pip sources from BrickSettingsDTO."""
    for source in pip_sources:
        source_url = source.source if source.source else "https://pypi.python.org/simple"
        packages = source.packages

        if not packages:
            continue

        typer.echo(f"\nInstalling {len(packages)} packages from {source_url}")
        _install_packages_batch(packages, source_url)


def _install_packages_batch(packages, source_url: str) -> None:
    """Install all packages from a specific source in a single command."""
    package_specs = []

    for package in packages:
        if not package.name:
            typer.echo("Warning: Package with no name found, skipping")
            continue

        package_spec = f"{package.name}=={package.version}" if package.version else package.name
        package_specs.append(package_spec)

    if not package_specs:
        typer.echo("No valid packages found to install")
        return

    pip_cmd = ["pip", "install", "-i", source_url] + package_specs
    typer.echo(f"Executing: {' '.join(pip_cmd)}")

    try:
        subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
        typer.echo(
            f"✓ Successfully installed {len(package_specs)} packages: {', '.join(package_specs)}"
        )
    except subprocess.CalledProcessError as e:
        typer.echo(f"✗ Failed to install packages: {e.stderr}", err=True)
        typer.echo(f"Command: {' '.join(pip_cmd)}", err=True)
    except Exception as e:
        typer.echo(f"✗ Error installing packages: {e}", err=True)
