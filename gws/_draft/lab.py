# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings

class Lab:

    @classmethod
    def get_uri(cls):
        settings = Settings.retrieve()
        return settings.get_data("uri")
    
    @classmethod
    def get_name(cls):
        settings = Settings.retrieve()
        return settings.name

    @classmethod
    def get_token(cls):
        settings = Settings.retrieve()
        return settings.get_data("token")

    @classmethod
    def get_status(cls):
        settings = Settings.retrieve()
        return {
            "uri": settings.get_data("uri"),
            "token": "", #settings.get_data("token"),
            "is_test": settings.is_test
        }