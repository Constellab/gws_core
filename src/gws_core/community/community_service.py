from pydantic import parse_obj_as

from .community_dto import CommunityLiveTaskVersionDTO
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException

class CommunityService(BaseService):

    community_api_url = Settings.get_community_api_url()

    @classmethod
    def get_community_live_task_version(cls, live_task_version_id: str) -> CommunityLiveTaskVersionDTO:
        """
        Get a community by its id
        """
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/live-task/version/{live_task_version_id}/for-lab/"
        try:
            # response = ExternalApiService.get(f"{cls.community_api_url}/live-task/version/{live_task_version_id}/",
            #                                   raise_exception_if_error=True)
            response = ExternalApiService.get(url, raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community live tasks for the lab. Error : {err.detail}"
            raise err
        return parse_obj_as(CommunityLiveTaskVersionDTO, response.json())
