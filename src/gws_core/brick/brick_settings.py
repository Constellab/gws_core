"""Brick settings data structures and parsing"""

import json
import os
from typing import Any, ClassVar

from gws_core.core.model.model_dto import BaseModelDTO


class BrickSettingsPipPackage(BaseModelDTO):
    """DTO representing a pip package"""

    name: str | None = None
    version: str | None = None

    def get_package_spec(self) -> str | None:
        """Get the package specification for pip install.

        :return: Package spec like 'package==1.0.0', 'package>=1.0,<2.0', or 'package', None if no name
        :rtype: str | None
        """
        if not self.name:
            return None

        if not self.version:
            return self.name

        # If version contains operators (>, <, =, !, ~, etc.), use it as-is
        # Otherwise, treat it as an exact version and prefix with ==
        version_operators = ['>', '<', '=', '!', '~', '*']
        if any(op in self.version for op in version_operators):
            return f"{self.name}{self.version}"
        else:
            return f"{self.name}=={self.version}"


class BrickSettingsPipSource(BaseModelDTO):
    """DTO representing a pip source with packages"""

    source: str | None = None
    packages: list[BrickSettingsPipPackage] | None = None

    DEFAULT_SOURCE: ClassVar[str] = "https://pypi.python.org/simple"

    def get_source_url(self) -> str:
        """Get the pip source URL, defaulting to PyPI if not specified.

        :return: Source URL
        :rtype: str
        """
        return self.source if self.source else self.DEFAULT_SOURCE

    def get_package_specs(self) -> list[str]:
        """Get all valid package specifications from this source.

        :return: List of package specs like ['package1==1.0.0', 'package2']
        :rtype: list[str]
        """
        if not self.packages:
            return []

        package_specs = []
        for package in self.packages:
            spec = package.get_package_spec()
            if spec:
                package_specs.append(spec)
        return package_specs

    def get_pip_install_command(self) -> list[str]:
        """Get the pip install command for this source.

        :return: Command as list like ['pip', 'install', '-i', 'source_url', 'package1', 'package2']
        :rtype: list[str]
        """
        package_specs = self.get_package_specs()
        if not package_specs:
            return []

        return ["pip", "install", "-i", self.get_source_url()] + package_specs


class BrickSettingsBrickDependency(BaseModelDTO):
    """DTO representing a brick dependency"""

    name: str
    version: str


class BrickSettingsEnvironment(BaseModelDTO):
    """DTO representing the environment section in settings.json"""

    bricks: list[BrickSettingsBrickDependency] | None = None
    pip: list[BrickSettingsPipSource] | None = None
    git: list[Any] | None = None

    def add_brick_dependency(self, brick_name: str, brick_version: str) -> None:
        """Add a brick dependency to the environment.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param brick_version: Version of the brick
        :type brick_version: str
        """
        if not self.bricks:
            self.bricks = []

        self.bricks.append(BrickSettingsBrickDependency(name=brick_name, version=brick_version))


class BrickSettings:
    """DTO representing the content of a brick's settings.json file"""

    name: str | None = None
    author: str | None = None
    version: str | None = None
    variables: dict[str, str] | None = None
    technical_info: dict[str, str] | None = None
    environment: BrickSettingsEnvironment | None = None

    FILE_NAME: str = "settings.json"

    def __init__(
        self,
        name: str | None = None,
        author: str | None = None,
        version: str | None = None,
        variables: dict[str, str] | None = None,
        technical_info: dict[str, str] | None = None,
        environment: BrickSettingsEnvironment | None = None,
    ):
        self.name = name
        self.author = author
        self.version = version
        self.variables = variables
        self.technical_info = technical_info
        self.environment = environment

    def count_pip_packages(self) -> int:
        """Count the total number of pip packages defined in the settings.

        :return: Total number of pip packages
        :rtype: int
        """
        if not self.environment or not self.environment.pip:
            return 0

        total_packages = sum(
            len(source.packages) if source.packages else 0 for source in self.environment.pip
        )
        return total_packages

    def get_pip_sources(self) -> list[BrickSettingsPipSource]:
        """Get all pip sources from the settings.

        :return: List of pip sources, empty list if none
        :rtype: list[BrickSettingsPipSource]
        """
        if not self.environment or not self.environment.pip:
            return []
        return self.environment.pip

    def add_brick_dependency(self, brick_name: str, brick_version: str) -> None:
        """Add a brick dependency to the technical_info section.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param brick_version: Version of the brick
        :type brick_version: str
        """
        if not self.environment:
            self.environment = BrickSettingsEnvironment()

        self.environment.add_brick_dependency(brick_name, brick_version)

    def to_json_dict(self) -> dict:
        """Convert the BrickSettings to a JSON string.

        :return: JSON string representation of the BrickSettings
        :rtype: str
        """
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "variables": self.variables,
            "technical_info": self.technical_info,
            "environment": self.environment.to_json_dict() if self.environment else {},
        }

    @staticmethod
    def from_file_path(file_path: str) -> "BrickSettings":
        """Create a BrickSettingsDTO from a settings.json file path.

        :param file_path: Path to the settings.json file
        :type file_path: str
        :return: BrickSettingsDTO with all settings, or None if file doesn't exist or can't be parsed
        :rtype: Optional[BrickSettingsDTO]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"settings.json file not found at path: {file_path}")

        settings_data: dict[str, Any]
        with open(file_path, encoding="utf-8") as f:
            settings_data = json.load(f)

        # Parse environment if present
        environment = None
        if "environment" in settings_data:
            env_data = settings_data["environment"]
            pip_sources = None
            if "pip" in env_data:
                pip_sources = []
                for pip_source in env_data["pip"]:
                    packages = None
                    if "packages" in pip_source:
                        packages = [
                            BrickSettingsPipPackage(**pkg) for pkg in pip_source["packages"]
                        ]
                    pip_sources.append(
                        BrickSettingsPipSource(source=pip_source.get("source"), packages=packages)
                    )
            environment = BrickSettingsEnvironment(pip=pip_sources, git=env_data.get("git"))

        return BrickSettings(
            name=settings_data.get("name"),
            author=settings_data.get("author"),
            version=settings_data.get("version"),
            variables=settings_data.get("variables"),
            technical_info=settings_data.get("technical_info"),
            environment=environment,
        )
