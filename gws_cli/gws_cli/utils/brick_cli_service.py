"""Service for managing brick operations in the CLI"""

from typing import List

from gws_core.brick.brick_service import BrickService
from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.utils.settings import Settings


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
    def list_installed_bricks_with_versions(cls) -> List[BrickDirectoryWithVersionDTO]:
        """List all installed brick directories with their versions.

        Returns a list of bricks sorted with gws_core first, then alphabetically.

        :return: List of brick directories with versions
        :rtype: List[BrickDirectoryWithVersionDTO]
        """

        user_bricks_folder = Settings.get_user_bricks_folder()

        brick_dirs = BrickService.list_brick_directories()
        bricks_with_versions: List[BrickDirectoryWithVersionDTO] = []

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
    def get_brick_settings(cls, brick_path: str) -> BrickSettings | None:
        """Read brick settings from a brick path.

        :param brick_path: Path to the brick folder
        :type brick_path: str
        :return: Brick settings or None if not found
        :rtype: BrickSettingsDTO | None
        """
        return BrickService.read_brick_settings(brick_path)
