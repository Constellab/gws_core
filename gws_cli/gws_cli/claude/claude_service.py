import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

from gws_cli.utils.node_service import NodeService


class ClaudeService:
    """Service for managing Claude Code installation and related operations"""

    @staticmethod
    def is_claude_code_installed() -> bool:
        """Check if Claude Code is installed

        Returns:
            bool: True if claude command is available, False otherwise
        """
        try:
            subprocess.run(["claude", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def install_claude_code() -> int:
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

    @staticmethod
    def install_claude_code_if_not_installed() -> int:
        """Install Claude Code only if it's not already installed

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if ClaudeService.is_claude_code_installed():
            print("Claude Code is already installed.")
            return 0

        print("Claude Code not found. Starting installation...")
        return ClaudeService.install_claude_code()

    @staticmethod
    def pull_agents() -> int:
        """Pull GWS agents to global Claude agents folder

        This command copies the agents from gws_cli/gws_cli/claude/agents to ~/.claude/agents/gws-agents,
        replacing any existing agents in that location.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Source: agents folder in the gws_cli package
            source_agents_dir = Path(__file__).parent / "agents"

            # Target: ~/.claude/agents/gws-agents
            home_dir = Path.home()
            target_base_dir = home_dir / ".claude" / "agents"
            target_agents_dir = target_base_dir / "gws-agents"

            # Validate source directory exists
            if not source_agents_dir.exists():
                print(f"Error: Source agents directory not found at {source_agents_dir}")
                return 1

            # Create ~/.claude/agents if it doesn't exist
            target_base_dir.mkdir(parents=True, exist_ok=True)

            # Remove existing gws-agents folder if it exists
            if target_agents_dir.exists():
                print(f"Removing existing agents at {target_agents_dir}")
                shutil.rmtree(target_agents_dir)

            # Copy the agents folder
            print(f"Copying agents from {source_agents_dir} to {target_agents_dir}")
            shutil.copytree(source_agents_dir, target_agents_dir)

            print("GWS agents successfully pulled to global Claude agents folder! Restart claude command to use them.")
            print(f"Location: {target_agents_dir}")
            return 0

        except Exception as e:
            print(f"Error pulling agents: {e}")
            return 1

    @staticmethod
    def init_settings() -> int:
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
            print(f"Found gws_core at: {gws_core_path}")

            # Path to settings.json
            home_dir = Path.home()
            claude_dir = home_dir / ".claude"
            settings_file = claude_dir / "settings.json"

            # Create .claude directory if it doesn't exist
            claude_dir.mkdir(parents=True, exist_ok=True)

            # Read existing settings or create empty dict
            settings = {}
            if settings_file.exists():
                print(f"Reading existing settings from {settings_file}")
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

            print(f"Successfully set GWS_CORE_SRC={gws_core_path} in Claude settings")
            return 0

        except Exception as e:
            print(f"Error initializing settings: {e}")
            return 1

    @staticmethod
    def _update_claude_config() -> int:
        """Common method to update Claude Code configuration (agents and settings)

        This helper method performs the configuration update steps:
        1. Pulls GWS agents to global Claude agents folder
        2. Updates Claude Code settings with GWS_CORE_SRC environment variable

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Pull agents
        print("Pulling GWS agents...")
        result = ClaudeService.pull_agents()
        if result != 0:
            print("Failed to pull agents")
            return result
        print()

        # Update settings
        print("Updating Claude settings...")
        result = ClaudeService.init_settings()
        if result != 0:
            print("Failed to update settings")
            return result
        print()

        return 0

    @staticmethod
    def init() -> int:
        """Initialize Claude Code environment for GWS

        This method performs the following steps:
        1. Installs Claude Code (if not already installed)
        2. Pulls GWS agents to global Claude agents folder
        3. Initializes Claude Code settings with GWS_CORE_SRC environment variable

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        print("=== Initializing Claude Code for GWS ===\n")

        # Step 1: Install Claude Code
        print("Installing Claude Code...")
        result = ClaudeService.install_claude_code_if_not_installed()
        if result != 0:
            print("Failed to install Claude Code")
            return result
        print()

        # Step 2 & 3: Update configuration
        result = ClaudeService._update_claude_config()
        if result != 0:
            return result

        print("=== Claude Code initialization completed successfully! ===")
        return 0

    @staticmethod
    def update() -> int:
        """Update Claude Code configuration for GWS

        This method performs the same steps as init() but only if Claude Code is already installed.
        If Claude Code is not installed, it does nothing and returns success.

        Steps performed (if Claude Code is installed):
        1. Pulls GWS agents to global Claude agents folder
        2. Updates Claude Code settings with GWS_CORE_SRC environment variable

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        print("=== Updating Claude Code configuration for GWS ===\n")

        # Check if Claude Code is installed
        if not ClaudeService.is_claude_code_installed():
            print("Claude Code is not installed. Nothing to update.")
            return 0

        print("Claude Code is installed. Proceeding with update...\n")

        # Update configuration
        result = ClaudeService._update_claude_config()
        if result != 0:
            return result

        print("=== Claude Code configuration updated successfully! ===")
        return 0
