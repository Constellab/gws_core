# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests

from gws.settings import Settings
from gws.logger import Error
from gws.report import Report
from gws.model import Experiment, Protocol, User

from .base_service import BaseService

class CentralService(BaseService):

    # -- A --

    # -- C --

    @classmethod
    def check_api_key(cls, api_key: str):
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            return False
        return settings.data["central"].get("api_key") == api_key

    # -- D --

    # -- F --

    # -- G --
    # -- L --

    # -- S --

    # -- S --

    @ classmethod
    def set_api_key(cls, api_key: str):
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            settings.data["central"] = {}

        settings.data["central"]["api_key"] = api_key
        tf = settings.save()
        return {"status": tf}

    # -- V --
