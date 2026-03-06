import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import typer
from gws_core.core.utils.settings import Settings

from gws_cli.ai_code.ai_code_service import AICodeService, SkillFrontmatter


class ClaudeService(AICodeService):
    """Service for managing Claude Code installation and related operations"""

    MCP_DIR = Path(__file__).parent / ".." / "mcp"

    # List of MCP servers to configure: (name, script filename)
    MCP_SERVERS: list[tuple[str, str]] = [
        # ("gws-mcp", "rag_mcp.py"),
        ("rich-text-editor", "rich_text_mcp.py"),
    ]

    def __init__(self):
        """Initialize ClaudeService"""
        super().__init__(ai_tool_name="Claude Code")

    def format_frontmatter(self, frontmatter: SkillFrontmatter) -> str:
        """Format frontmatter for Claude Code skills

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
        """Get the plugin root directory for Claude Code skills

        Returns:
            Path to ~/.claude/plugins/gws-commands
        """
        return Path(os.path.join(Path.home(), ".claude", "plugins", "gws-commands"))

    def get_skill_dir_name(self, base_filename: str) -> str:
        """Get the skill directory name for Claude Code

        Args:
            base_filename: The base filename (e.g., 'streamlit-app-developer.md')

        Returns:
            The skill directory name with gws- prefix (e.g., 'gws-streamlit-app-developer')
        """
        if base_filename.endswith(".md"):
            return f"gws-{base_filename[:-3]}"
        return f"gws-{base_filename}"

    def get_skill_pattern(self) -> str:
        """Get the glob pattern to match skill files in the target directory

        Returns:
            Glob pattern for Claude Code skill files
        """
        return "skills/gws-*/SKILL.md"

    def get_install_command(self) -> str:
        """Get the command to install/pull skills for Claude Code

        Returns:
            Command string to update Claude Code
        """
        return "gws claude update"

    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to ~/CLAUDE.md
        """
        return Path(os.path.join(Settings.get_user_folder(), "CLAUDE.md"))

    def _generate_plugin_manifest(self, target_dir: Path) -> None:
        """Generate the .claude-plugin/plugin.json manifest

        Args:
            target_dir: The plugin root directory
        """
        plugin_dir = target_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": self.PLUGIN_NAME,
            "description": self.PLUGIN_DESCRIPTION,
            "version": self.PLUGIN_VERSION,
        }

        manifest_path = plugin_dir / "plugin.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _write_skill_file(self, target_dir: Path, skill_name: str, content: str) -> None:
        """Write a skill as a directory with SKILL.md inside

        Args:
            target_dir: The plugin root directory
            skill_name: The skill directory name (e.g., 'gws-task-expert')
            content: The skill content with frontmatter
        """
        skill_dir = target_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")

    def is_configured(self) -> bool:
        """Check if Claude Code is configured (new plugin skills or legacy commands exist)

        Returns:
            bool: True if configured, False otherwise
        """
        # Check for new plugin skills
        if super().is_configured():
            return True

        # Check for legacy commands directory
        legacy_dir = Path(os.path.join(Path.home(), ".claude", "commands", "gws-commands"))
        return legacy_dir.exists() and any(legacy_dir.glob("gws-*"))

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
        and register the GWS plugin

        This method retrieves the path of the gws_core Python package and sets the
        GWS_CORE_SRC environment variable in ~/.claude/settings.json. It also
        registers the gws-commands plugin.

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

            # Register the gws-commands plugin
            plugin_dir = str(self.get_target_dir())
            if "enabledPlugins" not in settings:
                settings["enabledPlugins"] = []

            if plugin_dir not in settings["enabledPlugins"]:
                settings["enabledPlugins"].append(plugin_dir)

            # Write settings back
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)

            return 0

        except Exception as e:
            typer.echo(f"Error initializing settings: {e}", err=True)
            return 1

    def _configure_single_mcp(self, mcp_name: str, script_filename: str) -> int:
        """Configure a single MCP server for Claude Code.

        Adds (or refreshes) the MCP server by running the claude mcp add command.
        If the server already exists, it is removed first.

        Args:
            mcp_name: The MCP server name (e.g. 'rich-text-editor')
            script_filename: The script filename inside the mcp/ directory

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        mcp_script = (self.MCP_DIR / script_filename).resolve()

        if not mcp_script.exists():
            typer.echo(f"Error: MCP script not found at {mcp_script}", err=True)
            return 1

        try:
            # Check if the MCP server already exists
            result = subprocess.run(
                ["claude", "mcp", "get", mcp_name],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                typer.echo(f"Removing existing MCP server '{mcp_name}'...")
                subprocess.run(
                    ["claude", "mcp", "remove", "--scope", "user", mcp_name],
                    check=True,
                    capture_output=True,
                )

            typer.echo(f"Adding MCP server '{mcp_name}'...")
            subprocess.run(
                ["claude", "mcp", "add", "--scope", "user", mcp_name, "--", "python", str(mcp_script)],
                check=True,
                capture_output=True,
            )

            typer.echo(f"MCP server '{mcp_name}' configured successfully.")
            return 0

        except subprocess.CalledProcessError as e:
            typer.echo(f"Error configuring MCP server '{mcp_name}': {e}", err=True)
            return 1
        except Exception as e:
            typer.echo(f"Unexpected error configuring MCP server '{mcp_name}': {e}", err=True)
            return 1

    def configure_mcp_servers(self) -> int:
        """Configure all MCP servers listed in MCP_SERVERS.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        for mcp_name, script_filename in self.MCP_SERVERS:
            result = self._configure_single_mcp(mcp_name, script_filename)
            if result != 0:
                return result
        return 0

    def _cleanup_legacy_commands(self) -> None:
        """Remove old legacy commands directory (~/.claude/commands/gws-commands/) if it exists"""
        legacy_dir = Path(os.path.join(Path.home(), ".claude", "commands", "gws-commands"))
        if legacy_dir.exists() and legacy_dir.is_dir():
            shutil.rmtree(legacy_dir)
            typer.echo(f"Removed legacy commands directory: {legacy_dir}")

    def _update_claude_config(self) -> int:
        """Common method to update Claude Code configuration (skills and settings)

        This helper method performs the configuration update steps:
        1. Removes legacy commands directory if it exists
        2. Pulls GWS skills to global Claude plugin folder
        3. Updates Claude Code settings with GWS_CORE_SRC environment variable and plugin registration
        4. Generates main instructions file
        5. Configures MCP servers

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Clean up old legacy commands
        self._cleanup_legacy_commands()

        # Pull skills
        result = self.pull_skills_to_global()
        if result != 0:
            typer.echo("Failed to pull skills", err=True)
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

        # Configure MCP servers
        result = self.configure_mcp_servers()
        if result != 0:
            typer.echo("Failed to configure MCP servers", err=True)
            return result

        return 0

    def init(self) -> int:
        """Initialize Claude Code environment for GWS

        This method performs the following steps:
        1. Installs Claude Code (if not already installed)
        2. Pulls GWS skills to global Claude plugin folder
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
        1. Pulls GWS skills to global Claude plugin folder
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

    def pull_claude_skills(self) -> int:
        """Pull GWS skills to global Claude Code plugin folder and display usage instructions

        This method wraps pull_skills_to_global() and provides helpful information about
        how to use the installed skills in Claude Code.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Call the base method to pull skills
        result = self.pull_skills_to_global()

        if result == 0:
            self._log_post_installation_instructions()

        return result

    def _log_post_installation_instructions(self):
        """Log instructions for using GWS skills in Claude Code"""
        typer.echo("\n" + "=" * 70)
        typer.echo("How to use GWS skills in Claude Code:")
        typer.echo("=" * 70)
        typer.echo("\n1. Open Claude Code in your terminal or editor")
        typer.echo(
            "\n2. Use the / symbol to invoke GWS skills followed by your task description."
        )
        typer.echo("   Example: /gws-commands:gws-streamlit-app-developer Create a data visualization dashboard")
        typer.echo("\n" + "=" * 70)
