from peewee import CharField, ForeignKeyField, ModelSelect

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.model.model import Model
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.lab.lab_model.lab_dto import LabDTO
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.share.shared_dto import SharedEntityMode, ShareEntityInfoDTO
from gws_core.user.user import User
from gws_core.user.user_service import UserService


class SharedEntityInfo(Model):
    """Class to store information about a shared entity.
    It stores the origin of the entity if the entity was imported from an external source.
    It stores the destination of the entity if the entity was exported to an external source.
    """

    share_mode: SharedEntityMode = EnumField(choices=SharedEntityMode)

    # FK to LabModel — replaces lab_id, lab_name, space_id, space_name
    lab: LabModel = ForeignKeyField(LabModel, null=True, backref="+")

    # FK to User — the user from the external lab who shared/received the entity.
    # If the user doesn't exist locally, import them as inactive.
    user: User = ForeignKeyField(User, null=True, backref="+")

    # Current lab user who created the share link (SENT) or imported the entity (RECEIVED)
    created_by: User = ForeignKeyField(User, null=True, backref="+")

    # The entity ID on the *other* lab:
    # RECEIVED: original entity ID from the source lab (before local ID remapping)
    # SENT: entity ID assigned by the receiving lab
    external_id = CharField(max_length=36)

    # override on children classes
    entity: Model | None = None

    @classmethod
    def get_and_check_entity_origin(cls, entity_id: str) -> "SharedEntityInfo":
        """Method that check if the entity is shared and return the origin information"""
        shared_resource = cls.get_or_none(
            (cls.entity == entity_id) & (cls.share_mode == SharedEntityMode.RECEIVED)
        )

        if shared_resource is None:
            raise BadRequestException("Information about lab import does not exist")

        return shared_resource

    @classmethod
    def already_shared_with_lab(cls, entity_id: str, lab_dto: LabDTO) -> bool:
        """Method that check if the entity is already shared with the lab.

        Resolves the lab by (lab_id, mode) to find the local LabModel row.
        """
        lab = LabModel.get_by_lab_id_and_mode(lab_dto.lab_id, lab_dto.mode)
        if lab is None:
            return False
        return (
            cls.get_or_none(
                (cls.entity == entity_id)
                & (cls.share_mode == SharedEntityMode.SENT)
                & (cls.lab == lab.id)
            )
            is not None
        )

    @classmethod
    def get_sents(cls, entity_id: str) -> ModelSelect:
        """Method that return the receivers of the entity"""
        return (
            cls.select()
            .where(cls.entity == entity_id, cls.share_mode == SharedEntityMode.SENT)
            .order_by(cls.created_at.desc())
        )

    @classmethod
    def mark_as_received(
        cls,
        entity_id: str,
        lab_info: ExternalLabWithUserInfo,
        created_by: User,
        external_id: str,
    ) -> "SharedEntityInfo":
        """Mark an entity as received from an external lab.

        If the entity is already marked as received, return the existing record.
        """
        existing = cls.get_or_none(
            (cls.entity == entity_id) & (cls.share_mode == SharedEntityMode.RECEIVED)
        )
        if existing is not None:
            return existing

        return cls._create_from_lab_info(
            entity_id=entity_id,
            mode=SharedEntityMode.RECEIVED,
            lab_info=lab_info,
            created_by=created_by,
            external_id=external_id,
        )

    @classmethod
    def mark_as_sent(
        cls,
        entity_id: str,
        lab_info: ExternalLabWithUserInfo,
        created_by: User,
        external_id: str,
    ) -> "SharedEntityInfo":
        """Mark an entity as sent to an external lab."""
        return cls._create_from_lab_info(
            entity_id=entity_id,
            mode=SharedEntityMode.SENT,
            lab_info=lab_info,
            created_by=created_by,
            external_id=external_id,
        )

    @classmethod
    def _create_from_lab_info(
        cls,
        entity_id: str,
        mode: SharedEntityMode,
        lab_info: ExternalLabWithUserInfo,
        created_by: User,
        external_id: str,
    ) -> "SharedEntityInfo":
        """Internal method to create a shared entity info record."""
        lab = LabModel.get_or_create_from_dto(lab_info.lab)
        user = UserService.get_or_import_user_info(lab_info.user.id)

        shared_entity = cls()
        shared_entity.entity = entity_id
        shared_entity.share_mode = mode
        shared_entity.lab = lab
        shared_entity.user = user
        shared_entity.created_by = created_by
        shared_entity.external_id = external_id
        shared_entity.save()
        return shared_entity

    def to_dto(self) -> ShareEntityInfoDTO:
        return ShareEntityInfoDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            share_mode=self.share_mode,
            lab=self.lab.to_dto() if self.lab else None,
            user=self.user.to_dto() if self.user else None,
            created_by=self.created_by.to_dto() if self.created_by else None,
            external_id=self.external_id,
        )
