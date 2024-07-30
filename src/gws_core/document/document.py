

from abc import abstractmethod
from typing import final

from peewee import BooleanField, CharField, ForeignKeyField

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.document.document_dto import DocumentDTO, DocumentFullDTO
from gws_core.entity_navigator.entity_navigator_type import (EntityType,
                                                             NavigableEntity)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.project.model_with_project import ModelWithProject
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from ..core.model.db_field import BaseDTOField, DateTimeUTC
from ..core.model.model_with_user import ModelWithUser
from ..lab.lab_config_model import LabConfigModel
from ..project.project import Project


class Document(ModelWithUser, ModelWithProject, NavigableEntity):
    title = CharField()

    content: RichTextDTO = BaseDTOField(RichTextDTO, null=True)

    project: Project = ForeignKeyField(Project, null=True)

    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at = DateTimeUTC(null=True)
    validated_by: User = ForeignKeyField(User, null=True, backref='+')

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at = DateTimeUTC(null=True)
    last_sync_by: User = ForeignKeyField(User, null=True, backref='+')

    is_archived = BooleanField(default=False, index=True)

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.get_content()

    def check_is_updatable(self) -> None:
        """Throw an error if the report is not updatable
        """
        # check experiment status
        if self.is_validated:
            # TODO TO Update
            raise BadRequestException(GWSException.REPORT_VALIDATED.value, GWSException.REPORT_VALIDATED.name)
        if self.is_archived:
            raise BadRequestException(
                detail=f"The {self.get_entity_type_human_name()} is archived, please unachived it to update it")

    def to_dto(self) -> DocumentDTO:
        return DocumentDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            project=self.project.to_dto() if self.project else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived
        )

    def to_full_dto(self) -> DocumentFullDTO:
        return DocumentFullDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            project=self.project.to_dto() if self.project else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived,
            content=self.content
        )

    def validate(self) -> None:
        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()
        self.lab_config = LabConfigModel.get_current_config()

    def archive(self, archive: bool) -> 'Document':

        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

    def get_entity_name(self) -> str:
        return self.title

    @classmethod
    @abstractmethod
    def get_entity_type(cls) -> EntityType:
        pass

    @classmethod
    @abstractmethod
    def get_default_content(cls) -> RichTextDTO:
        pass

    def entity_is_validated(self) -> bool:
        return self.is_validated
