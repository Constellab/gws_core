import typer
from gws_cli.claude.claude_service import ClaudeService

app = typer.Typer(help="Claude Code management commands")


@app.command("install", help="Install Claude Code")
def install():
    """Install Claude Code CLI tool (automatically installs Node.js if needed)"""
    exit_code = ClaudeService.init()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("update", help="Update Claude Code configuration")
def update():
    """Update Claude Code configuration for GWS (agents and settings)

    Only runs if Claude Code is already installed. Does nothing if not installed.
    """
    exit_code = ClaudeService.update()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("agents", help="Manage Claude Code agents")
def agents(
    pull: bool = typer.Option(False, "--pull", help="Pull GWS agents to global Claude agents folder")
):
    """Manage Claude Code agents

    Use --pull to copy GWS agents to ~/.claude/agents/gws-agents
    """
    if pull:
        exit_code = ClaudeService.pull_agents()
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        print("Use --pull to copy GWS agents to global Claude agents folder")
        print("Example: gws claude agents --pull")
