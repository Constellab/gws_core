

from ..utils.settings import Settings
from .base_service import BaseService


class SettingsService(BaseService):

    @classmethod
    def get_settings(cls) -> Settings:
        return Settings.get_instance()
