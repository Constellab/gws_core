from pydantic import parse_obj_as

from typing import Dict, List

from .community_dto import CommunityLiveTaskVersionDTO, CommunityLiveTaskDTO
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from ..user.user import User
from ..user.current_user_service import CurrentUserService

class CommunityService(BaseService):

    community_api_url = Settings.get_community_api_url()
    api_key_header_key: str = 'Authorization'
    api_key_header_prefix: str = 'api-key'
    # Key to set the user in the request
    user_id_header_key: str = 'User'

    @classmethod
    def get_community_live_task_version(cls, live_task_version_id: str) -> CommunityLiveTaskVersionDTO:
        """
        Get a community by its id
        """
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/live-task/{live_task_version_id}/version/latest/for-lab/"
        try:
            # response = ExternalApiService.get(f"{cls.community_api_url}/live-task/version/{live_task_version_id}/",
            #                                   raise_exception_if_error=True)
            response = ExternalApiService.get(url, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community live tasks for the lab. Error : {err.detail}"
            raise err
        return parse_obj_as(CommunityLiveTaskVersionDTO, response.json())

    @classmethod
    def get_community_available_live_tasks(cls) -> List[CommunityLiveTaskDTO]:
        """
        Get a community by its id
        """
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/live-task/available/for-lab/"
        try:
            # response = ExternalApiService.get(f"{cls.community_api_url}/live-task/version/{live_task_version_id}/",
            #                                   raise_exception_if_error=True)
            response = ExternalApiService.get(url, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community live tasks for the lab. Error : {err.detail}"
            raise err
        return parse_obj_as(List[CommunityLiveTaskDTO], response.json())

    @classmethod
    def _get_request_header(cls) -> Dict[str, str]:
        """
        Return the header for a request to space, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {cls.api_key_header_key: cls.api_key_header_prefix +
                   ' ' + Settings.get_space_api_key()}

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[cls.user_id_header_key] = user.id

        return headers
