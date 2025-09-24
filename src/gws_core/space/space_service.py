

import json
from typing import List, Literal, Optional

from fastapi.encoders import jsonable_encoder
from requests.models import Response

from gws_core.brick.brick_service import BrickService
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.rich_text_modification import \
    RichTextModificationsDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.space.space_dto import (LabStartDTO, SaveNoteToSpaceDTO,
                                      SaveScenarioToSpaceDTO,
                                      ShareResourceWithSpaceDTO,
                                      SpaceHierarchyObjectDTO,
                                      SpaceRootFolderUserRole,
                                      SpaceSendMailToMailsDTO,
                                      SpaceSendMailToUsersDTO,
                                      SpaceSendNotificationDTO,
                                      SpaceSyncObjectDTO)
from gws_core.space.space_service_base import SpaceServiceBase
from gws_core.tag.tag import Tag
from gws_core.tag.tag_helper import TagHelper
from gws_core.user.user_dto import UserFullDTO, UserSpace

from ..core.exception.exceptions import BadRequestException
from ..core.service.external_api_service import ExternalApiService, FormData
from ..core.utils.settings import Settings
from ..folder.space_folder_dto import (ExternalSpaceCreateFolder,
                                       ExternalSpaceFolder,
                                       ExternalSpaceFolders)
from ..user.current_user_service import CurrentUserService
from ..user.user_credentials_dto import UserCredentials2Fa, UserCredentialsDTO


class ExternalCheckCredentialResponse(BaseModelDTO):
    status: Literal['OK', '2FA_REQUIRED']
    user: Optional[UserSpace] = None
    twoFAUrlCode: Optional[str] = None


class SpaceService(SpaceServiceBase):

    # external lab route on space
    _EXTERNAL_LABS_ROUTE: str = 'external-labs'

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
            f'{self._EXTERNAL_LABS_ROUTE}/{route}')
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
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/start")

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

    def save_scenario(self, folder_id: str, save_scenario_dto: SaveScenarioToSpaceDTO) -> SpaceHierarchyObjectDTO:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}/scenario")

        try:
            response = ExternalApiService.put(space_api_url, save_scenario_dto, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceHierarchyObjectDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't save the scenario in space. Error : {err.detail}"
            raise err

    def delete_scenario(self, folder_id: str, scenario_id: str) -> None:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}/scenario/{scenario_id}")

        try:
            ExternalApiService.delete(space_api_url, self._get_request_header(),
                                      raise_exception_if_error=True)

        except BaseHTTPException as err:
            err.detail = f"Can't delete the scenario in space. Error : {err.detail}"
            raise err

    def update_scenario_folder(self, current_folder_id: str, scenario_id: str, new_folder_id: str) -> None:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{current_folder_id}/scenario/{scenario_id}/folder/{new_folder_id}")

        try:
            ExternalApiService.put(space_api_url, None,
                                   self._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't update the scenario folder in space. Error : {err.detail}"
            raise err

    def get_synced_scenarios(self) -> List[SpaceSyncObjectDTO]:
        """ Get the list of scenarios synced with space
        """
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/scenario/sync")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceSyncObjectDTO.from_json_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't get scenario sync. Error : {err.detail}"
            raise err

    #################################### NOTE ####################################

    def save_note(self, folder_id: str, note: SaveNoteToSpaceDTO,
                  form_data: FormData) -> SpaceHierarchyObjectDTO:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}/note/v2")

        try:
            body = {"body": json.dumps(jsonable_encoder(note))}
            response = ExternalApiService.put_form_data(
                space_api_url,
                form_data=form_data,
                data=body,
                headers=self._get_request_header(),
                raise_exception_if_error=True)
            return SpaceHierarchyObjectDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't save the note in space. Error : {err.detail}"
            raise err

    def delete_note(self, folder_id: str, note_id: str) -> None:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}/note/{note_id}")
        try:
            ExternalApiService.delete(space_api_url, self._get_request_header(),
                                      raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't delete the note in space. Error : {err.detail}"
            raise err

    def update_note_folder(self, current_folder_id: str, note_id: str, new_folder_id: str) -> None:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{current_folder_id}/note/{note_id}/folder/{new_folder_id}")

        try:
            ExternalApiService.put(space_api_url, None,
                                   self._get_request_header(), raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't update the note folder in space. Error : {err.detail}"
            raise err

    def get_modifications(
            self, old_content: RichTextDTO, new_content: RichTextDTO,
            old_modifications: Optional[RichTextModificationsDTO] = None) -> RichTextModificationsDTO:

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/rich-text/compare")
        try:
            response = ExternalApiService.post(space_api_url, {
                'oldContent': old_content.to_json_dict(),
                'newContent': new_content.to_json_dict(),
                'oldModifications': old_modifications.to_json_dict() if old_modifications else None,
                'userId': CurrentUserService.get_current_user().id
            }, self._get_request_header(), raise_exception_if_error=True)
            return RichTextModificationsDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err

    def get_undo_content(self, content: RichTextDTO, modifications: RichTextModificationsDTO,
                         modification_id: str) -> RichTextDTO:
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/rich-text/previous-version")
        try:
            response = ExternalApiService.post(space_api_url, {
                'content': content.to_json_dict(),
                'modifications': modifications.to_json_dict(),
                'modificationId': modification_id,
            }, self._get_request_header(), raise_exception_if_error=True)
            return RichTextDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't get note modifications. Error : {err.detail}"
            raise err

    def get_synced_notes(self) -> List[SpaceSyncObjectDTO]:
        """ Get the list of notes synced with space
        """
        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/note/sync")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceSyncObjectDTO.from_json_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't get note sync. Error : {err.detail}"
            raise err

    #################################### RESOURCE ####################################

    def share_resource(self, folder_id: str, resource_dto: ShareResourceWithSpaceDTO) -> SpaceHierarchyObjectDTO:
        """Share a resource in a folder in space. Only the resource link is shared, not the resource itself.
        After this, the resource is available in the space folder if this lab is up and running.

        :param folder_id:
        :type folder_id: str
        :param resource_dto: _description_
        :type resource_dto: ShareResourceWithSpaceDTO
        :raises err: _description_
        :return: None
        :rtype: _type_
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}/resource")

        try:
            response = ExternalApiService.put(space_api_url, resource_dto, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceHierarchyObjectDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't share the resource in space. Error : {err.detail}"
            raise err

    #################################### FOLDER ####################################

    def get_all_lab_root_folders(self) -> ExternalSpaceFolders:
        """ Get all the folder trees (from root) accessible by the lab

        :return: list of folder trees
        :rtype: ExternalSpaceFolders
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/all-trees")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)

            # get response and parse it to a list of spaceFolder
            root_folders = ExternalSpaceFolder.from_json_list(response.json())
            return ExternalSpaceFolders(folders=root_folders)

        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folders for the lab. Error : {err.detail}"
            raise err

    def get_lab_root_folder(self, id_: str) -> ExternalSpaceFolder:
        """ Get the root folder tree information.
        The folder must be accessible by the lab.

        :param id_: id of the root folder
        :type id_: str
        :return: the root folder tree
        :rtype: ExternalSpaceFolder
        """

        space_api_url: str = self._get_space_api_url(f"{self._EXTERNAL_LABS_ROUTE}/folder/{id_}/root-tree")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            # get response and parse it to a list of spaceFolder
            return ExternalSpaceFolder.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folder for the lab. Error : {err.detail}"
            raise err

    def create_root_folder(self, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """ Create a root folder in the lab space.
        The root folder will be shared to the current user and mark as created by the current user.

        :param folder: folder information
        :type folder: ExternalSpaceCreateFolder
        :return: the created folder
        :rtype: ExternalSpaceFolder
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder")

        try:
            response = ExternalApiService.post(space_api_url, folder.to_dto(), self._get_request_header(),
                                               raise_exception_if_error=True)
            return ExternalSpaceFolder.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't create root folder. Error : {err.detail}"
            raise err

    def create_child_folder(self, parent_id: str, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """ Create a child folder in the lab space.

        :param parent_id: id of the parent folder
        :type parent_id: str
        :param folder: folder information
        :type folder: ExternalSpaceCreateFolder
        :return: the created folder
        :rtype: ExternalSpaceFolder
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{parent_id}")

        try:
            response = ExternalApiService.post(space_api_url, folder.to_dto(), self._get_request_header(),
                                               raise_exception_if_error=True)
            return ExternalSpaceFolder.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't create child folder. Error : {err.detail}"
            raise err

    def update_folder(self, folder_id: str, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """ Update a folder in the lab space.

        :param folder_id: id of the folder
        :type folder_id: str
        :param folder: folder information
        :type folder: ExternalSpaceCreateFolder
        :return: the updated folder
        :rtype: ExternalSpaceFolder
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{folder_id}")

        try:
            response = ExternalApiService.put(space_api_url, folder.to_dto(), self._get_request_header(),
                                              raise_exception_if_error=True)
            return ExternalSpaceFolder.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't update folder. Error : {err.detail}"
            raise err

    def share_root_folder(self, root_folder_id: str, group_id: str,
                          role: SpaceRootFolderUserRole = SpaceRootFolderUserRole.USER) -> None:
        """Share a root folder with a group

        :param root_folder_id: id of the root folder
        :type root_folder_id: str
        :param group_id: id of the group (can be a user id or a team id)
        :type group_id: str
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{root_folder_id}/share/{group_id}/role/{role.value}")

        try:
            ExternalApiService.put(space_api_url, None, self._get_request_header(),
                                   raise_exception_if_error=True)
        except BaseHTTPException as err:
            err.detail = f"Can't share root folder. Error : {err.detail}"
            raise err

    def share_root_folder_with_current_lab(self, root_folder_id: str) -> ExternalSpaceFolder:
        """Share a root folder with the current lab

        :param root_folder_id: id of the root folder
        :type root_folder_id: str
        :return: the shared root folder
        :rtype: ExternalSpaceFolder
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/{root_folder_id}/lab/current")

        try:
            response = ExternalApiService.put(space_api_url, None, self._get_request_header(),
                                              raise_exception_if_error=True)
            return ExternalSpaceFolder.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't share root folder with current lab. Error : {err.detail}"
            raise err

    def get_all_current_user_root_folders(self) -> List[SpaceHierarchyObjectDTO]:
        """ Get all the root folders accessible by the current user

        :return: list of root folders
        :rtype: List[SpaceHierarchyObjectDTO]
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/folder/user/current")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return SpaceHierarchyObjectDTO.from_json_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve folders for the lab. Error : {err.detail}"
            raise err

    ############################################# ENTITY #############################################

    def add_tags_to_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """ Add tags to a folder object in space. The tags are created if they don't exist.
        It does not replace tags with the same key (use add_or_replace_tags_on_object for that).

        :param entity_id: id of the object (folder, scenario, document, note, resource...)
        :type entity_id: str
        :param tags: list of tags to add
        :type tags: List[Tag]
        :return: the list of tags added
        :rtype: List[Tag]
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/hierarchyObject/{entity_id}/tags/multiple")

        try:
            tags_dto = [tag.to_dto() for tag in tags]
            response = ExternalApiService.post(space_api_url, {
                'tags': tags_dto
            }, self._get_request_header(),
                raise_exception_if_error=True)
            return TagHelper.tags_dict_to_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't add tags to object. Error : {err.detail}"
            raise err

    def add_or_replace_tags_on_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """ Add or replace tags on a folder object in space. The tags are created if they don't exist.
        If a tag with the same key exists, it is replaced by the new tag.

        :param entity_id: id of the object (folder, scenario, document, note, resource...)
        :type entity_id: str
        :param tags: list of tags to add or replace
        :type tags: List[Tag]
        :return: the list of tags added or replaced
        :rtype: List[Tag]
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/hierarchyObject/{entity_id}/tags/createOrReplace")

        try:
            tags_dto = [tag.to_dto() for tag in tags]
            response = ExternalApiService.post(space_api_url, {
                'tags': tags_dto
            }, self._get_request_header(),
                raise_exception_if_error=True)
            return TagHelper.tags_dict_to_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't add or replace tags on object. Error : {err.detail}"
            raise err

    def delete_tags_on_object(self, entity_id: str, tags: List[Tag]) -> None:
        """ Delete tags on a folder object in space.

        :param entity_id: id of the object (folder, scenario, document, note, resource...)
        :type entity_id: str
        :param tags: list of tags to delete
        :type tags: List[Tag]
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/hierarchyObject/{entity_id}/tags/delete")

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
        """ Get all the users of the lab

        :return: list of users
        :rtype: List[UserFullDTO]
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/user")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return UserFullDTO.from_json_list(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve users for the lab. Error : {err.detail}"
            raise err

    def get_user_info(self, user_id: str) -> UserFullDTO:
        """ Get the information of a user. The user must be in the same space as the lab.

        :param user_id: id of the user
        :type user_id: str
        :return: the user information
        :rtype: UserFullDTO
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/user/{user_id}")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return UserFullDTO.from_json(response.json())
        except BaseHTTPException as err:
            err.detail = f"Can't retrieve user info. Error : {err.detail}"
            raise err

    #################################### MAIL ####################################

    def send_mail(self, send_mail_dto: SpaceSendMailToUsersDTO) -> Response:
        """Send a mail to a list of users. To send a custom mail,
        use the template 'generic' and provide mail content in the data.

        :param send_mail_dto: mail information
        :type send_mail_dto: SpaceSendMailToUsersDTO
        :return: http response
        :rtype: Response
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/send-mail")
        return ExternalApiService.post(space_api_url, send_mail_dto, self._get_request_header(),
                                       raise_exception_if_error=True)

    def send_mail_to_mails(self, send_mail_to_mails_dto: SpaceSendMailToMailsDTO) -> Response:
        """ Send a mail to a list of mails. To send a custom mail,
        use the template 'generic' and provide mail content in the data.

        :param send_mail_to_mails_dto: mail information
        :type send_mail_to_mails_dto: SpaceSendMailToMailsDTO
        :return: http response
        :rtype: Response
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/send-mail-to-mails")
        return ExternalApiService.post(space_api_url, send_mail_to_mails_dto, self._get_request_header(),
                                       raise_exception_if_error=True)

    def send_notification(self, send_notification_dto: SpaceSendNotificationDTO) -> Response:
        """Send a notification to a list of users in a space

        :param send_notification_dto: notification information
        :type send_notification_dto: SpaceSendNotificationDTO
        :return: http response
        :rtype: Response
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/send-notification")
        return ExternalApiService.post(space_api_url, send_notification_dto, self._get_request_header(),
                                       raise_exception_if_error=True)

    ############################################## OTHER ##############################################

    def get_reflex_access_token(self) -> str:
        """ Get the reflex access token

        :return: the reflex access token
        :rtype: str
        """

        space_api_url: str = self._get_space_api_url(
            f"{self._EXTERNAL_LABS_ROUTE}/reflex-access_token")

        try:
            response = ExternalApiService.get(space_api_url, self._get_request_header(),
                                              raise_exception_if_error=True)
            return response.json().get('reflexAccessToken')

        except BaseHTTPException as err:
            err.detail = f"Can't retrieve reflex access token for the lab. Error : {err.detail}"
            raise err
