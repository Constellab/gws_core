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
    """Update Claude Code configuration for GWS (skills and settings)

    Only runs if Claude Code is already installed. Does nothing if not installed.
    """
    service = ClaudeService()
    exit_code = service.update()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("skills", help="Manage Claude Code skills")
def skills(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS skills to Claude plugin folder"
    ),
    list_skills: bool = typer.Option(False, "--list", help="List all available GWS skills"),
):
    """Manage Claude Code skills

    Use --pull to copy GWS skills to ~/.claude/plugins/gws-commands
    Use --list to show all available GWS skills
    """
    service = ClaudeService()

    if pull:
        exit_code = service.pull_claude_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    elif list_skills:
        exit_code = service.print_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        typer.echo("Use --pull to copy GWS skills to Claude plugin folder")
        typer.echo("Use --list to show all available GWS skills")
        typer.echo("Example: gws claude skills --pull")
        typer.echo("Example: gws claude skills --list")


@app.command("commands", help="Manage Claude Code commands (alias for skills)", hidden=True)
def commands(
    pull: bool = typer.Option(
        False, "--pull", help="Pull GWS skills to Claude plugin folder"
    ),
    list_skills: bool = typer.Option(False, "--list", help="List all available GWS skills"),
):
    """Alias for 'skills' command for backwards compatibility"""
    service = ClaudeService()

    if pull:
        exit_code = service.pull_claude_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    elif list_skills:
        exit_code = service.print_skills()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        typer.echo("Use --pull to copy GWS skills to Claude plugin folder")
        typer.echo("Use --list to show all available GWS skills")
        typer.echo("Example: gws claude skills --pull")
        typer.echo("Example: gws claude skills --list")


@app.command("statusline", help="Configure Claude Code statusline")
def statusline():
    """Configure Claude Code statusline at user level so it applies in any project."""
    exit_code = StatuslineService.configure()
    if exit_code != 0:
        raise typer.Exit(exit_code)
