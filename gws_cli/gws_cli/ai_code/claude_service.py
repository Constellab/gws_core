import importlib.util
import json
import os
import subprocess
from pathlib import Path

import typer
from gws_core.core.utils.settings import Settings

from gws_cli.ai_code.ai_code_service import AICodeService, CommandFrontmatter


class ClaudeService(AICodeService):
    """Service for managing Claude Code installation and related operations"""

    MCP_SCRIPT_PATH = Path(__file__).parent / ".." / "mcp" / "rag_mcp.py"
    MCP_NAME = "gws-mcp"

    def __init__(self):
        """Initialize ClaudeService"""
        super().__init__(ai_tool_name="Claude Code")

    def format_frontmatter(self, frontmatter: CommandFrontmatter) -> str:
        """Format frontmatter for Claude Code

        Args:
            frontmatter: The frontmatter configuration to format

        Returns:
            Frontmatter with description and argument-hint
        """
        return f"""---
description: {frontmatter.description}
argument-hint: [{frontmatter.argument_hint}]
---

"""

    def get_target_dir(self) -> Path:
        """Get the base directory for Claude Code commands

        Returns:
            Path to ~/.claude/commands/gws-commands
        """
        return Path(os.path.join(Path.home(), ".claude", "commands", "gws-commands"))

    def format_filename(self, base_filename: str) -> str:
        """Format the filename for Claude Code

        Args:
            base_filename: The base filename (e.g., 'streamlit-app-developer.md')

        Returns:
            The same filename (Claude uses .md files)
        """
        return base_filename

    def get_file_pattern(self) -> str:
        """Get the glob pattern to match command files in the target directory

        Returns:
            Glob pattern for Claude Code command files
        """
        return "gws-*.md"

    def get_install_command(self) -> str:
        """Get the command to install/pull commands for Claude Code

        Returns:
            Command string to initialize Claude Code
        """
        return "gws claude update"

    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to ~/CLAUDE.md
        """
        return Path(os.path.join(Settings.get_user_folder(), "CLAUDE.md"))

    def is_claude_code_installed(self) -> bool:
        """Check if Claude Code is installed

        Returns:
            bool: True if claude command is available, False otherwise
        """
        try:
            subprocess.run(["claude", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_claude_code(self) -> int:
        """Install Claude Code CLI tool using the official installer

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        script_dir = Path(__file__).parent.parent / "scripts"
        script_path = script_dir / "install-claude-code.sh"

        if not script_path.exists():
            typer.echo(f"Error: Install script not found at {script_path}", err=True)
            return 1

        typer.echo("Starting Claude Code installation...")

        try:
            # Execute the bash script
            result = subprocess.run(["bash", str(script_path)], check=True, capture_output=False)

            if result.returncode == 0:
                typer.echo("Claude Code installation completed successfully!")
                return 0
            else:
                typer.echo("Claude Code installation failed!", err=True)
                return 1

        except subprocess.CalledProcessError as e:
            typer.echo(f"Error during Claude Code installation: {e}", err=True)
            return 1
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            return 1

    def install_claude_code_if_not_installed(self) -> int:
        """Install Claude Code only if it's not already installed

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if self.is_claude_code_installed():
            typer.echo("Claude Code is already installed.")
            return 0

        typer.echo("Claude Code not found. Starting installation...")
        return self.install_claude_code()

    def init_settings(self) -> int:
        """Initialize Claude Code settings with GWS_CORE_SRC environment variable

        This method retrieves the path of the gws_core Python package and sets the
        GWS_CORE_SRC environment variable in ~/.claude/settings.json.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Find the gws_core package path
            gws_core_spec = importlib.util.find_spec("gws_core")
            if gws_core_spec is None or gws_core_spec.origin is None:
                typer.echo("Error: gws_core package not found", err=True)
                return 1

            # Get the source directory (parent of the __init__.py file)
            gws_core_path = Path(gws_core_spec.origin).parent

            # Path to settings.json
            home_dir = Path.home()
            claude_dir = home_dir / ".claude"
            settings_file = claude_dir / "settings.json"

            # Create .claude directory if it doesn't exist
            claude_dir.mkdir(parents=True, exist_ok=True)

            # Read existing settings or create empty dict
            settings = {}
            if settings_file.exists():
                with open(settings_file) as f:
                    settings = json.load(f)
            else:
                typer.echo(f"Creating new settings file at {settings_file}")

            # Ensure env key exists
            if "env" not in settings:
                settings["env"] = {}

            # Set GWS_CORE_SRC
            settings["env"]["GWS_CORE_SRC"] = str(gws_core_path)

            # Write settings back
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)

            return 0

        except Exception as e:
            typer.echo(f"Error initializing settings: {e}", err=True)
            return 1

    def configure_mcp(self) -> int:
        """Configure the gws-mcp MCP server for Claude Code

        This method adds (or refreshes) the gws-mcp MCP server by running
        the claude mcp add command. If the MCP server already exists, it is
        removed first to ensure a fresh configuration.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        mcp_script = self.MCP_SCRIPT_PATH.resolve()

        if not mcp_script.exists():
            typer.echo(f"Error: MCP script not found at {mcp_script}", err=True)
            return 1

        try:
            # Check if the MCP server already exists
            result = subprocess.run(
                ["claude", "mcp", "get", self.MCP_NAME],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # MCP server exists, remove it first
                typer.echo(f"Removing existing MCP server '{self.MCP_NAME}'...")
                subprocess.run(
                    ["claude", "mcp", "remove", "--scope", "user", self.MCP_NAME],
                    check=True,
                    capture_output=True,
                )

            # Add the MCP server at user level so it's available in all projects
            typer.echo(f"Adding MCP server '{self.MCP_NAME}'...")
            subprocess.run(
                [
                    "claude",
                    "mcp",
                    "add",
                    "--scope",
                    "user",
                    self.MCP_NAME,
                    "--",
                    "python",
                    str(mcp_script),
                ],
                check=True,
                capture_output=True,
            )

            typer.echo(f"MCP server '{self.MCP_NAME}' configured successfully.")
            return 0

        except subprocess.CalledProcessError as e:
            typer.echo(f"Error configuring MCP server: {e}", err=True)
            return 1
        except Exception as e:
            typer.echo(f"Unexpected error configuring MCP server: {e}", err=True)
            return 1

    def _update_claude_config(self) -> int:
        """Common method to update Claude Code configuration (commands and settings)

        This helper method performs the configuration update steps:
        1. Pulls GWS commands to global Claude commands folder
        2. Updates Claude Code settings with GWS_CORE_SRC environment variable
        3. Generates main instructions file
        4. Configures gws-mcp MCP server

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Pull commands
        result = self.pull_commands_to_global()
        if result != 0:
            typer.echo("Failed to pull commands", err=True)
            return result

        # Update settings
        result = self.init_settings()
        if result != 0:
            typer.echo("Failed to update settings", err=True)
            return result

        # Generate main instructions
        result = self.generate_main_instructions()
        if result != 0:
            typer.echo("Failed to generate main instructions", err=True)
            return result

        # Configure MCP server
        # result = self.configure_mcp()
        # if result != 0:
        #     typer.echo("Failed to configure MCP server", err=True)
        #     return result

        return 0

    def init(self) -> int:
        """Initialize Claude Code environment for GWS

        This method performs the following steps:
        1. Installs Claude Code (if not already installed)
        2. Pulls GWS commands to global Claude commands folder
        3. Initializes Claude Code settings with GWS_CORE_SRC environment variable

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        typer.echo("=== Initializing Claude Code for GWS ===\n")

        # Step 1: Install Claude Code
        typer.echo("Installing Claude Code...")
        result = self.install_claude_code_if_not_installed()
        if result != 0:
            typer.echo("Failed to install Claude Code", err=True)
            return result
        typer.echo()

        # Step 2 & 3: Update configuration
        result = self._update_claude_config()
        if result != 0:
            return result

        typer.echo("=== Claude Code initialization completed successfully! ===")
        self._log_post_installation_instructions()
        return 0

    def update(self) -> int:
        """Update Claude Code configuration for GWS

        This method performs the same steps as init() but only if Claude Code is already installed.
        If Claude Code is not installed, it does nothing and returns success.

        Steps performed (if Claude Code is installed):
        1. Pulls GWS commands to global Claude commands folder
        2. Updates Claude Code settings with GWS_CORE_SRC environment variable

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        typer.echo("=== Updating Claude Code configuration for GWS ===\n")

        # Check if Claude Code is installed
        if not self.is_claude_code_installed():
            typer.echo(
                "Claude Code is not installed. Nothing to update. Run 'gws claude install' to install."
            )
            return 0

        typer.echo("Claude Code is installed. Proceeding with update...\n")

        # Update configuration
        result = self._update_claude_config()
        if result != 0:
            return result

        typer.echo("=== Claude Code configuration updated successfully! ===")
        self._log_post_installation_instructions()
        return 0

    def pull_claude_commands(self) -> int:
        """Pull GWS commands to global Claude Code commands folder and display usage instructions

        This method wraps pull_commands_to_global() and provides helpful information about
        how to use the installed commands in Claude Code.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Call the base method to pull commands
        result = self.pull_commands_to_global()

        if result == 0:
            self._log_post_installation_instructions()

        return result

    def _log_post_installation_instructions(self):
        """Log instructions for installing Claude Code manually if needed"""
        typer.echo("\n" + "=" * 70)
        typer.echo("How to use GWS commands in Claude Code:")
        typer.echo("=" * 70)
        typer.echo("\n1. Open Claude Code in your terminal or editor")
        typer.echo(
            "\n2. Use the / symbol to invoke GWS slash commands followed by your task description."
        )
        typer.echo("   Example: /gws-streamlit-app-developer Create a data visualization dashboard")
        typer.echo("\n" + "=" * 70)
