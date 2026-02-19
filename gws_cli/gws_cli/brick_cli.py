import subprocess
from typing import Annotated

import typer

from gws_cli.generate_brick.generate_brick import generate_brick
from gws_cli.utils.brick_cli_service import BrickCliService
from gws_cli.utils.brick_configure_service import BrickConfigureService

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
    brick_path: Annotated[
        str | None,
        typer.Argument(
            help="Path to the brick folder. If not provided, uses the current directory."
        ),
    ] = None,
):
    """Install pip dependencies from a brick's settings.json file."""

    brick_dir = BrickCliService.resolve_brick_dir(brick_path)

    # Use BrickCliService to read settings
    settings = BrickCliService.get_brick_settings(brick_dir)

    if not settings:
        typer.echo(f"Error: Could not read settings.json from {brick_dir}", err=True)
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
        str | None,
        typer.Argument(
            help="Path to the brick folder. If not provided, uses the current directory."
        ),
    ] = None,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing generated files",
    ),
):
    """Configure a brick with GitHub Copilot instruction files in .github/."""

    brick_dir = BrickCliService.resolve_brick_dir(brick_path)
    BrickConfigureService.configure_brick(brick_dir, force=force)


version_app = typer.Typer(help="Manage brick versions")
app.add_typer(version_app, name="version")


@version_app.command("push", help="Push a new brick version to the Constellab community")
def version_push(
    brick_path: Annotated[
        str | None,
        typer.Argument(
            help="Path to the brick folder. If not provided, uses the current directory."
        ),
    ] = None,
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """Read the brick settings, verify a matching git tag exists, and publish the version."""

    brick_dir = BrickCliService.resolve_brick_dir(brick_path)

    settings = BrickCliService.get_brick_settings(brick_dir)
    if not settings:
        typer.echo("Error: Could not read brick settings", err=True)
        raise typer.Exit(1)

    typer.echo(f"Brick: {settings.name}")
    typer.echo(f"Version: {settings.version}")

    # Check if git tag exists before proceeding
    version = settings.version
    if not version:
        typer.echo("Error: Brick settings do not contain a version", err=True)
        raise typer.Exit(1)

    if not BrickCliService.git_tag_exists(brick_dir, version):
        typer.echo(f"Git tag '{version}' does not exist in the repository.")
        create_tag = typer.confirm(
            f"Would you like to create the tag '{version}'?",
            default=False,
        )
        if not create_tag:
            typer.echo("Aborted. Please create the tag manually before pushing the version.")
            raise typer.Exit(1)

        push_tag = typer.confirm(
            f"Push the tag '{version}' to origin?",
            default=True,
        )

        try:
            BrickCliService.create_git_tag(brick_dir, version, push=push_tag)
            typer.echo(f"Created tag '{version}'" + (" and pushed to origin" if push_tag else ""))
        except Exception as e:
            typer.echo(f"Error creating tag: {e}", err=True)
            raise typer.Exit(1) from e

    if not yes:
        typer.confirm("Do you want to push this version?", abort=True)

    try:
        result = BrickCliService.create_new_brick_version(brick_dir)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Successfully pushed version {result.version} of brick {result.name}")
