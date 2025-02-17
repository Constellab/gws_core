

from typing import Dict, List, Literal, Optional

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
                                      SpaceSendMailDTO,
                                      SpaceSendMailToMailsDTO)
                                      SpaceSendMailDTO)
from gws_core.tag.tag import Tag
from gws_core.tag.tag_helper import TagHelper
from gws_core.user.user_dto import UserFullDTO, UserSpace
from requests.models import Response

from ..core.exception.exceptions import BadRequestException
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.settings import Settings
from ..folder.space_folder_dto import (ExternalSpaceCreateFolder,
                                       ExternalSpaceFolder,
                                       ExternalSpaceFolders)
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from ..user.user_credentials_dto import UserCredentials2Fa, UserCredentialsDTO


class ExternalCheckCredentialResponse(BaseModelDTO):
    status: Literal['OK', '2FA_REQUIRED']
    user: Optional[UserSpace] = None
    twoFAUrlCode: Optional[str] = None


class SpaceService():

    # external lab route on space
    _EXTERNAL_LABS_ROUTe: str= 'external-labs'
    AUTH_HEADER_KEY: str= 'Authorization'
    AUTH_API_KEY_HEADER_PREFIX: str= 'api-key'
    # Key to set the user in the request
    USER_ID_HEADER_KEY: str= 'User'

    ACCESS_TOKEN_HEADER= 'access-token'

    _access_token: Optional[str]= None

    def __init__(self, access_token: Optional[str] = None):
        """ Constructor of the SpaceService

        :param access_token: if access token is provided, it is used to authenticate.
        Otherwise the current user is used for authentication, defaults to None
        :type access_token: Optional[str], optional
        """
        self._access_token= access_token

    @ staticmethod
    def get_instance() -> 'SpaceService':
        """
        Return a new instance of the SpaceService that use the
        current user for authentication

        :return: a new instance of the SpaceService
        :rtype: SpaceService
        """
        return SpaceService()

    @ staticmethod
    def create_with_access_token() -> 'SpaceService':
        """
        Return a new instance of the SpaceService that use the
        access token for authentication

        :return: a new instance of the SpaceService
        :rtype: SpaceService
        """

        # for now we fake an access token.
        # In the future, the access token will be passed as parameter
        # It allow to add the header in the request to switch to a access token request
        return SpaceService('1')

    #################################### AUTHENTICATION ####################################

    def check_api_key(self, api_key: str) -> bool:

        # In local env, we don't check the api key
        if Settings.get_lab_environment() == 'LOCAL':
            return True

        if Settings.is_dev_mode():
            raise BadRequestException(
                "The space routes are desactivated in dev environment")

        space_api_key = Settings.get_space_api_key()
        return space_api_key == api_key

    def check_credentials(
            self, credentials: UserCredentialsDTO, for_login: bool = True) -> ExternalCheckCredentialResponse:
        """
        Check the credential of an email/password by calling space, with 2Fa if needed
        """
        route = 'check-credentials' if for_login else 'check-credentials-simple'
        space_api_url: str = self._get_space_api_url(
            f'{self._EXTERNAL_LABS_ROUTe}/{route}')
        response = ExternalApiService.post(
            space_api_url, credentials, headers=self._get_request_header(),
            raise_exception_if_error=True)

        return ExternalCheckCredentialResponse.from_json(response.json())

    def check_2_fa(self, credentials: UserCredentials2Fa) -> UserSpace:
        """
        Check the credential of an email/password by calling space
        and return true if ok
        """
        space_api_url: str = self._get_space_api_url(
            'auth/external/check-2fa')
        response = ExternalApiService.post(
            space_api_url, credentials, raise_exception_if_error=True)

        return UserSpace.from_json(response.json())

    def register_lab_start(self, lab_config: LabConfigModelDTO) -> bool:
        """
        Call the space api to mark the lab as started
        """
        self._check_dev_mode()
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/start")

        body = LabStartDTO(lab_config=lab_config)

        try:
            ExternalApiService.put(space_api_url, body, self._get_request_header(),
                                   raise_exception_if_error=True)

        except BaseHTTPException as err:
            BrickService.log_brick_error(
                SpaceService, f"Can't register lab start on space. Error : {err.detail}")
            return False
        return True

    #################################### SCENARIO ####################################

    def save_scenario(self, folder_id: str, save_scenario_dto: SaveScenarioToSpaceDTO) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{folder_id}/scenario")

        try:
            return ExternalApiService.put(space_api_url, save_scenario_dto, self._get_request_header(),
                                          raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the scenario in space. Error : {err.detail}"
            raise err

    def delete_scenario(self, folder_id: str, scenario_id: str) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{folder_id}/scenario/{scenario_id}")

        try:
            return ExternalApiService.delete(space_api_url, self._get_request_header(),
                                             raise_exception_if_error=True)

        except BaseHTTPException as err:
            err.detail = f"Can't delete the scenario in space. Error : {err.detail}"
            raise err

    def update_scenario_folder(self, current_folder_id: str, scenario_id: str, new_folder_id: str) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{current_folder_id}/scenario/{scenario_id}/folder/{new_folder_id}")

        try:
            return ExternalApiService.put(space_api_url, None,
                                          self._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't update the scenario folder in space. Error : {err.detail}"
            raise err

    #################################### NOTE ####################################

    def save_note(self, folder_id: str, note: SaveNoteToSpaceDTO,
                  file_paths: List[str]) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{folder_id}/note/v2")

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
                headers=self._get_request_header(),
                files=files,
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't save the note in space. Error : {err.detail}"
            raise err

    def delete_note(self, folder_id: str, note_id: str) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{folder_id}/note/{note_id}")
        try:
            return ExternalApiService.delete(space_api_url, self._get_request_header(),
                                             raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't delete the note in space. Error : {err.detail}"
            raise err

    def update_note_folder(self, current_folder_id: str, note_id: str, new_folder_id: str) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{current_folder_id}/note/{note_id}/folder/{new_folder_id}")

        try:
            a = ExternalApiService.put(space_api_url, None,
                                       self._get_request_header(), raise_exception_if_error=True)
            return a
        except BaseHTTPException as err:
            err.detail = f"Can't update the note folder in space. Error : {err.detail}"
            raise err

    def get_modifications(
            self, old_content: RichTextDTO, new_content: RichTextDTO,
            old_modifications: Optional[RichTextModificationsDTO] = None) -> RichTextModificationsDTO:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/rich-text/compare")
        try:
            response = ExternalApiService.post(space_api_url, {
                'oldContent': old_content.to_json_dict(),
                'newContent': new_content.to_json_dict(),
                'oldModifications': old_modifications.to_json_dict() if old_modifications else None,
                'userId': CurrentUserService.get_current_user().id
            }, self._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err
        return RichTextModificationsDTO.from_json(response.json())

    def get_undo_content(self, content: RichTextDTO, modifications: RichTextModificationsDTO,
                         modification_id: str) -> RichTextDTO:
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/rich-text/previous-version")
        try:
            response = ExternalApiService.post(space_api_url, {
                'content': content.to_json_dict(),
                'modifications': modifications.to_json_dict(),
                'modificationId': modification_id,
            }, self._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err
        return RichTextDTO.from_json(response.json())

    #################################### RESOURCE ####################################

    def share_resource(self, folder_id: str, resource_dto: ShareResourceWithSpaceDTO) -> None:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{folder_id}/resource")

        try:
            return ExternalApiService.put(space_api_url, resource_dto, self._get_request_header(),
                                          raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't share the resource in space. Error : {err.detail}"
            raise err

    #################################### FOLDER ####################################

    def get_all_lab_folders(self) -> ExternalSpaceFolders:
        """
        Call the space api to get the list of folder for this lab
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/all-trees")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folders for the lab. Error : {err.detail}"
            raise err

        # get response and parse it to a list of spaceFolder
        root_folders = ExternalSpaceFolder.from_json_list(response.json())
        return ExternalSpaceFolders(folders=root_folders)

    def get_lab_root_folder(self, id_: str) -> ExternalSpaceFolder:
        """
        Call the space api to get the a folder for this lab
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(f"{self._EXTERNAL_LABS_ROUTe}/folder/{id_}/root-tree")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folder for the lab. Error : {err.detail}"
            raise err

        # get response and parse it to a list of spaceFolder
        return ExternalSpaceFolder.from_json(response.json())

    def create_root_folder(self, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """
        Call the space api to create a root folder
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder")

        try:
            response = ExternalApiService.post(space_api_url, folder.to_dto(), self._get_request_header(),
                                               raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't create root folder. Error : {err.detail}"
            raise err

        return ExternalSpaceFolder.from_json(response.json())

    def create_child_folder(self, parent_id: str, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """
        Call the space api to create a child folder
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/folder/{parent_id}")

        try:
            response = ExternalApiService.post(space_api_url, folder.to_dto(), self._get_request_header(),
                                               raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't create child folder. Error : {err.detail}"
            raise err

        return ExternalSpaceFolder.from_json(response.json())

    ############################################# ENTITY #############################################

    def add_tags_to_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """
        Call the space api to create a child folder
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/hierarchyObject/{entity_id}/tags/multiple")

        try:
            tags_dto = [tag.to_dto() for tag in tags]
            response = ExternalApiService.post(space_api_url, {
                'tags': tags_dto
            }, self._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't add tags to object. Error : {err.detail}"
            raise err

        return TagHelper.tags_dict_to_list(response.json())

    def add_or_replace_tags_on_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """
        Call the space api to create a child folder
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/hierarchyObject/{entity_id}/tags/createOrReplace")

        try:
            tags_dto = [tag.to_dto() for tag in tags]
            response = ExternalApiService.post(space_api_url, {
                'tags': tags_dto
            }, self._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't add or replace tags on object. Error : {err.detail}"
            raise err

        return TagHelper.tags_dict_to_list(response.json())

    def delete_tags_on_object(self, entity_id: str, tags: List[Tag]) -> None:
        """
        Call the space api to create a child folder
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/hierarchyObject/{entity_id}/tags/delete")

        try:
            tags_dto = [tag.to_dto() for tag in tags]
            ExternalApiService.post(space_api_url, {
                'tags': tags_dto
            }, self._get_request_header(),
                raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't delete tags on object. Error : {err.detail}"
            raise err

    #################################### USER ####################################

    def get_all_lab_users(self) -> List[UserFullDTO]:
        """
        Call the space api to get the list of users for this lab
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/user")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve users for the lab. Error : {err.detail}"
            raise err

        return UserFullDTO.from_json_list(response.json())

    def get_user_info(self, user_id: str) -> UserFullDTO:
        """
        Call the space api to get the user info
        """
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/user/{user_id}")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve user info. Error : {err.detail}"
            raise err

        return UserFullDTO.from_json(response.json())

    #################################### MAIL ####################################

    def send_mail(self, send_mail_dto: SpaceSendMailDTO) -> Response:
        self._check_dev_mode()

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTe}/send-mail")
        return ExternalApiService.post(space_api_url, send_mail_dto, self._get_request_header(),
                                       raise_exception_if_error=True)

    @classmethod
    def send_mail_to_mails(cls, send_mail_to_mails_dto: SpaceSendMailToMailsDTO) -> Response:
        cls._check_dev_mode()

        space_api_url: str = cls._get_space_api_url(
            f"{cls._external_labs_route}/send-mail-to-mails")
        return ExternalApiService.post(space_api_url, send_mail_to_mails_dto, cls._get_request_header(),
                                       raise_exception_if_error=True)

    #################################### OTHER ####################################
    def _check_dev_mode(self) -> None:
        if Settings.is_dev_mode():
            raise BadRequestException(
                "The action is disabled in dev environment")

    def _get_space_api_url(self, route: str) -> str:
        """
        Build an URL to call the space API
        """

        space_api_url = Settings.get_space_api_url()
        return space_api_url + '/' + route

    def _get_request_header(self) -> Dict[str, str]:
        """
        Return the header for a request to space, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {self.AUTH_HEADER_KEY: self.AUTH_API_KEY_HEADER_PREFIX +
                   ' ' + Settings.get_space_api_key()}

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[self.USER_ID_HEADER_KEY] = user.id

        if self._access_token:
            headers[self.ACCESS_TOKEN_HEADER] = self._access_token

        return headers
