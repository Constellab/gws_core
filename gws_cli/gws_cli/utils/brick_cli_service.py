"""Service for managing brick operations in the CLI"""

import os

import typer
from gws_core.brick.brick_service import BrickService
from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.settings import Settings
from gws_core.impl.shell.shell_proxy import ShellProxy

from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.community_cli_service import CommunityCliService


class BrickDirectoryWithVersionDTO:
    """DTO representing a brick directory with its version"""

    def __init__(self, name: str, path: str, version: str | None, location: str = ""):
        self.name = name
        self.path = path
        self.version = version
        self.location = location  # "user" or "system"


class BrickCliService:
    """Service for brick CLI operations"""

    @classmethod
    def list_installed_bricks_with_versions(cls) -> list[BrickDirectoryWithVersionDTO]:
        """List all installed brick directories with their versions.

        Returns a list of bricks sorted with gws_core first, then alphabetically.

        :return: List of brick directories with versions
        :rtype: List[BrickDirectoryWithVersionDTO]
        """

        user_bricks_folder = Settings.get_user_bricks_folder()

        brick_dirs = BrickService.list_brick_directories()
        bricks_with_versions: list[BrickDirectoryWithVersionDTO] = []

        for brick_dir in brick_dirs:
            settings = BrickService.read_brick_settings(brick_dir.path)
            version = settings.version if settings else None

            # Determine location (user or system)
            location = "user" if brick_dir.path.startswith(user_bricks_folder) else "system"

            bricks_with_versions.append(
                BrickDirectoryWithVersionDTO(
                    name=brick_dir.name, path=brick_dir.path, version=version, location=location
                )
            )

        # Sort with gws_core first, then alphabetically, prefer user bricks over system
        bricks_with_versions.sort(
            key=lambda x: (
                x.name != Settings.get_gws_core_brick_name(),
                x.name,
                x.location != "user",
            )
        )

        return bricks_with_versions

    @classmethod
    def resolve_brick_dir(cls, brick_path: str | None) -> str:
        """Resolve the brick directory from an optional path argument.

        If brick_path is provided, resolves it to the parent brick folder.
        Otherwise, uses the current working directory.

        :param brick_path: Optional path to a brick folder or a path inside a brick
        :type brick_path: str | None
        :return: The resolved brick directory
        :rtype: str
        """
        if brick_path:
            absolute_path = os.path.abspath(brick_path)
            brick_dir = BrickService.get_parent_brick_folder(absolute_path)
            if not brick_dir:
                typer.echo(f"Error: {brick_path} is not inside a valid brick directory", err=True)
                raise typer.Exit(1)
            return brick_dir
        return CLIUtils.get_and_check_current_brick_dir()

    @classmethod
    def get_brick_settings(cls, brick_path: str) -> BrickSettings | None:
        """Read brick settings from a brick path.

        :param brick_path: Path to the brick folder
        :type brick_path: str
        :return: Brick settings or None if not found
        :rtype: BrickSettingsDTO | None
        """
        return BrickService.read_brick_settings(brick_path)

    @classmethod
    def create_new_brick_version(cls, brick_path: str) -> BrickSettings:
        """Read brick settings from the given path and create a new version on the community.

        Checks that a git tag matching the brick version exists in the repository before
        calling the community API.

        :param brick_path: Path to the brick folder
        :type brick_path: str
        :return: The updated BrickSettings returned by the community API
        :rtype: BrickSettings
        """
        brick_settings = BrickService.read_brick_settings(brick_path)
        if brick_settings is None:
            raise BadRequestException(f"Could not read brick settings from path: {brick_path}")

        version = brick_settings.version
        if not version:
            raise BadRequestException("Brick settings do not contain a version")

        if not cls.git_tag_exists(brick_path, version):
            raise BadRequestException(
                f"Git tag '{version}' does not exist in repository at '{brick_path}'. "
                "Please create the tag before publishing a new version."
            )

        community_user_service = CommunityCliService.get_community_service(
            requires_authentication=True
        )

        return community_user_service.create_new_brick_version(brick_settings)

    @classmethod
    def git_tag_exists(cls, repo_path: str, tag_name: str) -> bool:
        """Check if a git tag with the given name exists in the repository.

        :param repo_path: Path to the git repository
        :type repo_path: str
        :param tag_name: Tag name to look for
        :type tag_name: str
        :return: True if the tag exists, False otherwise
        :rtype: bool
        """
        try:
            shell_proxy = ShellProxy(working_dir=repo_path)
            result = shell_proxy.check_output(["git", "tag", "-l", tag_name])
            return result.strip() == tag_name
        except Exception:
            return False

    @classmethod
    def create_git_tag(cls, repo_path: str, tag_name: str, push: bool = False) -> None:
        """Create a git tag in the repository and optionally push it to origin.

        :param repo_path: Path to the git repository
        :type repo_path: str
        :param tag_name: Tag name to create
        :type tag_name: str
        :param push: If True, push the tag to origin after creating it
        :type push: bool
        """
        shell_proxy = ShellProxy(working_dir=repo_path)
        shell_proxy.check_output(["git", "tag", tag_name])

        if push:
            shell_proxy.check_output(["git", "push", "origin", tag_name])
