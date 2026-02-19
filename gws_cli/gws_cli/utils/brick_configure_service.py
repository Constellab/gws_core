import os
import shutil

import typer

from gws_cli.ai_code.ai_code_service import AICodeService


class BrickConfigureService:
    """Service for configuring a brick with AI code instruction files."""

    BRICK_SPECIFIC_DIR = AICodeService.SOURCE_COMMANDS_DIR / "brick-specific"
    COMMANDS_DIR = AICodeService.SOURCE_COMMANDS_DIR

    # Files from brick-specific/ copied directly (no prefix)
    COPILOT_INSTRUCTIONS = "copilot-instructions.md"

    # Files from commands/ copied with gws- prefix
    COMMAND_FILES_WITH_PREFIX = [
        "code-review-instructions.md",
        "reflex-app-developer.md",
        "streamlit-app-developer.md",
    ]

    @classmethod
    def configure_brick(cls, brick_dir: str, force: bool = False) -> None:
        """Configure a brick with GitHub Copilot instruction files.

        Args:
            brick_dir: Path to the brick root directory.
            force: If True, overwrite existing files.
        """
        github_dir = os.path.join(brick_dir, ".github")

        if force and os.path.exists(github_dir):
            typer.echo("Force option enabled. Deleting existing .github directory...")
            shutil.rmtree(github_dir)

        os.makedirs(github_dir, exist_ok=True)

        # Copy copilot-instructions.md -> .github/copilot-instructions.md
        cls._copy_file(
            src=os.path.join(cls.BRICK_SPECIFIC_DIR, cls.COPILOT_INSTRUCTIONS),
            dest=os.path.join(github_dir, cls.COPILOT_INSTRUCTIONS),
            force=force,
        )

        # Copy command files with gws- prefix
        for filename in cls.COMMAND_FILES_WITH_PREFIX:
            cls._copy_file(
                src=os.path.join(cls.COMMANDS_DIR, filename),
                dest=os.path.join(github_dir, f"gws-{filename}"),
                force=force,
            )

        typer.echo("Brick configured successfully!")

    @classmethod
    def _copy_file(cls, src: str, dest: str, force: bool) -> None:
        """Copy a file from src to dest.

        Args:
            src: Source file path.
            dest: Destination file path.
            force: If True, overwrite existing files.
        """
        if not os.path.exists(src):
            typer.echo(f"Warning: Source file not found: {src}")
            return

        if os.path.exists(dest) and not force:
            typer.echo(f"Skipping (already exists): {dest}")
            return

        shutil.copyfile(src, dest)
        typer.echo(f"Copied: {dest}")
