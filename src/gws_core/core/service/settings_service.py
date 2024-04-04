

from typing import List

from ..utils.settings import PipPackage, Settings
from .base_service import BaseService


class SettingsService(BaseService):

    @classmethod
    def get_settings(cls) -> Settings:
        return Settings.get_instance()

    @classmethod
    def get_installed_pip_packages(cls) -> List[PipPackage]:
        return cls.get_settings().get_all_pip_packages()
