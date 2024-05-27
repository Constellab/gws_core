

from typing import List

from ..utils.settings import PipPackage, Settings


class SettingsService():

    @classmethod
    def get_settings(cls) -> Settings:
        return Settings.get_instance()

    @classmethod
    def get_installed_pip_packages(cls) -> List[PipPackage]:
        return cls.get_settings().get_all_pip_packages()
