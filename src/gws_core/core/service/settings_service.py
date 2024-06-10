
from ..utils.settings import Settings


class SettingsService():

    @classmethod
    def get_settings(cls) -> Settings:
        return Settings.get_instance()
