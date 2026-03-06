import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import typer


@dataclass
class SkillFrontmatter:
    """Configuration for skill file frontmatter"""

    filename: str
    description: str
    argument_hint: str


@dataclass
class SkillInfo:
    """Information about an installed skill"""

    name: str
    description: str | None
    file_path: Path


class AICodeService(ABC):
    """Base service for managing AI code assistant skills (Claude Code, GitHub Copilot, etc.)"""

    SOURCE_SKILLS_DIR = Path(__file__).parent / "skills"

    # Plugin metadata
    PLUGIN_NAME = "gws-commands"
    PLUGIN_DESCRIPTION = "GWS-specific development skills for Constellab platform"
    PLUGIN_VERSION = "1.0.0"

    # Frontmatter configuration for each skill file
    SKILL_FRONTMATTER: list[SkillFrontmatter] = [
        SkillFrontmatter(
            filename="reflex-app-developer.md",
            description="Create, develop, modify, or debug a Reflex web application",
            argument_hint="description of what to build",
        ),
        SkillFrontmatter(
            filename="streamlit-app-developer.md",
            description="Create, develop, modify, or debug a Streamlit web application",
            argument_hint="description of what to build",
        ),
        SkillFrontmatter(
            filename="task-expert.md",
            description="Create or modify a Constellab Task that processes data resources",
            argument_hint="task description or modification request",
        ),
        SkillFrontmatter(
            filename="agent-expert.md",
            description="Create or modify a Constellab Agent that processes data resources",
            argument_hint="agent description or modification request",
        ),
        SkillFrontmatter(
            filename="nextflow-to-constellab.md",
            description="Convert a Nextflow pipeline or process to Constellab Tasks",
            argument_hint="path to Nextflow file or description of pipeline to convert",
        ),
        SkillFrontmatter(
            filename="snakemake-to-constellab.md",
            description="Convert a Snakemake workflow or rule to Constellab Tasks",
            argument_hint="path to Snakefile or description of workflow to convert",
        ),
        SkillFrontmatter(
            filename="code-review-instructions.md",
            description="Instructions for reviewing code",
            argument_hint="description of code review request",
        ),
        SkillFrontmatter(
            filename="update-doc-json.md",
            description="Update a developer documentation file to match current source code using JSON input",
            argument_hint="brick_name [doc keyword] (e.g. gws_core docker)",
        ),
    ]

    def __init__(self, ai_tool_name: str):
        """Initialize AICodeService

        Args:
            ai_tool_name: Display name of the AI tool (e.g., 'Claude Code', 'GitHub Copilot')
        """
        self.ai_tool_name = ai_tool_name

    @abstractmethod
    def format_frontmatter(self, frontmatter: SkillFrontmatter) -> str:
        """Format frontmatter for the specific AI tool

        Args:
            frontmatter: The frontmatter configuration to format

        Returns:
            Formatted frontmatter string with surrounding ---
        """

    @abstractmethod
    def get_target_dir(self) -> Path:
        """Get the base directory for the AI tool's skills/instructions

        Returns:
            Path to the base directory (e.g., plugin root dir or prompts dir)
        """

    @abstractmethod
    def get_skill_dir_name(self, base_filename: str) -> str:
        """Get the skill directory name for the specific AI tool

        Args:
            base_filename: The base filename (e.g., 'streamlit-app-developer.md')

        Returns:
            Directory or file name for the skill
        """

    @abstractmethod
    def get_skill_pattern(self) -> str:
        """Get the glob pattern to match skill files in the target directory

        Returns:
            Glob pattern for skill files/directories
        """

    @abstractmethod
    def get_install_command(self) -> str:
        """Get the command to install/pull skills for this AI tool

        Returns:
            Command string (e.g., 'gws claude update' or 'gws copilot update')
        """

    @abstractmethod
    def get_main_instructions_path(self) -> Path:
        """Get the path where main instructions file should be generated

        Returns:
            Path to the main instructions file (e.g., ~/CLAUDE.md or ~/.github/copilot-instructions.md)
        """

    @abstractmethod
    def update(self) -> int:
        """Update AI tool configuration (skills and instructions)

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """

    def pull_skills_to_global(self) -> int:
        """Pull skills from source to global AI tool skills folder

        This is a generic method that copies skills from a source directory to the
        appropriate global skills folder for different AI code assistants.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Validate source directory exists
            if not self.SOURCE_SKILLS_DIR.exists():
                typer.echo(
                    f"Error: Source skills directory not found at {self.SOURCE_SKILLS_DIR}",
                    err=True,
                )
                return 1

            # Get target directory from child class implementation
            target_dir = self.get_target_dir()

            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Clean up existing skills
            self._clean_existing_skills(target_dir)

            # Generate plugin manifest if supported
            self._generate_plugin_manifest(target_dir)

            # Process each skill from SKILL_FRONTMATTER
            for frontmatter_config in AICodeService.SKILL_FRONTMATTER:
                self._write_skill(target_dir, frontmatter_config)

            typer.echo(
                f"GWS skills successfully pulled to global {self.ai_tool_name} skills folder! Location: {target_dir}."
            )
            return 0

        except OSError as e:
            typer.echo(f"Error pulling skills: {e}", err=True)
            return 1

    def _clean_existing_skills(self, target_dir: Path) -> None:
        """Clean up existing GWS skill files/directories in the target directory

        Args:
            target_dir: The target directory to clean
        """
        # Remove existing gws- files (legacy flat format)
        for gws_file in target_dir.glob("gws-*"):
            if gws_file.is_file():
                gws_file.unlink()

        # Remove existing gws- skill directories (new format)
        skills_dir = target_dir / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.glob("gws-*"):
                if skill_dir.is_dir():
                    shutil.rmtree(skill_dir)

    def _generate_plugin_manifest(self, target_dir: Path) -> None:
        """Generate plugin manifest file. Override in subclasses that support plugins.

        Args:
            target_dir: The plugin root directory
        """

    def _write_skill(self, target_dir: Path, frontmatter_config: SkillFrontmatter) -> None:
        """Write a single skill to the target directory

        Args:
            target_dir: The target directory
            frontmatter_config: The skill frontmatter configuration
        """
        # Source file
        source_file = self.SOURCE_SKILLS_DIR / frontmatter_config.filename

        if not source_file.exists():
            typer.echo(f"Warning: Source file not found: {source_file}")
            return

        # Read the source file
        content = source_file.read_text(encoding="utf-8")

        # Check if frontmatter already exists
        if not content.startswith("---"):
            frontmatter = self.format_frontmatter(frontmatter_config)
            content = frontmatter + content

        # Get skill directory/file name and write
        skill_dir_name = self.get_skill_dir_name(frontmatter_config.filename)
        self._write_skill_file(target_dir, skill_dir_name, content)

    def _write_skill_file(self, target_dir: Path, skill_name: str, content: str) -> None:
        """Write a skill file. Override in subclasses for different structures.

        Default: writes as a flat file (legacy behavior for Copilot).

        Args:
            target_dir: The target directory
            skill_name: The skill name/filename
            content: The skill content with frontmatter
        """
        target_file = target_dir / skill_name
        target_file.write_text(content, encoding="utf-8")

    def get_skills_list(self) -> list[SkillInfo]:
        """Get a structured list of all available GWS skills for the AI tool

        Returns:
            List[SkillInfo]: List of skill information objects
        """
        skills = []
        try:
            target_dir = self.get_target_dir()

            if not target_dir.exists():
                return skills

            # Find all GWS skill files using the pattern from child class
            skill_pattern = self.get_skill_pattern()
            gws_files = sorted(target_dir.glob(skill_pattern))

            for gws_file in gws_files:
                # Extract skill name
                skill_name = self._extract_skill_name(gws_file)

                # Try to read description from frontmatter
                description = None
                try:
                    content = gws_file.read_text(encoding="utf-8")
                    if content.startswith("---"):
                        end_frontmatter = content.find("---", 3)
                        if end_frontmatter > 0:
                            frontmatter = content[3:end_frontmatter].strip()
                            for line in frontmatter.split("\n"):
                                if line.startswith("description:"):
                                    description = line.split(":", 1)[1].strip()
                                    break
                except Exception:
                    pass

                skills.append(
                    SkillInfo(name=skill_name, description=description, file_path=gws_file)
                )

        except Exception:
            pass

        return skills

    def _extract_skill_name(self, skill_file: Path) -> str:
        """Extract the skill name from a skill file path

        Args:
            skill_file: Path to the skill file

        Returns:
            The skill name
        """
        name = skill_file.name
        if name.endswith(".prompt.md"):
            name = name.replace(".prompt.md", "")
        elif name == "SKILL.md":
            name = skill_file.parent.name
        elif name.endswith(".md"):
            name = name.replace(".md", "")
        return name

    def print_skills(self) -> int:
        """Print all available GWS skills for the AI tool in a user-friendly format

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            target_dir = self.get_target_dir()

            typer.echo("\n" + "=" * 70)
            typer.echo(f"Available GWS skills for {self.ai_tool_name}:")
            typer.echo("=" * 70)

            if not target_dir.exists():
                typer.echo(
                    f"\nNo skills folder found. Run '{self.get_install_command()}' to install skills."
                )
                return 0

            skills = self.get_skills_list()

            if not skills:
                typer.echo(
                    f"\nNo GWS skills found. Run '{self.get_install_command()}' to install skills."
                )
                return 0

            typer.echo(f"\nLocation: {target_dir}\n")

            for skill in skills:
                typer.echo(f"  /{skill.name}")
                if skill.description:
                    typer.echo(f"    {skill.description}")
                typer.echo()

            typer.echo("Usage: /<skill-name> [your task description]")
            typer.echo("Example: /gws-commands:gws-streamlit-app-developer Create a dashboard")
            typer.echo("=" * 70)

            return 0

        except Exception as e:
            typer.echo(f"Error printing skills: {e}", err=True)
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
                typer.echo(f"Error: Template file not found at {template_path}", err=True)
                return 1

            template_content = template_path.read_text(encoding="utf-8")

            # Prepare the generated content with markers
            generated_content = f"{start_marker}\n{template_content}\n{end_marker}"

            # Get the target path from child class
            target_path = self.get_main_instructions_path()

            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            if target_path.exists():
                # Read existing content
                existing_content = target_path.read_text(encoding="utf-8")

                # Check if markers exist
                if start_marker in existing_content and end_marker in existing_content:
                    # Find positions of markers
                    start_pos = existing_content.find(start_marker)
                    end_pos = existing_content.find(end_marker) + len(end_marker)

                    # Replace only the generated section
                    new_content = (
                        existing_content[:start_pos]
                        + generated_content
                        + existing_content[end_pos:]
                    )
                else:
                    # No markers found, prepend generated content at the top
                    new_content = generated_content + "\n\n" + existing_content
            else:
                # File doesn't exist, create with generated content
                new_content = generated_content + "\n"

            # Write the file
            target_path.write_text(new_content, encoding="utf-8")

            typer.echo(f"Main instructions generated successfully at: {target_path}")
            return 0

        except Exception as e:
            typer.echo(f"Error generating main instructions: {e}", err=True)
            return 1

    def update_if_configured(self) -> None:
        """Update AI tool configuration only if it is already configured

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not self.is_configured():
            return

        typer.echo(f"{self.ai_tool_name} is configured. Updating configuration...")
        exit_code = self.update()
        if exit_code != 0:
            typer.echo(f"Error updating {self.ai_tool_name} configuration.", err=True)
        else:
            typer.echo(f"{self.ai_tool_name} configuration updated successfully.")

    def is_configured(self) -> bool:
        """Check if the AI tool is configured (i.e., if the target skills directory exists)

        Returns:
            bool: True if configured, False otherwise
        """
        target_dir = self.get_target_dir()

        if not target_dir.exists():
            return False

        skills = self.get_skills_list()
        return len(skills) > 0
