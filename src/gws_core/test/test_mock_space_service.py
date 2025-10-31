"""
Mock SpaceService for testing purposes.
This mock class overrides SpaceService methods to avoid making actual API calls during tests.
"""

from typing import List
from unittest.mock import Mock

from gws_core.core.service.external_api_service import FormData
from gws_core.core.utils.string_helper import StringHelper
from gws_core.folder.space_folder_dto import (ExternalSpaceCreateFolder,
                                              ExternalSpaceFolder,
                                              ExternalSpaceFolders)
from gws_core.impl.rich_text.rich_text_modification import \
    RichTextModificationsDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.space.space_dto import (SaveNoteToSpaceDTO,
                                      SaveScenarioToSpaceDTO,
                                      ShareResourceWithSpaceDTO,
                                      SpaceHierarchyObjectDTO,
                                      SpaceHierarchyObjectType,
                                      SpaceRootFolderUserRole,
                                      SpaceSendMailToMailsDTO,
                                      SpaceSendMailToUsersDTO,
                                      SpaceSendNotificationDTO,
                                      SpaceSyncObjectDTO)
from gws_core.space.space_service import (ExternalCheckCredentialResponse,
                                          SpaceService)
from gws_core.tag.tag import Tag
from gws_core.user.user_credentials_dto import (UserCredentials2Fa,
                                                UserCredentialsDTO)
from gws_core.user.user_dto import (UserFullDTO, UserLanguage, UserSpace,
                                    UserTheme)
from gws_core.user.user_group import UserGroup
from requests.models import Response


class TestMockSpaceService(SpaceService):
    """
    Mock implementation of SpaceService for testing.
    All methods return mock data instead of making actual API calls.
    """

    # ==================== AUTHENTICATION ====================

    def check_api_key(self, api_key: str) -> bool:
        """Mock check_api_key - always returns True"""
        return True

    def check_credentials(self, credentials: UserCredentialsDTO, for_login: bool = True):
        """Mock check_credentials - returns mock response"""
        return ExternalCheckCredentialResponse(
            status='OK',
            user=UserSpace(
                id=StringHelper.generate_uuid(),
                firstname='Mock',
                lastname='User',
                email='mock@example.com',
                theme=UserTheme.LIGHT_THEME,
                lang=UserLanguage.EN,
                photo=None
            )
        )

    def check_2_fa(self, credentials: UserCredentials2Fa) -> UserSpace:
        """Mock check_2_fa - returns mock UserSpace"""
        return UserSpace(
            id=StringHelper.generate_uuid(),
            firstname='Mock',
            lastname='User',
            email='mock@example.com',
            theme=UserTheme.LIGHT_THEME,
            lang=UserLanguage.EN,
            photo=None
        )

    def register_lab_start(self, lab_config: LabConfigModelDTO) -> bool:
        """Mock register_lab_start - always returns True"""
        return True

    # ==================== SCENARIO ====================

    def save_scenario(self, folder_id: str, save_scenario_dto: SaveScenarioToSpaceDTO) -> SpaceHierarchyObjectDTO:
        """Mock save_scenario"""
        return SpaceHierarchyObjectDTO(
            id=save_scenario_dto.scenario.id,
            name=save_scenario_dto.scenario.title,
            objectType=SpaceHierarchyObjectType.SCENARIO,
            parentId=folder_id
        )

    def delete_scenario(self, folder_id: str, scenario_id: str) -> None:
        """Mock delete_scenario"""
        pass

    def update_scenario_folder(self, current_folder_id: str, scenario_id: str, new_folder_id: str) -> None:
        """Mock update_scenario_folder"""
        pass

    def get_synced_scenarios(self) -> List[SpaceSyncObjectDTO]:
        """Mock get_synced_scenarios - returns empty list"""
        return []

    # ==================== NOTE ====================

    def save_note(self, folder_id: str, note: SaveNoteToSpaceDTO, form_data: FormData) -> SpaceHierarchyObjectDTO:
        """Mock save_note"""
        return SpaceHierarchyObjectDTO(
            id=note.note.id,
            name=note.note.title,
            objectType=SpaceHierarchyObjectType.NOTE,
            parentId=folder_id
        )

    def delete_note(self, folder_id: str, note_id: str) -> None:
        """Mock delete_note"""
        pass

    def update_note_folder(self, current_folder_id: str, note_id: str, new_folder_id: str) -> None:
        """Mock update_note_folder"""
        pass

    def get_modifications(self, old_content: RichTextDTO, new_content: RichTextDTO,
                          old_modifications: RichTextModificationsDTO = None) -> RichTextModificationsDTO:
        """Mock get_modifications"""
        return RichTextModificationsDTO(version=1, modifications=[])

    def get_undo_content(self, content: RichTextDTO, modifications: RichTextModificationsDTO,
                         modification_id: str) -> RichTextDTO:
        """Mock get_undo_content"""
        return content

    def get_synced_notes(self) -> List[SpaceSyncObjectDTO]:
        """Mock get_synced_notes - returns empty list"""
        return []

    # ==================== RESOURCE ====================

    def share_resource(self, folder_id: str, resource_dto: ShareResourceWithSpaceDTO) -> SpaceHierarchyObjectDTO:
        """Mock share_resource"""
        return SpaceHierarchyObjectDTO(
            id=resource_dto.resource_id,
            name=resource_dto.name,
            objectType=SpaceHierarchyObjectType.RESOURCE,
            parentId=folder_id
        )

    # ==================== FOLDER ====================

    def get_all_lab_root_folders(self) -> ExternalSpaceFolders:
        """Mock get_all_lab_root_folders - returns empty folders"""
        return ExternalSpaceFolders(folders=[])

    def get_lab_root_folder(self, id_: str) -> ExternalSpaceFolder:
        """Mock get_lab_root_folder"""
        return ExternalSpaceFolder(
            id=id_,
            name='Mock Root Folder',
            code='MOCK_FOLDER',
            tags=[],
            starting_date=None,
            ending_date=None,
            children=[]
        )

    def create_root_folder(self, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """Mock create_root_folder that returns a fake folder"""
        return ExternalSpaceFolder(
            id=StringHelper.generate_uuid(),
            name=folder.name,
            children=[]
        )

    def create_child_folder(self, parent_id: str, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """Mock create_child_folder"""
        return ExternalSpaceFolder(
            id=StringHelper.generate_uuid(),
            name=folder.name,
            children=[]
        )

    def update_folder(self, folder_id: str, folder: ExternalSpaceCreateFolder) -> ExternalSpaceFolder:
        """Mock update_folder that returns a fake updated folder"""
        return ExternalSpaceFolder(
            id=folder_id,
            name=folder.name,
            children=[]
        )

    def share_root_folder(self, root_folder_id: str, group_id: str,
                          role: SpaceRootFolderUserRole = SpaceRootFolderUserRole.USER) -> None:
        """Mock share_root_folder"""
        pass

    def share_root_folder_with_current_lab(self, root_folder_id: str) -> ExternalSpaceFolder:
        """Mock share_root_folder_with_current_lab"""
        return ExternalSpaceFolder(
            id=root_folder_id,
            name='Shared Root Folder',
            children=[]
        )

    def unshare_root_folder(self, folder_id: str, group_id: str) -> None:
        """Mock unshare_folder"""
        pass

    def update_share_folder(self, folder_id: str, user_id: str, role: SpaceRootFolderUserRole) -> None:
        """Mock update_share_folder"""
        pass

    def get_folder_users(self, folder_id: str) -> List[UserSpace]:
        """Mock get_folder_users - returns empty list"""
        return []

    def delete_folder(self, folder_id: str) -> None:
        """Mock delete_folder"""
        pass

    def get_all_current_user_root_folders(self) -> List[SpaceHierarchyObjectDTO]:
        """Mock get_all_current_user_root_folders - returns empty list"""
        return []

    # ==================== ENTITY ====================

    def add_tags_to_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """Mock add_tags_to_object - returns the same tags"""
        return tags

    def add_or_replace_tags_on_object(self, entity_id: str, tags: List[Tag]) -> List[Tag]:
        """Mock add_or_replace_tags_on_object - returns the same tags"""
        return tags

    def delete_tags_on_object(self, entity_id: str, tags: List[Tag]) -> None:
        """Mock delete_tags_on_object"""
        pass

    # ==================== USER ====================

    def get_all_lab_users(self) -> List[UserFullDTO]:
        """Mock get_all_lab_users - returns empty list"""
        return []

    def get_user_info(self, user_id: str) -> UserFullDTO:
        """Mock get_user_info"""
        return UserFullDTO(
            id=user_id,
            email='mock@example.com',
            first_name='Mock',
            last_name='User',
            group=UserGroup.USER,
            is_active=True,
            theme=UserTheme.LIGHT_THEME,
            lang=UserLanguage.EN,
            photo=None
        )

    # ==================== MAIL ====================

    def send_mail(self, send_mail_dto: SpaceSendMailToUsersDTO) -> Response:
        """Mock send_mail"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.json.return_value = {'success': True}
        return response

    def send_mail_to_mails(self, send_mail_to_mails_dto: SpaceSendMailToMailsDTO) -> Response:
        """Mock send_mail_to_mails"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.json.return_value = {'success': True}
        return response

    def send_notification(self, send_notification_dto: SpaceSendNotificationDTO) -> Response:
        """Mock send_notification"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.json.return_value = {'success': True}
        return response

    # ==================== OTHER ====================

    def get_reflex_access_token(self) -> str:
        """Mock get_reflex_access_token - returns a fake token"""
        return 'mock-reflex-token'
