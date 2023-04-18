# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from requests.models import Response
from typing_extensions import TypedDict

from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings
from gws_core.share.share_link import ShareLinkType
from gws_core.user.user import User


class ExternalLabWithUserInfo(TypedDict):
    """Class that contains information a lab when 2 labs communicate with each other"""
    lab_id: str
    lab_name: str
    lab_api_url: str

    user_id: str
    user_firstname: str
    user_lastname: str

    space_id: str
    space_name: str


class ExternalLabService():

    _core_api = 'core-api'

    """Class that contains method to communicate with external lab API"""

    @classmethod
    def get_shared_object(cls, link: str) -> Response:
        """Method that download a shared object from a given link of another lab (like resource)"""
        return ExternalApiService.get(link, raise_exception_if_error=True, timeout=60 * 30)

    @classmethod
    def mark_shared_object_as_received(cls, lab_api_url: str, entity_type: ShareLinkType,
                                       token: str, current_lab_info: ExternalLabWithUserInfo) -> Response:
        """Method that mark a shared object as received"""
        return ExternalApiService.post(
            f"{lab_api_url}/{cls._core_api}/share/{entity_type.value}/mark-as-shared/{token}", current_lab_info)

    @classmethod
    def get_current_lab_info(cls, user: User) -> ExternalLabWithUserInfo:
        """Get information about the current lab. Usefule when 2 labs communicate with each other"""
        settings = Settings.get_instance()
        space = settings.get_space()
        return {
            'lab_id': settings.get_lab_id(),
            'lab_name': settings.get_lab_name(),
            'lab_api_url': settings.get_lab_api_url(),
            'user_id': user.id,
            'user_firstname': user.first_name,
            'user_lastname': user.last_name,
            'space_id': space['id'] if space is not None else None,
            'space_name': space['name'] if space is not None else None
        }
