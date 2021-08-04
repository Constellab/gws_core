# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..user.credentials_dto import CredentialsDTO


class CentralService(BaseService):

    @classmethod
    def check_api_key(cls, api_key: str):
        central_settings = CentralService.__get_central_settings()
        return central_settings.get("api_key") == api_key

    @classmethod
    def set_api_key(cls, api_key: str):
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            settings.data["central"] = {}

        settings.data["central"]["api_key"] = api_key
        tf = settings.save()
        return {"status": tf}

    @classmethod
    def check_credentials(cls, credentials: CredentialsDTO) -> bool:
        """
        Check the credential of an email/password by calling central
        and return true if ok
        """
        central_api_url: str = CentralService.__get_central_api_url(
            'auth/login')
        response = ExternalApiService.post(central_api_url, credentials.dict())

        return response.status_code == 201

    @classmethod
    def __get_central_api_url(cls, route: str) -> str:
        """
        Build an URL to call the central API
        """
        central_settings = CentralService.__get_central_settings()

        return central_settings.get('api_url') + route

    @classmethod
    def __get_central_settings(cls) -> Dict:
        """
        Retrieve the central settings and throw error if the settings does not exists
        """
        settings = Settings.retrieve()
        if not settings.data.get("central"):
            raise BadRequestException("The central setting does not exists")

        return settings.data.get("central")
