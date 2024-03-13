

from typing import Optional

from requests.models import Response

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.settings import Settings
from gws_core.share.shared_dto import ShareLinkType
from gws_core.user.user import User


class ExternalLabWithUserInfo(BaseModelDTO):
    """Class that contains information a lab when 2 labs communicate with each other"""
    lab_id: str
    lab_name: str
    lab_api_url: str

    user_id: str
    user_firstname: str
    user_lastname: str

    space_id: Optional[str]
    space_name: Optional[str]


class ExternalLabService():

    """Class that contains method to communicate with external lab API"""

    @classmethod
    def get_shared_object(cls, link: str) -> Response:
        """Method that download a shared object from a given link of another lab (like resource)"""
        return ExternalApiService.get(link, raise_exception_if_error=True, timeout=60 * 30)

    @classmethod
    def get_shared_resource_info(cls, lab_api_url: str, token: str) -> Response:
        """Method that get information about a shared resource"""
        return ExternalApiService.get(f"{lab_api_url}/{Settings.core_api_route_path()}/share/resource/info/{token}")

    @classmethod
    def mark_shared_object_as_received(cls, lab_api_url: str, entity_type: ShareLinkType,
                                       token: str, current_lab_info: ExternalLabWithUserInfo) -> Response:
        """Method that mark a shared object as received"""
        return ExternalApiService.post(
            f"{lab_api_url}/{Settings.core_api_route_path()}/share/{entity_type.value}/mark-as-shared/{token}",
            current_lab_info.dict())

    @classmethod
    def get_current_lab_info(cls, user: User) -> ExternalLabWithUserInfo:
        """Get information about the current lab. Usefule when 2 labs communicate with each other"""
        settings = Settings.get_instance()
        space = settings.get_space()
        return ExternalLabWithUserInfo(
            lab_id=settings.get_lab_id(),
            lab_name=settings.get_lab_name(),
            lab_api_url=settings.get_lab_api_url(),
            user_id=user.id,
            user_firstname=user.first_name,
            user_lastname=user.last_name,
            space_id=space['id'] if space is not None else None,
            space_name=space['name'] if space is not None else None
        )

    @classmethod
    def get_current_lab_route(cls, route: str) -> str:
        """Get the current lab route"""
        return f"{Settings.get_instance().get_lab_api_url()}/{Settings.core_api_route_path()}/{route}"
