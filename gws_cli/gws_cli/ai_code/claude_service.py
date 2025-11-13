import importlib.util
import json
import os
import subprocess
from pathlib import Path

from gws_cli.ai_code.ai_code_service import AICodeService, CommandFrontmatter
from gws_cli.utils.node_service import NodeService
from gws_core.core.utils.settings import Settings


class ClaudeService(AICodeService):
    """Service for managing Claude Code installation and related operations"""

    def __init__(self):
        """Initialize ClaudeService"""
        super().__init__(
            ai_tool_name="Claude Code"
        )

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
        return 'gws-*.md'

    def get_install_command(self) -> str:
        """Get the command to install/pull commands for Claude Code

        Returns:
            Command string to initialize Claude Code
        """
        return 'gws claude update'

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
        """Install Claude Code CLI tool (automatically installs Node.js if needed)

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # First, check if Node.js is available
        if not NodeService.is_node_installed():
            print("Node.js not found. Installing Node.js first...")
            node_result = NodeService.install_node()
            if node_result != 0:
                return node_result

        script_dir = Path(__file__).parent.parent / "scripts"
        script_path = script_dir / "install-claude-code.sh"

        if not script_path.exists():
            print(f"Error: Install script not found at {script_path}")
            return 1

        print("Starting Claude Code installation...")

        try:
            # Execute the bash script
            result = subprocess.run(["bash", str(script_path)], check=True, capture_output=False)

            if result.returncode == 0:
                print("Claude Code installation completed successfully!")
                return 0
            else:
                print("Claude Code installation failed!")
                return 1

        except subprocess.CalledProcessError as e:
            print(f"Error during Claude Code installation: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1

    def install_claude_code_if_not_installed(self) -> int:
        """Install Claude Code only if it's not already installed

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if self.is_claude_code_installed():
            print("Claude Code is already installed.")
            return 0

        print("Claude Code not found. Starting installation...")
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
                print("Error: gws_core package not found")
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
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            else:
                print(f"Creating new settings file at {settings_file}")

            # Ensure env key exists
            if "env" not in settings:
                settings["env"] = {}

            # Set GWS_CORE_SRC
            settings["env"]["GWS_CORE_SRC"] = str(gws_core_path)

            # Write settings back
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            return 0

        except Exception as e:
            print(f"Error initializing settings: {e}")
            return 1

    def _update_claude_config(self) -> int:
        """Common method to update Claude Code configuration (commands and settings)

        This helper method performs the configuration update steps:
        1. Pulls GWS commands to global Claude commands folder
        2. Updates Claude Code settings with GWS_CORE_SRC environment variable
        3. Generates main instructions file

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Pull commands
        result = self.pull_commands_to_global()
        if result != 0:
            print("Failed to pull commands")
            return result

        # Update settings
        result = self.init_settings()
        if result != 0:
            print("Failed to update settings")
            return result

        # Generate main instructions
        result = self.generate_main_instructions()
        if result != 0:
            print("Failed to generate main instructions")
            return result

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
        print("=== Initializing Claude Code for GWS ===\n")

        # Step 1: Install Claude Code
        print("Installing Claude Code...")
        result = self.install_claude_code_if_not_installed()
        if result != 0:
            print("Failed to install Claude Code")
            return result
        print()

        # Step 2 & 3: Update configuration
        result = self._update_claude_config()
        if result != 0:
            return result

        print("=== Claude Code initialization completed successfully! ===")
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
        print("=== Updating Claude Code configuration for GWS ===\n")

        # Check if Claude Code is installed
        if not self.is_claude_code_installed():
            print("Claude Code is not installed. Nothing to update.")
            return 0

        print("Claude Code is installed. Proceeding with update...\n")

        # Update configuration
        result = self._update_claude_config()
        if result != 0:
            return result

        print("=== Claude Code configuration updated successfully! ===")
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
        print("\n" + "=" * 70)
        print("How to use GWS commands in Claude Code:")
        print("=" * 70)
        print("\n1. Open Claude Code in your terminal or editor")
        print("\n2. Use the / symbol to invoke GWS slash commands followed by your task description.")
        print("   Example: /gws-streamlit-app-developer Create a data visualization dashboard")
        print("\n" + "=" * 70)
