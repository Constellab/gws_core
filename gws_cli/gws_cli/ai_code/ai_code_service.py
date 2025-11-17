from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CommandFrontmatter:
    """Configuration for command file frontmatter"""
    filename: str
    description: str
    argument_hint: str


@dataclass
class CommandInfo:
    """Information about an installed command"""
    name: str
    description: Optional[str]
    file_path: Path


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

    @abstractmethod
    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to the main instructions file (e.g., ~/CLAUDE.md or ~/.github/copilot-instructions.md)
        """

    @abstractmethod
    def update(self) -> int:
        """Update AI tool configuration (commands and instructions)

        Returns:
            int: Exit code (0 for success, 1 for failure)
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

    def get_commands_list(self) -> List[CommandInfo]:
        """Get a structured list of all available GWS commands for the AI tool

        Returns:
            List[CommandInfo]: List of command information objects
        """
        commands = []
        try:
            target_dir = self.get_target_dir()

            if not target_dir.exists():
                return commands

            # Find all GWS command files using the pattern from child class
            file_pattern = self.get_file_pattern()
            gws_files = sorted(target_dir.glob(file_pattern))

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

                commands.append(CommandInfo(
                    name=command_name,
                    description=description,
                    file_path=gws_file
                ))

        except Exception:
            pass

        return commands

    def print_commands(self) -> int:
        """Print all available GWS commands for the AI tool in a user-friendly format

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

            commands = self.get_commands_list()

            if not commands:
                print(f"\nNo GWS commands found. Run '{self.get_install_command()}' to install commands.")
                return 0

            print(f"\nLocation: {target_dir}\n")

            for command in commands:
                print(f"  /{command.name}")
                if command.description:
                    print(f"    {command.description}")
                print()

            print("Usage: /gws-<command-name> [your task description]")
            print("Example: /gws-streamlit-app-developer Create a dashboard")
            print("=" * 70)

            return 0

        except Exception as e:
            print(f"Error printing commands: {e}")
            return 1


    def generate_main_instructions(self) -> int:
        """Generate main instructions file from template

        This method reads the main_instructions.md template and generates
        the main instructions file for the specific AI tool. If the file already
        exists, it replaces only the generated section without touching custom content.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Define markers for generated content
            start_marker = "<!-- BEGIN AUTO-GENERATED GWS INSTRUCTIONS -->"
            end_marker = "<!-- END AUTO-GENERATED GWS INSTRUCTIONS -->"

            # Read the template
            template_path = Path(__file__).parent / "main_instructions.md"
            if not template_path.exists():
                print(f"Error: Template file not found at {template_path}")
                return 1

            template_content = template_path.read_text(encoding='utf-8')

            # Prepare the generated content with markers
            generated_content = f"{start_marker}\n{template_content}\n{end_marker}"

            # Get the target path from child class
            target_path = self.get_main_instructions_path()

            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            if target_path.exists():
                # Read existing content
                existing_content = target_path.read_text(encoding='utf-8')

                # Check if markers exist
                if start_marker in existing_content and end_marker in existing_content:
                    # Find positions of markers
                    start_pos = existing_content.find(start_marker)
                    end_pos = existing_content.find(end_marker) + len(end_marker)

                    # Replace only the generated section
                    new_content = (
                        existing_content[:start_pos] +
                        generated_content +
                        existing_content[end_pos:]
                    )
                else:
                    # No markers found, prepend generated content at the top
                    new_content = generated_content + "\n\n" + existing_content
            else:
                # File doesn't exist, create with generated content
                new_content = generated_content + "\n"

            # Write the file
            target_path.write_text(new_content, encoding='utf-8')

            print(f"Main instructions generated successfully at: {target_path}")
            return 0

        except Exception as e:
            print(f"Error generating main instructions: {e}")
            return 1

    def update_if_configured(self) -> None:
        """Update AI tool configuration only if it is already configured

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not self.is_configured():
            return

        print(f"{self.ai_tool_name} is configured. Updating configuration...")
        exit_code = self.update()
        if exit_code != 0:
            print(f"Error updating {self.ai_tool_name} configuration.")
        else:
            print(f"{self.ai_tool_name} configuration updated successfully.")

    def is_configured(self) -> bool:
        """Check if the AI tool is configured (i.e., if the target commands directory exists)

        Returns:
            bool: True if configured, False otherwise
        """
        target_dir = self.get_target_dir()

        if not target_dir.exists():
            return False

        commands = self.get_commands_list()
        return len(commands) > 0
