
import json
import subprocess
from pathlib import Path

import typer
from typing_extensions import Annotated

from gws_cli.generate_brick.generate_brick import generate_brick

app = typer.Typer(help="Generate and manage bricks - reusable components for data processing")


@app.command("generate", help="Generate a new brick with boilerplate code and structure")
def generate(name: Annotated[str, typer.Argument(help="Name of the brick to create (snake_case recommended).")]):
    print(f"Creating brick: '{name}'")
    generate_brick(name)
    print(f"Brick '{name}' created successfully")


@app.command("install-deps", help="Install pip dependencies from a brick's settings.json file")
def install_deps(settings_path: Annotated[str, typer.Argument(help="Path to the settings.json file")]):
    """Install pip dependencies from a brick's settings.json file."""
    settings_file = Path(settings_path)

    if not settings_file.exists():
        typer.echo(f"Error: settings.json file not found at {settings_path}", err=True)
        raise typer.Exit(1)

    if not settings_file.is_file():
        typer.echo(f"Error: {settings_path} is not a file", err=True)
        raise typer.Exit(1)

    settings_data = _load_settings_file(settings_file)
    pip_sources = _extract_pip_sources(settings_data)

    if not pip_sources:
        typer.echo("No pip dependencies found in settings.json")
        return

    total_packages = _count_total_packages(pip_sources)
    if total_packages == 0:
        typer.echo("No pip packages found in settings.json")
        return

    typer.echo(f"Found {total_packages} pip packages to install")
    _install_packages_from_sources(pip_sources)
    typer.echo("\nDependency installation completed")


def _load_settings_file(settings_file: Path) -> dict:
    """Load and parse the settings.json file."""
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in settings.json: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error reading settings.json: {e}", err=True)
        raise typer.Exit(1) from e


def _extract_pip_sources(settings_data: dict) -> list:
    """Extract pip sources from settings data."""
    environment = settings_data.get('environment', {})
    return environment.get('pip', [])


def _count_total_packages(pip_sources: list) -> int:
    """Count total packages across all sources."""
    return sum(len(source.get('packages', [])) for source in pip_sources)


def _install_packages_from_sources(pip_sources: list) -> None:
    """Install packages from all pip sources."""
    for source in pip_sources:
        source_url = source.get('source', 'https://pypi.python.org/simple')
        packages = source.get('packages', [])

        if not packages:
            continue

        typer.echo(f"\nInstalling {len(packages)} packages from {source_url}")
        _install_packages_batch(packages, source_url)


def _install_packages_batch(packages: list, source_url: str) -> None:
    """Install all packages from a specific source in a single command."""
    package_specs = []
    
    for package in packages:
        name = package.get('name')
        if not name:
            typer.echo("Warning: Package with no name found, skipping")
            continue

        version = package.get('version')
        package_spec = f"{name}=={version}" if version else name
        package_specs.append(package_spec)

    if not package_specs:
        typer.echo("No valid packages found to install")
        return

    pip_cmd = ["pip", "install", "-i", source_url] + package_specs
    typer.echo(f"Executing: {' '.join(pip_cmd)}")

    try:
        subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
        typer.echo(f"✓ Successfully installed {len(package_specs)} packages: {', '.join(package_specs)}")
    except subprocess.CalledProcessError as e:
        typer.echo(f"✗ Failed to install packages: {e.stderr}", err=True)
        typer.echo(f"Command: {' '.join(pip_cmd)}", err=True)
    except Exception as e:
        typer.echo(f"✗ Error installing packages: {e}", err=True)
