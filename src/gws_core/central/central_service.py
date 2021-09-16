# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..study.study_dto import CentralStudy
from ..user.credentials_dto import CredentialsDTO
from ..user.current_user_service import CurrentUserService
from ..user.user import User


class CentralService(BaseService):

    # external lab route on central
    _external_labs_route: str = 'external-labs'
    _api_key_header: str = 'api-key'

    @classmethod
    def check_api_key(cls, api_key: str) -> bool:

        settings: Settings = Settings.retrieve()

        # In local env, we don't check the api key
        if settings.get_lab_environment() == 'LOCAL':
            return True

        if settings.is_dev:
            raise BadRequestException("The central routes are desactivated in dev environment")

        central_api_key = Settings.get_central_api_key()
        return central_api_key == api_key

    @classmethod
    def check_credentials(cls, credentials: CredentialsDTO) -> bool:
        """
        Check the credential of an email/password by calling central
        and return true if ok
        """
        central_api_url: str = cls._get_central_api_url(
            'auth/login')
        response = ExternalApiService.post(central_api_url, credentials.dict())

        return response.status_code == 201

    @classmethod
    def get_current_user_studies(cls) -> List[CentralStudy]:
        """
        Call the central api to get the list of study for the current user
        """
        user: User = CurrentUserService.get_and_check_current_user()
        central_api_url: str = cls._get_central_api_url(f"{cls._external_labs_route}/user/{user.uri}/studies")
        response = ExternalApiService.get(central_api_url, cls._get_api_key_header())

        if response.status_code != 200:
            Logger.error(f"Can't retrieve studies for the user {user.uri}, {user.email}")
            raise BadRequestException(f"Can't retrieve studies for current user")

        return response.json()

    @classmethod
    def _get_central_api_url(cls, route: str) -> str:
        """
        Build an URL to call the central API
        """

        central_api_url = Settings.get_central_api_url()
        if central_api_url is None:
            raise BadRequestException('The CENTRAL_API_URL environment variable is not set')
        return central_api_url + route

    @classmethod
    def _get_api_key_header(cls) -> Dict[str, str]:
        """
        Return the api key header to authenticate to central api
        """
        return {cls._api_key_header: Settings.get_central_api_key()}
