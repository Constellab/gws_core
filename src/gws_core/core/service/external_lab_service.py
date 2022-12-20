# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from requests.models import Response

from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.resource.resource_zipper import ZipOriginInfo


class ExternalLabService():

    _core_api = 'core-api'

    """Class that contains method to communicate with external lab API"""

    @classmethod
    def get_shared_object(cls, link: str) -> Response:
        """Method that download a shared object from a given link of another lab (like resource)"""
        return ExternalApiService.get(link)

    @classmethod
    def mark_shared_object_as_received(cls, lab_api_url: str, token: str, current_lab_info: ZipOriginInfo) -> Response:
        """Method that mark a shared object as received"""
        return ExternalApiService.post(
            f"{lab_api_url}/{cls._core_api}/share/resource/mark-as-downloaded/{token}", current_lab_info)
