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
    def check_api_key(cls, api_key: str) -> bool:

        settings: Settings = Settings.retrieve()

        # In local env, we don't check the api key
        if settings.get_lab_environment() == 'LOCAL':
            return True

        if settings.is_dev:
            raise BadRequestException("The central routes are desactivated in dev environment")

        api_key = Settings.get_central_api_key()
        return api_key == api_key

    @classmethod
    def check_credentials(cls, credentials: CredentialsDTO) -> bool:
        """
        Check the credential of an email/password by calling central
        and return true if ok
        """
        central_api_url: str = CentralService._get_central_api_url(
            'auth/login')
        response = ExternalApiService.post(central_api_url, credentials.dict())

        return response.status_code == 201

    @classmethod
    def _get_central_api_url(cls, route: str) -> str:
        """
        Build an URL to call the central API
        """

        central_api_url = Settings.get_central_api_url()
        if central_api_url is None:
            raise BadRequestException('The CENTRAL_API_URL environment variable is not set')
        return central_api_url + route
