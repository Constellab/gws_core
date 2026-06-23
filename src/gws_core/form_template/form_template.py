from typing import final

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import NullableTextField, TypedBooleanField, TypedCharField
from gws_core.entity_navigator.entity_navigator_type import (
    NavigableEntity,
    NavigableEntityType,
)
from gws_core.form_template.form_template_dto import FormTemplateDTO
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType


@final
class FormTemplate(ModelWithUser, NavigableEntity):
    """Family record for a versioned form schema. Tags and high-level metadata
    live here; schema content lives in FormTemplateVersion."""

    name = TypedCharField(max_length=255)
    description = NullableTextField()
    is_archived = TypedBooleanField(default=False, index=True)

    def archive(self, archive: bool) -> "FormTemplate":
        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

    def get_navigable_entity_type(self) -> NavigableEntityType:
        return NavigableEntityType.FORM_TEMPLATE

    def get_navigable_entity_name(self) -> str:
        return self.name

    def delete_instance(self, *args, **kwargs):
        super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(TagEntityType.FORM_TEMPLATE, self.id)

    def to_dto(self) -> FormTemplateDTO:
        return FormTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            description=self.description,
            is_archived=self.is_archived,
        )

    class Meta:
        table_name = "gws_form_template"
        is_table = True
