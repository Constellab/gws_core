from typing import Any, Dict, List, Literal

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.impl.agent.helper.agent_factory import AgentFactory
from gws_core.model.typing_dto import TypingRefDTO
from gws_core.model.typing_name import TypingNameObj

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
    def send_process_run_stats(cls, run_stats: List[Dict]) -> None:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/run-stat-lab/new-stats"
        try:
            ExternalApiService.post(
                url, {'stats': run_stats},
                cls._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't send run stats to Community. Error : {err.detail}"
            raise err

    @classmethod
    def send_app_stat(cls, app_url: str) -> None:
        if cls.community_api_url is None:
            return None
        url = f"{cls.community_api_url}/app/for-lab/stat"
        try:
            ExternalApiService.post(
                url, {'app_url': app_url},
                cls._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't send app stat to Community. Error : {err.detail}"
            raise err

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

    ############################################# LINKS #############################################

    @classmethod
    def get_typing_doc_url(cls, typing_name: str,
                           brick_major_version: int | Literal['latest'] = 'latest') -> str:
        typing_name_obj = TypingNameObj.from_typing_name(typing_name)
        brick_version_str = 'latest' if brick_major_version == 'latest' else 'v' + str(brick_major_version)

        object_type: str = None
        if typing_name_obj.object_type == 'TASK':
            object_type = 'task'
        elif typing_name_obj.object_type == 'RESOURCE':
            object_type = 'resource'
        else:
            raise Exception(f"Object with type '{typing_name_obj.object_type}' are not documented in community")

        return f"{cls.community_api_url}/bricks/{typing_name_obj.brick_name}/{brick_version_str}/doc/technical-folder/{object_type}/{typing_name_obj.unique_name}"
