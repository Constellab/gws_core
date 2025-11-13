import typer
from gws_cli.ai_code.copilot_service import CopilotService

app = typer.Typer(help="GitHub Copilot management commands")


def _manage_instructions(pull: bool, list_commands: bool):
    """Shared logic for managing GitHub Copilot instructions"""
    service = CopilotService()

    if pull:
        exit_code = service.pull_copilot_commands()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    elif list_commands:
        exit_code = service.list_commands()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        print("Use --pull to copy GWS instructions to global GitHub Copilot instructions folder")
        print("Use --list to show all available GWS commands")
        print("Example: gws copilot instructions --pull")
        print("Example: gws copilot instructions --list")
        print("Example: gws copilot commands --pull")
        print("Example: gws copilot commands --list")


@app.command("instructions", help="Manage GitHub Copilot instructions")
def instructions(
    pull: bool = typer.Option(False, "--pull", help="Pull GWS instructions to global Copilot instructions folder"),
    list_commands: bool = typer.Option(False, "--list", help="List all available GWS commands")
):
    """Manage GitHub Copilot instructions

    Use --pull to copy GWS instructions to ~/.github/copilot/instructions/gws-instructions
    Use --list to show all available GWS commands
    """
    _manage_instructions(pull, list_commands)


@app.command("update", help="Update GitHub Copilot configuration")
def update():
    """Update GitHub Copilot configuration for GWS (instructions and settings)

    Only runs if GitHub Copilot is already installed. Does nothing if not installed.
    """
    service = CopilotService()
    exit_code = service.update()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("commands", help="Manage GitHub Copilot commands (alias for instructions)")
def commands(
    pull: bool = typer.Option(False, "--pull", help="Pull GWS commands to global Copilot instructions folder"),
    list_commands: bool = typer.Option(False, "--list", help="List all available GWS commands")
):
    """Manage GitHub Copilot commands (alias for instructions)

    Use --pull to copy GWS commands to ~/.github/copilot/instructions/gws-instructions
    Use --list to show all available GWS commands
    """
    _manage_instructions(pull, list_commands)
