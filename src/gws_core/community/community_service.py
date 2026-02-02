from typing import Any

from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException
from gws_core.core.model.model_dto import PageDTO
from gws_core.core.utils.logger import Logger
from gws_core.impl.agent.helper.agent_factory import AgentFactory
from gws_core.tag.tag_dto import ShareTagMode

from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .community_dto import (
    CommunityAgentDTO,
    CommunityAgentFileDTO,
    CommunityAgentVersionCreateResDTO,
    CommunityAgentVersionDTO,
    CommunityCreateAgentDTO,
    CommunityTagKeyDTO,
    CommunityTagValueDTO,
)


class CommunityService:
    api_key_header_key: str = "Authorization"
    api_key_header_prefix: str = "api-key"
    # Key to set the user in the request
    user_id_header_key: str = "User"

    @classmethod
    def get_community_agent_version(cls, agent_version_id: str) -> CommunityAgentVersionDTO:
        """
        Get a community by its id
        """
        url = f"{cls.get_community_api_url()}/agent/{agent_version_id}/version/latest/for-lab/{AgentFactory().current_json_version}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionDTO.from_json(response.json())

    @classmethod
    def get_community_available_space(cls) -> Any:
        url = f"{cls.get_community_api_url()}/space/available/for-lab"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community spaces for the lab. Error : {err.detail}"
            raise err
        return response.json()

    @classmethod
    def get_community_available_agents(
        cls,
        spaces_filter: list[str],
        title_filter: str,
        personal_only: bool,
        page: int,
        number_of_items_per_page: int,
    ) -> PageDTO[CommunityAgentDTO]:
        url = f"{cls.get_community_api_url()}/agent/available/for-lab?page={page}&size={number_of_items_per_page}"
        try:
            response = ExternalApiService.post(
                url,
                {
                    "titleFilter": title_filter,
                    "spacesFilter": spaces_filter,
                    "personalOnly": personal_only,
                },
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        res_parsed = response.json()
        return PageDTO(
            is_first_page=res_parsed["first"],
            is_last_page=res_parsed["last"],
            page=res_parsed["currentPage"],
            prev_page=res_parsed["currentPage"] - 1,
            next_page=res_parsed["currentPage"] + 1,
            last_page=(res_parsed["totalElements"] % res_parsed["pageSize"]),
            total_number_of_items=res_parsed["totalElements"],
            total_number_of_pages=(res_parsed["totalElements"] % res_parsed["pageSize"]) + 1,
            number_of_items_per_page=res_parsed["pageSize"],
            objects=[CommunityAgentDTO.from_json(agent) for agent in res_parsed["objects"]],
            total_is_approximate=False,
        )

    @classmethod
    def get_community_agent(cls, agent_version_id: str) -> CommunityAgentDTO:
        """
        Get a community agent by comunity agent version id
        """
        url = f"{cls.get_community_api_url()}/agent/for-lab/version/{agent_version_id}/{AgentFactory().current_json_version}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community agents for the lab. Error : {err.detail}"
            raise err
        return CommunityAgentDTO.from_json(response.json())

    @classmethod
    def get_community_agent_and_check_rights(
        cls, agent_version_id: str
    ) -> CommunityAgentDTO | None:
        """
        Get a community agent by comunity agent version id and check if the user has the right to edit it, if not return None
        """
        url = f"{cls.get_community_api_url()}/agent/for-lab/check-rights/version/{agent_version_id}/{AgentFactory().current_json_version}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            Logger.info(f"Can't retrieve community agent for the lab. Error : {err.detail}")
            return None
        return CommunityAgentDTO.from_json(response.json())

    @classmethod
    def create_community_agent(
        cls, version_file: CommunityAgentFileDTO, form_data: CommunityCreateAgentDTO
    ) -> CommunityAgentVersionCreateResDTO:
        url = f"{cls.get_community_api_url()}/agent/for-lab"
        try:
            response = ExternalApiService.post(
                url,
                {
                    "versionFile": version_file.to_json_dict(),
                    "title": form_data.title,
                    "type": form_data.type,
                    "space": form_data.space,
                },
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

    @classmethod
    def fork_community_agent(
        cls,
        version_file: CommunityAgentFileDTO,
        form_data: CommunityCreateAgentDTO,
        agent_version_id: str,
    ) -> CommunityAgentVersionCreateResDTO:
        url = f"{cls.get_community_api_url()}/agent/for-lab/fork/{agent_version_id}"
        try:
            response = ExternalApiService.post(
                url,
                {
                    "versionFile": version_file.to_json_dict(),
                    "title": form_data.title,
                    "type": form_data.type,
                    "space": form_data.space,
                },
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

    @classmethod
    def create_community_agent_version(
        cls, version_file: CommunityAgentFileDTO, agent_id: str
    ) -> CommunityAgentVersionCreateResDTO:
        url = f"{cls.get_community_api_url()}/agent/for-lab/version/{agent_id}"
        try:
            response = ExternalApiService.post(
                url,
                {"versionFile": version_file.to_json_dict()},
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't create community agent version from the lab. Error : {err.detail}"
            raise err
        return CommunityAgentVersionCreateResDTO.from_json(response.json())

    @classmethod
    def send_process_run_stats(cls, run_stats: list[dict]) -> None:
        url = f"{cls.get_community_api_url()}/run-stat-lab/new-stats"
        try:
            ExternalApiService.post(
                url, {"stats": run_stats}, cls._get_request_header(), raise_exception_if_error=True, timeout=60*5
            )
        except BaseHTTPException as err:
            err.detail = f"Can't send run stats to Community. Error : {err.detail}"
            raise err

    @classmethod
    def send_app_stat(cls, app_url: str) -> None:
        url = f"{cls.get_community_api_url()}/app/for-lab/stat"
        try:
            ExternalApiService.post(
                url, {"app_url": app_url}, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't send app stat to Community. Error : {err.detail}"
            raise err

    @classmethod
    def get_community_tag_key(cls, key: str) -> CommunityTagKeyDTO | None:
        """
        Get a community tag key by its technical name
        """
        url = f"{cls.get_community_api_url()}/tag/for-lab/key/{key}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community tag key for the lab. Error : {err.detail}"
            raise err
        return CommunityTagKeyDTO.from_json(response.json())

    @classmethod
    def get_community_tag_value(cls, key: str, value_id: str) -> CommunityTagValueDTO | None:
        """
        Get a community tag value by its key and value id
        """
        url = f"{cls.get_community_api_url()}/tag/for-lab/key/{key}/value/{value_id}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community tag value for the lab. Error : {err.detail}"
            raise err
        return CommunityTagValueDTO.from_json(response.json())

    @classmethod
    def get_available_community_tags(
        cls,
        spaces_filter: list[str],
        key_filter: str,
        label_filter: str,
        personal_only: bool,
        page: int,
        number_of_items_per_page: int,
    ) -> PageDTO[CommunityTagKeyDTO]:
        url = f"{cls.get_community_api_url()}/tag/for-lab/available?page={page}&size={number_of_items_per_page}"
        try:
            response = ExternalApiService.post(
                url,
                {
                    "technicalNameFilter": key_filter,
                    "labelFilter": label_filter,
                    "spacesFilter": spaces_filter,
                    "personalOnly": personal_only,
                },
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community tags for the lab. Error : {err.detail}"
            raise err
        res_parsed = response.json()
        if res_parsed["pageSize"] == 0:
            return PageDTO(
                is_first_page=True,
                is_last_page=True,
                page=0,
                prev_page=0,
                next_page=0,
                last_page=0,
                total_number_of_items=0,
                total_number_of_pages=1,
                number_of_items_per_page=number_of_items_per_page,
                objects=[],
                total_is_approximate=False,
            )
        return PageDTO(
            is_first_page=res_parsed["first"],
            is_last_page=res_parsed["last"],
            page=res_parsed["currentPage"],
            prev_page=res_parsed["currentPage"] - 1,
            next_page=res_parsed["currentPage"] + 1,
            last_page=(res_parsed["totalElements"] % res_parsed["pageSize"]),
            total_number_of_items=res_parsed["totalElements"],
            total_number_of_pages=(res_parsed["totalElements"] % res_parsed["pageSize"]) + 1,
            number_of_items_per_page=res_parsed["pageSize"],
            objects=[CommunityTagKeyDTO.from_json(tag) for tag in res_parsed["objects"]],
            total_is_approximate=False,
        )

    @classmethod
    def get_community_tag_values(
        cls, community_tag_key: str, page: int, number_of_items_per_page: int
    ) -> PageDTO[CommunityTagValueDTO]:
        url = f"{cls.get_community_api_url()}/tag/for-lab/key/{community_tag_key}/values?page={page}&size={number_of_items_per_page}"
        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community tag values for the lab. Error : {err.detail}"
            raise err
        res_parsed = response.json()
        if res_parsed["pageSize"] == 0:
            return PageDTO(
                is_first_page=True,
                is_last_page=True,
                page=0,
                prev_page=0,
                next_page=0,
                last_page=0,
                total_number_of_items=0,
                total_number_of_pages=1,
                number_of_items_per_page=number_of_items_per_page,
                objects=[],
                total_is_approximate=False,
            )
        return PageDTO(
            is_first_page=res_parsed["first"],
            is_last_page=res_parsed["last"],
            page=res_parsed["currentPage"],
            prev_page=res_parsed["currentPage"] - 1,
            next_page=res_parsed["currentPage"] + 1,
            last_page=(res_parsed["totalElements"] % res_parsed["pageSize"]),
            total_number_of_items=res_parsed["totalElements"],
            total_number_of_pages=(res_parsed["totalElements"] % res_parsed["pageSize"]) + 1,
            number_of_items_per_page=res_parsed["pageSize"],
            objects=[CommunityTagValueDTO.from_json(tag) for tag in res_parsed["objects"]],
            total_is_approximate=False,
        )

    @classmethod
    def get_all_community_tag_values(cls, key: str) -> list[CommunityTagValueDTO]:
        """
        Get all community tag values for a given key
        """
        url = f"{cls.get_community_api_url()}/tag/for-lab/key/{key}/values/all"

        try:
            response = ExternalApiService.get(
                url, cls._get_request_header(), raise_exception_if_error=True
            )
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve community tag values for the lab. Error : {err.detail}"
            raise err
        return [CommunityTagValueDTO.from_json(value) for value in response.json()]

    @classmethod
    def share_tag_to_community(
        cls,
        tag_key: CommunityTagKeyDTO,
        tag_values: list[CommunityTagValueDTO],
        publish_mode: ShareTagMode,
        space_selected: str | None = None,
    ) -> CommunityTagKeyDTO:
        """
        Share a tag key and its values to the community
        """
        url = f"{cls.get_community_api_url()}/tag/for-lab/share"

        try:
            response = ExternalApiService.post(
                url,
                {
                    "tagKey": tag_key.to_json_dict(),
                    "tagValues": [value.to_json_dict() for value in tag_values],
                    "spaceId": space_selected if publish_mode == "SPACE" else None,
                },
                cls._get_request_header(),
                raise_exception_if_error=True,
            )
        except BaseHTTPException as err:
            err.detail = f"Can't share tag to community. Error : {err.detail}"
            raise err
        return CommunityTagKeyDTO.from_json(response.json())

    @classmethod
    def get_community_api_url(cls) -> str:
        community_api_url = Settings.get_community_api_url()
        if community_api_url is None:
            raise Exception("Environment variable 'COMMUNITY_API_URL' is not set")
        return community_api_url

    @classmethod
    def _get_request_header(cls) -> dict[str, str]:
        """
        Return the header for a request to space, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {
            cls.api_key_header_key: cls.api_key_header_prefix + " " + Settings.get_space_api_key()
        }

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[cls.user_id_header_key] = user.id

        return headers
