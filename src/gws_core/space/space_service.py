

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, parse_obj_as
from requests.models import Response

from gws_core.brick.brick_service import BrickService
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.space.space_dto import (LabStartDTO, SaveExperimentToSpaceDTO,
                                      SaveReportToSpaceDTO, SpaceSendMailDTO)
from gws_core.user.user_dto import UserFullDTO, UserSpace

from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..project.project_dto import SpaceProject
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from ..user.user_credentials_dto import UserCredentials2Fa, UserCredentialsDTO


class ExternalCheckCredentialResponse(BaseModel):
    status: Literal['OK', '2FA_REQUIRED']
    user: Optional[UserSpace]
    twoFAUrlCode: Optional[str]


class SpaceService(BaseService):

    # external lab route on space
    _external_labs_route: str = 'external-labs'
    api_key_header_key: str = 'Authorization'
    api_key_header_prefix: str = 'api-key'
    # Key to set the user in the request
    user_id_header_key: str = 'User'

    @classmethod
    def check_api_key(cls, api_key: str) -> bool:

        # In local env, we don't check the api key
        if Settings.get_lab_environment() == 'LOCAL':
            return True

        if Settings.is_dev_mode():
            raise BadRequestException(
                "The space routes are desactivated in dev environment")

        space_api_key = Settings.get_space_api_key()
        return space_api_key == api_key

    @classmethod
    def check_credentials(
            cls, credentials: UserCredentialsDTO, for_login: bool = True) -> ExternalCheckCredentialResponse:
        """
        Check the credential of an email/password by calling space, with 2Fa if needed
        """
        route = 'check-credentials' if for_login else 'check-credentials-simple'
        space_api_url: str = cls._get_space_api_url(
            f'{cls._external_labs_route}/{route}')
        response = ExternalApiService.post(
            space_api_url, credentials.dict(), headers=cls._get_request_header(),
            raise_exception_if_error=True)

        return parse_obj_as(ExternalCheckCredentialResponse, response.json())

    @classmethod
    def check_2_fa(cls, credentials: UserCredentials2Fa) -> UserSpace:
        """
        Check the credential of an email/password by calling space
        and return true if ok
        """
        space_api_url: str = cls._get_space_api_url(
            'auth/external/check-2fa')
        response = ExternalApiService.post(
            space_api_url, credentials.dict(), raise_exception_if_error=True)

        return parse_obj_as(UserSpace, response.json())

    @classmethod
    def register_lab_start(cls, lab_config: LabConfigModelDTO) -> bool:
        """
        Call the space api to mark the lab as started
        """
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/start")

        body = LabStartDTO(lab_config=lab_config)

        try:
            ExternalApiService.put(space_api_url, body, cls._get_request_header(),
                                   raise_exception_if_error=True)

        except BaseHTTPException as err:
            BrickService.log_brick_error(
                SpaceService, f"Can't register lab start on space. Error : {err.detail}")
            return False
        return True

    @classmethod
    def save_experiment(cls, project_id: str, save_experiment_dto: SaveExperimentToSpaceDTO) -> None:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/project/{project_id}/experiment")

        try:
            return ExternalApiService.put(space_api_url, save_experiment_dto, cls._get_request_header(),
                                          raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the experiment in space. Error : {err.detail}"
            raise err

    @classmethod
    def delete_experiment(cls, project_id: str, experiment_id: str) -> None:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/project/{project_id}/experiment/{experiment_id}")

        try:
            return ExternalApiService.delete(space_api_url, cls._get_request_header(),
                                             raise_exception_if_error=True)

        except BaseHTTPException as err:
            err.detail = f"Can't delete the experiment in space. Error : {err.detail}"
            raise err

    @classmethod
    def save_report(cls, project_id: str, report: SaveReportToSpaceDTO,
                    file_paths: List[str]) -> None:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/project/{project_id}/report/v2")

        # convert the file paths to file object supported by the form data request
        files = []
        for file_path in file_paths:
            file = open(file_path, 'rb')
            filename = FileHelper.get_name_with_extension(file_path)
            content_type = FileHelper.get_mime(file_path)
            files.append(('files', (filename, file, content_type)))

        try:
            return ExternalApiService.put_form_data(
                space_api_url, data=report,
                headers=cls._get_request_header(),
                files=files,
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the report in space. Error : {err.detail}"
            raise err

    @classmethod
    def delete_report(cls, project_id: str, report_id: str) -> None:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/project/{project_id}/report/{report_id}")
        try:
            return ExternalApiService.delete(space_api_url, cls._get_request_header(),
                                             raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't delete the report in space. Error : {err.detail}"
            raise err

    @classmethod
    def send_mail(cls, send_mail_dto: SpaceSendMailDTO) -> Response:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/send-mail")
        return ExternalApiService.post(space_api_url, send_mail_dto, cls._get_request_header(),
                                       raise_exception_if_error=True)

    #################################### SYNCHRONIZATION ####################################

    @classmethod
    def get_all_lab_projects(cls) -> List[SpaceProject]:
        """
        Call the space api to get the list of project for this lab
        """
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/project/all-trees")

        try:
            response = ExternalApiService.get(space_api_url, cls._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve projects for the lab. Error : {err.detail}"
            raise err

        # get response and parse it to a list of spaceProject
        return parse_obj_as(List[SpaceProject], response.json())

    @classmethod
    def get_all_lab_users(cls) -> List[UserFullDTO]:
        """
        Call the space api to get the list of users for this lab
        """
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/user")

        try:
            response = ExternalApiService.get(space_api_url, cls._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve users for the lab. Error : {err.detail}"
            raise err

        return UserFullDTO.from_json_list(response.json())

    @classmethod
    def _get_space_api_url(cls, route: str) -> str:
        """
        Build an URL to call the space API
        """

        space_api_url = Settings.get_space_api_url()
        if space_api_url is None:
            if Settings.is_dev_mode():
                raise BadRequestException(
                    "The space routes are desactivated in dev and test environment")
            else:
                raise BadRequestException(
                    'The space_API_URL environment variable is not set')
        return space_api_url + '/' + route

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

    # TODO TO REMOVE
    @classmethod
    def migrate_text_editor(cls, content: Any) -> Any:
        """
        Check the credential of an email/password by calling space, with 2Fa if needed
        """
        space_api_url: str = cls._get_space_api_url('lab-instances/migrate-quill-json')
        response = ExternalApiService.post(
            space_api_url, content, raise_exception_if_error=True)

        return response.json()
