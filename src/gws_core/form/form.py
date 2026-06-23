from typing import final

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import (
    NullableDateTimeUTC,
    NullableForeignKeyField,
    NullableJSONField,
    TypedBooleanField,
    TypedCharField,
    TypedEnumField,
    TypedForeignKeyField,
)
from gws_core.entity_navigator.entity_navigator_type import (
    NavigableEntity,
    NavigableEntityType,
)
from gws_core.form.form_dto import FormDTO, FormStatus, FormTemplateRefDTO
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.user.user import User


@final
class Form(ModelWithUser, NavigableEntity):
    """An instance of a FormTemplateVersion filled (or being filled) with values."""

    name = TypedCharField(max_length=255, null=False)

    # FK is non-cascading: deleting a version that has Forms is forbidden at
    # the service layer (Phase 2). Forms outlive the version they were minted
    # from for as long as the version is not hard-deleted.
    template_version = TypedForeignKeyField(
        FormTemplateVersion, null=False, backref="forms"
    )

    status = TypedEnumField(
        choices=FormStatus, default=FormStatus.DRAFT, index=True
    )

    submitted_at = NullableDateTimeUTC(null=True)
    submitted_by = NullableForeignKeyField(User, null=True, backref="+")

    # Field values keyed by ConfigSpecs key; ParamSet items carry __item_id.
    values = NullableJSONField(null=True)

    is_archived = TypedBooleanField(default=False, index=True)

    @classmethod
    def count_for_template(cls, template_id: str) -> int:
        """Count forms across all versions of the given template."""
        return (
            cls.select()
            .join(FormTemplateVersion)
            .where(FormTemplateVersion.template_id == template_id)
            .count()
        )

    @classmethod
    def count_for_version(cls, version_id: str) -> int:
        return cls.select().where(cls.template_version == version_id).count()

    @classmethod
    def find_by_template(cls, template_id: str) -> list["Form"]:
        """Return every Form bound to any version of the given template."""
        return list(
            cls.select()
            .join(FormTemplateVersion)
            .where(FormTemplateVersion.template_id == template_id)
        )

    def get_navigable_entity_type(self) -> NavigableEntityType:
        return NavigableEntityType.FORM

    def get_navigable_entity_name(self) -> str:
        return self.name

    def delete_instance(self, *args, **kwargs):
        super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(TagEntityType.FORM, self.id)

    def to_dto(self) -> FormDTO:
        version = self.template_version
        template = version.template
        return FormDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            template=FormTemplateRefDTO(
                template_id=template.id,
                template_name=template.name,
                version_id=version.id,
                version_number=version.version,
            ),
            status=self.status,
            submitted_at=self.submitted_at,
            submitted_by=self.submitted_by.to_dto() if self.submitted_by else None,
            is_archived=self.is_archived,
        )

    class Meta:
        table_name = "gws_form"
        is_table = True
