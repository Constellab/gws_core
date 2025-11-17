"""Brick settings data structures and parsing"""

import json
import os
from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO


class BrickSettingsPipPackage(BaseModelDTO):
    """DTO representing a pip package"""
    name: Optional[str] = None
    version: Optional[str] = None


class BrickSettingsPipSource(BaseModelDTO):
    """DTO representing a pip source with packages"""
    source: Optional[str] = None
    packages: Optional[List[BrickSettingsPipPackage]] = None


class BrickSettingsEnvironment(BaseModelDTO):
    """DTO representing the environment section in settings.json"""
    pip: Optional[List[BrickSettingsPipSource]] = None
    git: Optional[List[Any]] = None


class BrickSettings():
    """DTO representing the content of a brick's settings.json file"""
    name: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    technical_info: Optional[Dict[str, str]] = None
    environment: Optional[BrickSettingsEnvironment] = None

    FILE_NAME: str = "settings.json"

    def __init__(self, name: Optional[str] = None,
                 author: Optional[str] = None,
                 version: Optional[str] = None,
                 variables: Optional[Dict[str, str]] = None,
                 technical_info: Optional[Dict[str, str]] = None,
                 environment: Optional[BrickSettingsEnvironment] = None):
        self.name = name
        self.author = author
        self.version = version
        self.variables = variables
        self.technical_info = technical_info
        self.environment = environment

    @staticmethod
    def from_file_path(file_path: str) -> 'BrickSettings':
        """Create a BrickSettingsDTO from a settings.json file path.

        :param file_path: Path to the settings.json file
        :type file_path: str
        :return: BrickSettingsDTO with all settings, or None if file doesn't exist or can't be parsed
        :rtype: Optional[BrickSettingsDTO]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"settings.json file not found at path: {file_path}")

        settings_data: Dict[str, Any]
        with open(file_path, 'r', encoding='utf-8') as f:
            settings_data = json.load(f)

        # Parse environment if present
        environment = None
        if 'environment' in settings_data:
            env_data = settings_data['environment']
            pip_sources = None
            if 'pip' in env_data:
                pip_sources = []
                for pip_source in env_data['pip']:
                    packages = None
                    if 'packages' in pip_source:
                        packages = [BrickSettingsPipPackage(**pkg) for pkg in pip_source['packages']]
                    pip_sources.append(BrickSettingsPipSource(
                        source=pip_source.get('source'),
                        packages=packages
                    ))
            environment = BrickSettingsEnvironment(
                pip=pip_sources,
                git=env_data.get('git')
            )

        return BrickSettings(
            name=settings_data.get('name'),
            author=settings_data.get('author'),
            version=settings_data.get('version'),
            variables=settings_data.get('variables'),
            technical_info=settings_data.get('technical_info'),
            environment=environment
        )
