"""Service for configuring Claude Code statusline at user level."""

import json
import shutil
from pathlib import Path

import typer


class StatuslineService:
    """Configures Claude Code statusline at user level so it applies in any project."""

    SCRIPT_DIR = Path(__file__).parent
    USER_CLAUDE_DIR = Path.home() / ".claude"
    SCRIPT_NAME = "statusline-command.sh"

    @classmethod
    def configure(cls) -> int:
        """Install statusline script at user level and clean project-level overrides.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Install script to ~/.claude/
            script_dest = cls._install_script()

            # Set statusLine in ~/.claude/settings.json
            cls._set_statusline_in_settings(
                cls.USER_CLAUDE_DIR / "settings.json",
                f"bash {script_dest}",
            )
            typer.echo(f"Statusline configured in {cls.USER_CLAUDE_DIR / 'settings.json'}")

            # Remove project-level statusLine overrides so the user-level one is used
            project_settings = Path("/lab/user/.claude/settings.json")
            if cls._remove_statusline_from_settings(project_settings):
                typer.echo(f"Removed project-level statusLine override from {project_settings}")

            typer.echo("Done. Restart Claude Code to apply.")
            return 0
        except Exception as e:
            typer.echo(f"Error configuring statusline: {e}", err=True)
            return 1

    @classmethod
    def _install_script(cls) -> Path:
        """Copy the statusline shell script to ~/.claude/.

        Returns:
            Path to the installed script.
        """
        source = cls.SCRIPT_DIR / "statusline_command.sh"
        cls.USER_CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
        dest = cls.USER_CLAUDE_DIR / cls.SCRIPT_NAME
        shutil.copy2(source, dest)
        dest.chmod(0o755)
        return dest

    @classmethod
    def _set_statusline_in_settings(cls, settings_path: Path, command: str) -> None:
        """Set the statusLine config in a settings.json, preserving other keys."""
        if settings_path.exists():
            with open(settings_path, "r") as f:
                settings = json.load(f)
        else:
            settings = {}

        settings["statusLine"] = {"type": "command", "command": command}

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")

    @classmethod
    def _remove_statusline_from_settings(cls, settings_path: Path) -> bool:
        """Remove statusLine from a settings.json if present.

        Returns:
            True if the key was removed, False otherwise.
        """
        if not settings_path.exists():
            return False

        with open(settings_path, "r") as f:
            settings = json.load(f)

        if "statusLine" not in settings:
            return False

        del settings["statusLine"]

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")

        return True
