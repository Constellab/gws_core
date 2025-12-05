import os
from pathlib import Path

from gws_core.core.utils.settings import Settings

from gws_cli.ai_code.ai_code_service import AICodeService, CommandFrontmatter


class CopilotService(AICodeService):
    """Service for managing GitHub Copilot instructions"""

    def __init__(self):
        """Initialize CopilotService"""
        super().__init__(ai_tool_name="GitHub Copilot")

    def format_frontmatter(self, frontmatter: CommandFrontmatter) -> str:
        """Format frontmatter for GitHub Copilot

        Args:
            frontmatter: The frontmatter configuration to format

        Returns:
            Frontmatter with agent, description, and argument-hint
        """
        return f"""---
agent: agent
description: {frontmatter.description}
argument-hint: {frontmatter.argument_hint}
---

"""

    def get_target_dir(self) -> Path:
        """Get the base directory for GitHub Copilot instructions

        Returns:
            Path to ~/.github/prompts
        """
        return Path(os.path.join(Settings.get_user_folder(), ".github", "prompts"))

    def format_filename(self, base_filename: str) -> str:
        """Format the filename for GitHub Copilot

        Args:
            base_filename: The base filename (e.g., 'streamlit-app-developer.md')

        Returns:
            Filename with .prompt.md extension (e.g., 'streamlit-app-developer.prompt.md')
        """
        # Remove .md extension and add .prompt.md
        if base_filename.endswith(".md"):
            base_name = base_filename[:-3]  # Remove '.md'
            return f"{base_name}.prompt.md"
        return f"{base_filename}.prompt"

    def get_file_pattern(self) -> str:
        """Get the glob pattern to match command files in the target directory

        Returns:
            Glob pattern for GitHub Copilot prompt files
        """
        return "gws-*.prompt.md"

    def get_install_command(self) -> str:
        """Get the command to install/pull commands for GitHub Copilot

        Returns:
            Command string to pull Copilot commands
        """
        return "gws copilot pull"

    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to ~/.github/copilot-instructions.md
        """
        return Path(os.path.join(Settings.get_user_folder(), ".github", "copilot-instructions.md"))

    def update(self) -> int:
        """Update GitHub Copilot configuration for GWS

        This method performs the following steps:
        1. Pulls GWS commands to global GitHub Copilot prompts folder
        2. Generates main instructions file

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        print("=== Updating GitHub Copilot configuration for GWS ===\n")

        # Pull commands
        result = self.pull_commands_to_global()
        if result != 0:
            print("Failed to pull commands")
            return result

        # Generate main instructions
        result = self.generate_main_instructions()
        if result != 0:
            print("Failed to generate main instructions")
            return result

        print("\n=== GitHub Copilot configuration updated successfully! ===")
        self._log_post_installation_instructions()
        return 0

    def pull_copilot_commands(self) -> int:
        """Pull GWS commands to global GitHub Copilot prompts folder and display usage instructions

        This method wraps pull_commands_to_global() and provides helpful information about
        how to use the installed commands in GitHub Copilot.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Call the base method to pull commands
        result = self.pull_commands_to_global()

        if result == 0:
            self._log_post_installation_instructions()

        return result

    def _log_post_installation_instructions(self):
        """Log instructions for using GitHub Copilot with GWS commands"""
        print("\n" + "=" * 70)
        print("How to use GWS commands in GitHub Copilot:")
        print("=" * 70)
        print("\n1. Open GitHub Copilot Chat in your editor (VS Code, JetBrains, etc.)")
        print("\n2. Use the / symbol to reference GWS prompts followed by your task description.")
        print("   Exemple: /gws-streamlit-app-developer Create a data visualization dashboard")
        print("\n" + "=" * 70)
