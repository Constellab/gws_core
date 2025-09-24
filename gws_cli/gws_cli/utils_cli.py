import os
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Utility commands for development environment setup")


@app.command("install-node", help="Install Node.js via NVM")
def install_node():
    """Install Node.js using NVM (Node Version Manager)"""
    script_dir = Path(__file__).parent / "scripts"
    script_path = script_dir / "install-node.sh"

    if not script_path.exists():
        typer.echo(f"Error: Install script not found at {script_path}", err=True)
        raise typer.Exit(1)

    typer.echo("Starting Node.js installation...")

    try:
        # Execute the bash script
        result = subprocess.run(["bash", str(script_path)], check=True, capture_output=False)

        if result.returncode == 0:
            typer.echo("Node.js installation completed successfully!")
        else:
            typer.echo("Node.js installation failed!", err=True)
            raise typer.Exit(1)

    except subprocess.CalledProcessError as e:
        typer.echo(f"Error during Node.js installation: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command("install-claude-code", help="Install Claude Code (requires Node.js)")
def install_claude_code():
    """Install Claude Code CLI tool (automatically installs Node.js if needed)"""

    # First, check if Node.js is available
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        typer.echo("Node.js not found. Installing Node.js first...")
        install_node()

    script_dir = Path(__file__).parent / "scripts"
    script_path = script_dir / "install-claude-code.sh"

    if not script_path.exists():
        typer.echo(f"Error: Install script not found at {script_path}", err=True)
        raise typer.Exit(1)

    typer.echo("Starting Claude Code installation...")

    try:
        # Execute the bash script
        result = subprocess.run(["bash", str(script_path)], check=True, capture_output=False)

        if result.returncode == 0:
            typer.echo("Claude Code installation completed successfully!")
        else:
            typer.echo("Claude Code installation failed!", err=True)
            raise typer.Exit(1)

    except subprocess.CalledProcessError as e:
        typer.echo(f"Error during Claude Code installation: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)
