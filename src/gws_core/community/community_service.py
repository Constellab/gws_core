from typing import Any, Dict, List

from gws_core.code.agent_factory import AgentFactory
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException

from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .community_dto import (CommunityAgentDTO, CommunityAgentFileDTO,
                            CommunityAgentVersionCreateResDTO,
                            CommunityAgentVersionDTO, CommunityCreateAgentDTO)


class CommunityService:

    community_api_url = Settings.get_community_api_url()
    api_key_header_key: str = 'Authorization'
    api_key_header_prefix: str = 'api-key'
    # Key to set the user in the request
    user_id_header_key: str = 'User'

    @classmethod
    def get_community_agent_version(cls, agent_version_id: str) -> CommunityAgentVersionDTO:
        """
        Get a community by its id
        """
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/{agent_version_id}/version/latest/for-lab/{AgentFactory().current_json_version}"
        try:
            response = ExternalApiService.get(url, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionDTO.from_json(response.json())

    @classmethod
    def get_community_available_space(cls) -> Any:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/space/available/for-lab"
        try:
            response = ExternalApiService.get(url, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community spaces for the lab. Error : {err.detail}"
            raise err
        return response.json()

    @classmethod
    def get_community_available_agents(
            cls, spaces_filter: List[str],
            title_filter: str, personal_only: bool, page: int, number_of_items_per_page: int) -> Any:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/available/for-lab?page={page}&size={number_of_items_per_page}"
        try:
            response = ExternalApiService.post(
                url, {'titleFilter': title_filter, 'spacesFilter': spaces_filter, 'personalOnly': personal_only},
                cls._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        res_parsed = response.json()
        return {
            'page': res_parsed['currentPage'],
            'prev_page': res_parsed['currentPage'] - 1,
            'next_page': res_parsed['currentPage'] + 1,
            'last_page': (res_parsed['totalElements'] % res_parsed['pageSize']),
            'total_number_of_items': res_parsed['totalElements'],
            'total_number_of_pages': (res_parsed['totalElements'] % res_parsed['pageSize']) + 1,
            'number_of_items_per_page': res_parsed['pageSize'],
            'objects': res_parsed['objects'],
            'is_first_page': res_parsed['first'],
            'is_last_page': res_parsed['last'],
            'total_is_approximate': False
        }

    @classmethod
    def get_community_agent(cls, agent_version_id: str) -> CommunityAgentDTO:
        """
        Get a community agent by comunity agent version id
        """
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/for-lab/version/{agent_version_id}/{AgentFactory().current_json_version}"
        try:
            response = ExternalApiService.get(url, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        return CommunityAgentDTO.from_json(response.json())

    @classmethod
    def create_community_agent(
            cls, version_file: CommunityAgentFileDTO, form_data: CommunityCreateAgentDTO) -> CommunityAgentVersionCreateResDTO:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/for-lab"
        try:
            response = ExternalApiService.post(url,
                                               {'versionFile': version_file.to_json_dict(), 'title': form_data.title,
                                                'type': form_data.type, 'space': form_data.space},
                                               cls._get_request_header(),
                                               raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

    @classmethod
    def fork_community_agent(cls, version_file: CommunityAgentFileDTO, form_data: CommunityCreateAgentDTO,
                             agent_version_id: str) -> CommunityAgentVersionCreateResDTO:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/for-lab/fork/{agent_version_id}"
        try:
            response = ExternalApiService.post(url,
                                               {'versionFile': version_file.to_json_dict(), 'title': form_data.title,
                                                'type': form_data.type, 'space': form_data.space},
                                               cls._get_request_header(),
                                               raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

    @classmethod
    def create_community_agent_version(
            cls, version_file: CommunityAgentFileDTO, agent_id: str) -> CommunityAgentVersionCreateResDTO:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/agent/for-lab/version/{agent_id}"
        try:
            response = ExternalApiService.post(
                url, {'versionFile': version_file.to_json_dict()},
                cls._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent version from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

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
