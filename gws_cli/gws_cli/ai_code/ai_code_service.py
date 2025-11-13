from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class CommandFrontmatter:
    """Configuration for command file frontmatter"""
    filename: str
    description: str
    argument_hint: str


class AICodeService(ABC):
    """Base service for managing AI code assistant commands (Claude Code, GitHub Copilot, etc.)"""

    SOURCE_COMMANDS_DIR = Path(__file__).parent / "commands"
    # Frontmatter configuration for each command file
    COMMAND_FRONTMATTER: List[CommandFrontmatter] = [
        CommandFrontmatter(
            filename="reflex-app-developer.md",
            description="Create, develop, modify, or debug a Reflex web application",
            argument_hint="description of what to build"
        ),
        CommandFrontmatter(
            filename="streamlit-app-developer.md",
            description="Create, develop, modify, or debug a Streamlit web application",
            argument_hint="description of what to build"
        ),
        CommandFrontmatter(
            filename="task-expert.md",
            description="Create or modify a Constellab Task that processes data resources",
            argument_hint="task description or modification request"
        )
    ]

    def __init__(self, ai_tool_name: str):
        """Initialize AICodeService

        Args:
            ai_tool_name: Display name of the AI tool (e.g., 'Claude Code', 'GitHub Copilot')
        """
        self.ai_tool_name = ai_tool_name

    @abstractmethod
    def format_frontmatter(self, frontmatter: CommandFrontmatter) -> str:
        """Format frontmatter for the specific AI tool

        Args:
            frontmatter: The frontmatter configuration to format

        Returns:
            Formatted frontmatter string with surrounding ---
        """

    @abstractmethod
    def get_target_dir(self) -> Path:
        """Get the base directory for the AI tool's commands/instructions

        Returns:
            Path to the base directory (e.g., ~/.claude/commands or ~/.github/copilot/instructions)
        """

    @abstractmethod
    def format_filename(self, base_filename: str) -> str:
        """Format the filename for the specific AI tool

        Args:
            base_filename: The base filename (e.g., 'streamlit-app-developer.md')

        Returns:
            Formatted filename (e.g., 'streamlit-app-developer.md' for Claude,
                               'streamlit-app-developer.prompt.md' for Copilot)
        """

    @abstractmethod
    def get_file_pattern(self) -> str:
        """Get the glob pattern to match command files in the target directory

        Returns:
            Glob pattern (e.g., 'gws-*.md' for Claude, 'gws-*.prompt.md' for Copilot)
        """

    @abstractmethod
    def get_install_command(self) -> str:
        """Get the command to install/pull commands for this AI tool

        Returns:
            Command string (e.g., 'gws claude init' or 'gws copilot pull')
        """

    def pull_commands_to_global(self) -> int:
        """Pull commands from source to global AI tool commands folder

        This is a generic method that copies commands from a source directory to the
        appropriate global commands folder for different AI code assistants.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Validate source directory exists
            if not self.SOURCE_COMMANDS_DIR.exists():
                print(f"Error: Source commands directory not found at {self.SOURCE_COMMANDS_DIR}")
                return 1

            # Get target directory from child class implementation
            target_dir = self.get_target_dir()

            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Remove existing GWS files (files starting with 'gws-')
            if target_dir.exists():
                gws_files = list(target_dir.glob('gws-*'))
                if gws_files:
                    for gws_file in gws_files:
                        if gws_file.is_file():
                            gws_file.unlink()

            # Process each command from COMMAND_FRONTMATTER
            for frontmatter_config in AICodeService.COMMAND_FRONTMATTER:
                # Source file
                source_file = self.SOURCE_COMMANDS_DIR / frontmatter_config.filename

                if not source_file.exists():
                    print(f"Warning: Source file not found: {source_file}")
                    continue

                # Target file with formatted filename (prefixed with 'gws-')
                formatted_filename = self.format_filename(frontmatter_config.filename)
                target_filename = f"gws-{formatted_filename}"
                target_file = target_dir / target_filename

                # Read the source file
                content = source_file.read_text(encoding='utf-8')

                # Check if frontmatter already exists
                if not content.startswith('---'):
                    # Add frontmatter using the abstract method
                    frontmatter = self.format_frontmatter(frontmatter_config)
                    content = frontmatter + content

                # Write to target file
                target_file.write_text(content, encoding='utf-8')

            print(
                f"GWS commands successfully pulled to global {self.ai_tool_name} commands folder! Location: {target_dir}.")
            return 0

        except (OSError, IOError) as e:
            print(f"Error pulling commands: {e}")
            return 1

    def list_commands(self) -> int:
        """List all available GWS commands for the AI tool

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            target_dir = self.get_target_dir()

            print("\n" + "=" * 70)
            print(f"Available GWS commands for {self.ai_tool_name}:")
            print("=" * 70)

            if not target_dir.exists():
                print(f"\nNo commands folder found. Run '{self.get_install_command()}' to install commands.")
                return 0

            # Find all GWS command files using the pattern from child class
            file_pattern = self.get_file_pattern()
            gws_files = sorted(target_dir.glob(file_pattern))

            if not gws_files:
                print(f"\nNo GWS commands found. Run '{self.get_install_command()}' to install commands.")
                return 0

            print(f"\nLocation: {target_dir}\n")

            for gws_file in gws_files:
                # Extract command name (remove 'gws-' prefix and any extension)
                command_name = gws_file.name
                if command_name.endswith('.prompt.md'):
                    command_name = command_name.replace('.prompt.md', '')
                elif command_name.endswith('.md'):
                    command_name = command_name.replace('.md', '')

                # Try to read description from frontmatter
                description = None
                try:
                    content = gws_file.read_text(encoding='utf-8')
                    if content.startswith('---'):
                        # Extract frontmatter
                        end_frontmatter = content.find('---', 3)
                        if end_frontmatter > 0:
                            frontmatter = content[3:end_frontmatter].strip()
                            for line in frontmatter.split('\n'):
                                if line.startswith('description:'):
                                    description = line.split(':', 1)[1].strip()
                                    break
                except Exception:
                    pass

                # Print command info
                print(f"  /{command_name}")
                if description:
                    print(f"    {description}")
                print()

            print("Usage: /gws-<command-name> [your task description]")
            print("Example: /gws-streamlit-app-developer Create a dashboard")
            print("=" * 70)

            return 0

        except Exception as e:
            print(f"Error listing commands: {e}")
            return 1
