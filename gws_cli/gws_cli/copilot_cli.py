import typer

from gws_cli.ai_code.copilot_service import CopilotService

app = typer.Typer(help="GitHub Copilot management commands")


def _manage_skills(pull: bool, list_skills: bool):
    """Shared logic for managing GitHub Copilot skills"""
    service = CopilotService()

    if pull:
        exit_code = service.pull_copilot_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    elif list_skills:
        exit_code = service.print_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        typer.echo(
            "Use --pull to copy GWS skills to global GitHub Copilot instructions folder"
        )
        typer.echo("Use --list to show all available GWS skills")
        typer.echo("Example: gws copilot skills --pull")
        typer.echo("Example: gws copilot skills --list")


@app.command("skills", help="Manage GitHub Copilot skills")
def skills(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS skills to global Copilot instructions folder"
    ),
    list_skills: bool = typer.Option(False, "--list", help="List all available GWS skills"),
):
    """Manage GitHub Copilot skills

    Use --pull to copy GWS skills to ~/.github/prompts
    Use --list to show all available GWS skills
    """
    _manage_skills(pull, list_skills)


@app.command("instructions", help="Manage GitHub Copilot instructions (alias for skills)", hidden=True)
def instructions(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS skills to global Copilot instructions folder"
    ),
    list_skills: bool = typer.Option(False, "--list", help="List all available GWS skills"),
):
    """Alias for 'skills' command for backwards compatibility"""
    _manage_skills(pull, list_skills)


@app.command("commands", help="Manage GitHub Copilot commands (alias for skills)", hidden=True)
def commands(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS skills to global Copilot instructions folder"
    ),
    list_skills: bool = typer.Option(False, "--list", help="List all available GWS skills"),
):
    """Alias for 'skills' command for backwards compatibility"""
    _manage_skills(pull, list_skills)


@app.command("update", help="Update GitHub Copilot configuration")
def update():
    """Update GitHub Copilot configuration for GWS (skills and settings)

    Only runs if GitHub Copilot is already installed. Does nothing if not installed.
    """
    service = CopilotService()
    exit_code = service.update()
    if exit_code != 0:
        raise typer.Exit(exit_code)
