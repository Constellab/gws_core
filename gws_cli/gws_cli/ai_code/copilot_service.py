import os
from pathlib import Path

import typer
from gws_core.core.utils.settings import Settings

from gws_cli.ai_code.ai_code_service import AICodeService, SkillFrontmatter


class CopilotService(AICodeService):
    """Service for managing GitHub Copilot skills"""

    def __init__(self):
        """Initialize CopilotService"""
        super().__init__(ai_tool_name="GitHub Copilot")

    def format_frontmatter(self, frontmatter: SkillFrontmatter) -> str:
        """Format frontmatter for GitHub Copilot skills

        Args:
            frontmatter: The frontmatter configuration to format

        Returns:
            Frontmatter with name and description
        """
        skill_name = self.get_skill_dir_name(frontmatter.filename)
        return f"""---
name: {skill_name}
description: {frontmatter.description}
---

"""

    def get_target_dir(self) -> Path:
        """Get the base directory for GitHub Copilot skills

        Returns:
            Path to ~/.copilot/skills
        """
        return Path(os.path.join(Path.home(), ".copilot", "skills"))

    def get_skill_dir_name(self, base_filename: str) -> str:
        """Get the skill directory name for GitHub Copilot

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
            Glob pattern for GitHub Copilot skill files
        """
        return "gws-*/SKILL.md"

    def get_install_command(self) -> str:
        """Get the command to install/pull skills for GitHub Copilot

        Returns:
            Command string to pull Copilot skills
        """
        return "gws copilot update"

    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to ~/.github/copilot-instructions.md
        """
        return Path(os.path.join(Settings.get_user_folder(), ".github", "copilot-instructions.md"))

    def _write_skill_file(self, target_dir: Path, skill_name: str, content: str) -> None:
        """Write a skill as a directory with SKILL.md inside

        Args:
            target_dir: The skills directory
            skill_name: The skill directory name (e.g., 'gws-task-expert')
            content: The skill content with frontmatter
        """
        skill_dir = target_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")

    def is_configured(self) -> bool:
        """Check if GitHub Copilot is configured (new skills or legacy prompts exist)

        Returns:
            bool: True if configured, False otherwise
        """
        # Check for new skills
        if super().is_configured():
            return True

        # Check for legacy prompts directory
        legacy_dir = Path(os.path.join(Settings.get_user_folder(), ".github", "prompts"))
        return legacy_dir.exists() and any(legacy_dir.glob("gws-*.prompt.md"))

    def _cleanup_legacy_prompts(self) -> None:
        """Remove old legacy prompt files (~/.github/prompts/gws-*.prompt.md) if they exist"""
        legacy_dir = Path(os.path.join(Settings.get_user_folder(), ".github", "prompts"))
        if not legacy_dir.exists():
            return

        for legacy_file in legacy_dir.glob("gws-*.prompt.md"):
            if legacy_file.is_file():
                legacy_file.unlink()
                typer.echo(f"Removed legacy prompt file: {legacy_file}")

    def update(self) -> int:
        """Update GitHub Copilot configuration for GWS

        This method performs the following steps:
        1. Removes legacy prompt files if they exist
        2. Pulls GWS skills to ~/.copilot/skills/
        3. Generates main instructions file

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        typer.echo("=== Updating GitHub Copilot configuration for GWS ===\n")

        # Clean up old legacy prompts
        self._cleanup_legacy_prompts()

        # Pull skills
        result = self.pull_skills_to_global()
        if result != 0:
            typer.echo("Failed to pull skills", err=True)
            return result

        # Generate main instructions
        result = self.generate_main_instructions()
        if result != 0:
            typer.echo("Failed to generate main instructions", err=True)
            return result

        typer.echo("\n=== GitHub Copilot configuration updated successfully! ===")
        self._log_post_installation_instructions()
        return 0

    def pull_copilot_skills(self) -> int:
        """Pull GWS skills to GitHub Copilot skills folder and display usage instructions

        This method wraps pull_skills_to_global() and provides helpful information about
        how to use the installed skills in GitHub Copilot.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        result = self.pull_skills_to_global()

        if result == 0:
            self._log_post_installation_instructions()

        return result

    def _log_post_installation_instructions(self):
        """Log instructions for using GitHub Copilot with GWS skills"""
        typer.echo("\n" + "=" * 70)
        typer.echo("How to use GWS skills in GitHub Copilot:")
        typer.echo("=" * 70)
        typer.echo("\n1. Open GitHub Copilot Chat in your editor (VS Code, JetBrains, etc.)")
        typer.echo(
            "\n2. GWS skills are automatically loaded by Copilot when relevant to your task."
        )
        typer.echo("   You can also reference them explicitly in your prompts.")
        typer.echo("\n" + "=" * 70)
