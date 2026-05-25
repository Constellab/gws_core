import subprocess
from typing import Annotated

import typer

from gws_cli.code_migration.code_migration import (
    get_all_code_migrations,
    get_code_migration,
    get_code_migrations_after,
)
from gws_cli.code_migration.code_migration_runner import (
    get_brick_gws_core_version,
    run_code_migration,
)
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

technical_doc_app = typer.Typer(help="Manage brick technical documentation")
app.add_typer(technical_doc_app, name="technical-doc")


@app.command(
    "code-migrate",
    help=(
        "Apply gws_core code migrations (source-to-source refactors) to a brick. "
        "By default runs every migration newer than the gws_core version the brick targets: "
        "describes each migration, lists the impacted files, and asks one confirmation before "
        "applying to all of them. Use --dry-run to see the diffs, --yes to skip the confirmation."
    ),
)
def code_migrate(
    brick_path: Annotated[
        str | None,
        typer.Argument(
            help="Path to the brick folder. If not provided, uses the current directory."
        ),
    ] = None,
    version: Annotated[
        str | None,
        typer.Option(
            "--version",
            "-v",
            help="Run only the migration for this gws_core version (e.g. 0.22.0).",
        ),
    ] = None,
    list_migrations: Annotated[
        bool,
        typer.Option("--list", "-l", help="List the available code migrations and exit."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show the diffs without modifying any file."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Apply every change without prompting (CI use)."),
    ] = False,
):
    """Run versioned code migrations over the brick's ``src`` directory."""
    if list_migrations:
        migrations = get_all_code_migrations()
        if not migrations:
            typer.echo("No code migrations are registered.")
            return
        typer.echo("Available code migrations:")
        for migration in migrations:
            typer.echo(f"  - {migration.version}: {migration.short_description}")
        return

    brick_dir = BrickCliService.resolve_brick_dir(brick_path)
    settings = BrickCliService.get_brick_settings(brick_dir)
    if not settings:
        typer.echo(f"Error: could not read settings.json in {brick_dir}", err=True)
        raise typer.Exit(1)

    if version is not None:
        migration = get_code_migration(version)
        if migration is None:
            available = ", ".join(str(m.version) for m in get_all_code_migrations()) or "(none)"
            typer.echo(
                f"Error: no code migration registered for version '{version}'. "
                f"Available: {available}",
                err=True,
            )
            raise typer.Exit(1)
        to_run = [migration]
    else:
        current_version = get_brick_gws_core_version(settings)
        if current_version is None:
            typer.echo(
                "Could not determine the gws_core version this brick targets "
                "(no 'gws_core' dependency in settings.json). "
                "Re-run with --version <x> to pick a specific migration, or --list to see them.",
                err=True,
            )
            raise typer.Exit(1)
        to_run = get_code_migrations_after(current_version)
        if not to_run:
            typer.echo(f"Brick targets gws_core {current_version}; no newer code migration to run.")
            return
        typer.echo(
            f"Brick targets gws_core {current_version}. "
            f"Running {len(to_run)} migration(s): {', '.join(str(m.version) for m in to_run)}"
        )

    for migration in to_run:
        run_code_migration(brick_dir, migration, assume_yes=yes, dry_run=dry_run)


@technical_doc_app.command(
    "push", help="Push the technical documentation of a brick to the Constellab community"
)
def technical_doc_push(
    brick_path: Annotated[
        str | None,
        typer.Argument(
            help="Path to the brick folder. If not provided, uses the current directory."
        ),
    ] = None,
):
    """Push the technical documentation of a brick without pushing a new version."""

    brick_dir = BrickCliService.resolve_brick_dir(brick_path)

    settings = BrickCliService.get_brick_settings(brick_dir)
    if not settings:
        typer.echo("Error: Could not read brick settings", err=True)
        raise typer.Exit(1)

    typer.echo(f"Brick: {settings.name}")
    typer.echo("Pushing technical documentation...")
    try:
        BrickCliService.push_technical_doc(brick_dir)
    except Exception as e:
        typer.echo(f"Error pushing technical documentation: {e}", err=True)
        raise typer.Exit(1) from e
    typer.echo("Successfully pushed technical documentation")


def _ensure_git_tag(brick_dir: str, version: str, yes: bool) -> None:
    """Check that the git tag exists, prompting the user to create it if needed."""
    if BrickCliService.git_tag_exists(brick_dir, version):
        return

    typer.echo(f"Git tag '{version}' does not exist in the repository.")
    if not yes:
        create_tag = typer.confirm(
            f"Would you like to create the tag '{version}'?",
            default=False,
        )
        if not create_tag:
            typer.echo("Aborted. Please create the tag manually before pushing the version.")
            raise typer.Exit(1)

    push_tag = yes or typer.confirm(
        f"Push the tag '{version}' to origin?",
        default=True,
    )

    try:
        BrickCliService.create_git_tag(brick_dir, version, push=push_tag)
        typer.echo(f"Created tag '{version}'" + (" and pushed to origin" if push_tag else ""))
    except Exception as e:
        typer.echo(f"Error creating tag: {e}", err=True)
        raise typer.Exit(1) from e


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
    technical_doc: bool = typer.Option(
        False,
        "--technical-doc",
        "-td",
        help="Skip technical documentation confirmation and push it automatically",
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

    version = settings.version
    if not version:
        typer.echo("Error: Brick settings do not contain a version", err=True)
        raise typer.Exit(1)

    _ensure_git_tag(brick_dir, version, yes)

    if not yes:
        typer.confirm("Do you want to push this version?", abort=True)

    try:
        BrickCliService.create_new_brick_version(brick_dir)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Successfully pushed version {version} of brick {settings.name}")

    # Ask if the user wants to push the technical documentation
    push_doc = (
        technical_doc
        or yes
        or typer.confirm(
            "Do you also want to push the technical documentation?",
            default=False,
        )
    )

    if push_doc:
        typer.echo("Pushing technical documentation...")
        try:
            BrickCliService.push_technical_doc(brick_dir)
        except Exception as e:
            typer.echo(f"Error pushing technical documentation: {e}", err=True)
            raise typer.Exit(1) from e
        typer.echo("Successfully pushed technical documentation")
