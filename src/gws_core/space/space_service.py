

from typing import Any, Dict, List, Literal, Optional

from requests.models import Response

from gws_core.brick.brick_service import BrickService
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text_types import (RichTextDTO,
                                                     RichTextModificationsDTO)
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.space.space_dto import (LabStartDTO, SaveNoteToSpaceDTO,
                                      SaveScenarioToSpaceDTO,
                                      ShareResourceWithSpaceDTO,
                                      SpaceSendMailDTO)
from gws_core.user.user_dto import UserFullDTO, UserSpace

from ..core.exception.exceptions import BadRequestException
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..folder.space_folder_dto import ExternalSpaceFolder, ExternalSpaceFolders
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from ..user.user_credentials_dto import UserCredentials2Fa, UserCredentialsDTO


class ExternalCheckCredentialResponse(BaseModelDTO):
    status: Literal['OK', '2FA_REQUIRED']
    user: Optional[UserSpace] = None
    twoFAUrlCode: Optional[str] = None


class SpaceService():

    # external lab route on space
    _external_labs_route: str = 'external-labs'
    api_key_header_key: str = 'Authorization'
    api_key_header_prefix: str = 'api-key'
    # Key to set the user in the request
    user_id_header_key: str = 'User'

    #################################### AUTHENTICATION ####################################

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
            space_api_url, credentials, headers=cls._get_request_header(),
            raise_exception_if_error=True)

        return ExternalCheckCredentialResponse.from_json(response.json())

    @classmethod
    def check_2_fa(cls, credentials: UserCredentials2Fa) -> UserSpace:
        """
        Check the credential of an email/password by calling space
        and return true if ok
        """
        space_api_url: str = cls._get_space_api_url(
            'auth/external/check-2fa')
        response = ExternalApiService.post(
            space_api_url, credentials, raise_exception_if_error=True)

        return UserSpace.from_json(response.json())

    @classmethod
    def register_lab_start(cls, lab_config: LabConfigModelDTO) -> bool:
        """
        Call the space api to mark the lab as started
        """
        cls._check_dev_mode()
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

    #################################### SCENARIO ####################################

    @classmethod
    def save_scenario(cls, folder_id: str, save_scenario_dto: SaveScenarioToSpaceDTO) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{folder_id}/scenario")

        try:
            return ExternalApiService.put(space_api_url, save_scenario_dto, cls._get_request_header(),
                                          raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the scenario in space. Error : {err.detail}"
            raise err

    @classmethod
    def delete_scenario(cls, folder_id: str, scenario_id: str) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{folder_id}/scenario/{scenario_id}")

        try:
            return ExternalApiService.delete(space_api_url, cls._get_request_header(),
                                             raise_exception_if_error=True)

        except BaseHTTPException as err:
            err.detail = f"Can't delete the scenario in space. Error : {err.detail}"
            raise err

    @classmethod
    def update_scenario_folder(cls, current_folder_id: str, scenario_id: str, new_folder_id: str) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{current_folder_id}/scenario/{scenario_id}/folder/{new_folder_id}")

        try:
            return ExternalApiService.put(space_api_url, None,
                                          cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't update the scenario folder in space. Error : {err.detail}"
            raise err

    #################################### NOTE ####################################
    @classmethod
    def save_note(cls, folder_id: str, note: SaveNoteToSpaceDTO,
                  file_paths: List[str]) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{folder_id}/note/v2")

        # convert the file paths to file object supported by the form data request
        files = []
        for file_path in file_paths:
            file = open(file_path, 'rb')
            filename = FileHelper.get_name_with_extension(file_path)
            content_type = FileHelper.get_mime(file_path)
            files.append(('files', (filename, file, content_type)))

        try:
            return ExternalApiService.put_form_data(
                space_api_url, data=note,
                headers=cls._get_request_header(),
                files=files,
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the note in space. Error : {err.detail}"
            raise err

    @classmethod
    def delete_note(cls, folder_id: str, note_id: str) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{folder_id}/note/{note_id}")
        try:
            return ExternalApiService.delete(space_api_url, cls._get_request_header(),
                                             raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't delete the note in space. Error : {err.detail}"
            raise err

    @classmethod
    def update_note_folder(cls, current_folder_id: str, note_id: str, new_folder_id: str) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{current_folder_id}/note/{note_id}/folder/{new_folder_id}")

        try:
            a = ExternalApiService.put(space_api_url, None,
                                       cls._get_request_header(), raise_exception_if_error=True)
            return a
        except BaseHTTPException as err:
            err.detail = f"Can't update the note folder in space. Error : {err.detail}"
            raise err

    @classmethod
    def get_modifications(
            cls, old_content: RichTextDTO, new_content: RichTextDTO,
            old_modifications: Optional[RichTextModificationsDTO] = None) -> RichTextModificationsDTO:

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/rich-text/compare")
        try:
            response = ExternalApiService.post(space_api_url, {
                'oldContent': old_content.to_json_dict(),
                'newContent': new_content.to_json_dict(),
                'oldModifications': old_modifications.to_json_dict() if old_modifications else None,
                'userId': CurrentUserService.get_current_user().id
            }, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err
        return RichTextModificationsDTO.from_json(response.json())

    @classmethod
    def get_undo_content(cls, content: RichTextDTO, modifications: RichTextModificationsDTO,
                         modification_id: str) -> RichTextDTO:
        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/rich-text/previous-version")
        try:
            response = ExternalApiService.post(space_api_url, {
                'content': content.to_json_dict(),
                'modifications': modifications.to_json_dict(),
                'modificationId': modification_id,
            }, cls._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err
        return RichTextDTO.from_json(response.json())

    #################################### RESOURCE ####################################

    @classmethod
    def share_resource(cls, folder_id: str, resource_dto: ShareResourceWithSpaceDTO) -> None:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/{folder_id}/resource")

        try:
            return ExternalApiService.put(space_api_url, resource_dto, cls._get_request_header(),
                                          raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't share the resource in space. Error : {err.detail}"
            raise err

    #################################### SYNCHRONIZATION ####################################

    @classmethod
    def get_all_lab_folders(cls) -> ExternalSpaceFolders:
        """
        Call the space api to get the list of folder for this lab
        """
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/folder/all-trees")

        try:
            response = ExternalApiService.get(space_api_url, cls._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folders for the lab. Error : {err.detail}"
            raise err

        # get response and parse it to a list of spaceFolder
        root_folders = ExternalSpaceFolder.from_json_list(response.json())
        return ExternalSpaceFolders(folders=root_folders)

    @classmethod
    def get_lab_root_folder(cls, id_: str) -> ExternalSpaceFolder:
        """
        Call the space api to get the a folder for this lab
        """
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(f"{cls._external_labs_route}/folder/{id_}/root-tree")

        try:
            response = ExternalApiService.get(space_api_url, cls._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folder for the lab. Error : {err.detail}"
            raise err

        # get response and parse it to a list of spaceFolder
        return ExternalSpaceFolder.from_json(response.json())

    @classmethod
    def get_all_lab_users(cls) -> List[UserFullDTO]:
        """
        Call the space api to get the list of users for this lab
        """
        cls._check_dev_mode()

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
    def get_user_info(cls, user_id: str) -> UserFullDTO:
        """
        Call the space api to get the user info
        """
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/user/{user_id}")

        try:
            response = ExternalApiService.get(space_api_url, cls._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve user info. Error : {err.detail}"
            raise err

        return UserFullDTO.from_json(response.json())

    #################################### OTHER ####################################

    @classmethod
    def send_mail(cls, send_mail_dto: SpaceSendMailDTO) -> Response:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/send-mail")
        return ExternalApiService.post(space_api_url, send_mail_dto, cls._get_request_header(),
                                       raise_exception_if_error=True)

    @classmethod
    def _check_dev_mode(cls) -> None:
        pass
        # if Settings.is_dev_mode():
        #     raise BadRequestException(
        #         "The action is disabled in dev environment")

    @classmethod
    def _get_space_api_url(cls, route: str) -> str:
        """
        Build an URL to call the space API
        """

        space_api_url = Settings.get_space_api_url()
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
