import typer

from gws_cli.ai_code.claude.statusline.configure_statusline import StatuslineService
from gws_cli.ai_code.claude_service import ClaudeService

app = typer.Typer(help="Claude Code management commands")


@app.command("install", help="Install Claude Code")
def install():
    """Install Claude Code CLI tool (automatically installs Node.js if needed)"""
    service = ClaudeService()
    exit_code = service.init()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("update", help="Update Claude Code configuration")
def update():
    """Update Claude Code configuration for GWS (commands and settings)

    Only runs if Claude Code is already installed. Does nothing if not installed.
    """
    service = ClaudeService()
    exit_code = service.update()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("commands", help="Manage Claude Code commands")
def commands(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS commands to global Claude commands folder"
    ),
    list_commands: bool = typer.Option(False, "--list", help="List all available GWS commands"),
):
    """Manage Claude Code commands

    Use --pull to copy GWS commands to ~/.claude/commands/gws-commands
    Use --list to show all available GWS commands
    """
    service = ClaudeService()

    if pull:
        exit_code = service.pull_claude_commands()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    elif list_commands:
        exit_code = service.print_commands()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        typer.echo("Use --pull to copy GWS commands to global Claude commands folder")
        typer.echo("Use --list to show all available GWS commands")
        typer.echo("Example: gws claude commands --pull")
        typer.echo("Example: gws claude commands --list")


@app.command("statusline", help="Configure Claude Code statusline")
def statusline():
    """Configure Claude Code statusline at user level so it applies in any project."""
    exit_code = StatuslineService.configure()
    if exit_code != 0:
        raise typer.Exit(exit_code)
