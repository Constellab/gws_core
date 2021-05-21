# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings
from .base_service import BaseService
    
class SettingsService(BaseService):
    
    @classmethod
    def get_settings(cls) -> Settings:
        return Settings.retrieve()
    
    