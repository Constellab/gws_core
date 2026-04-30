from typing import final

from peewee import BooleanField, CharField, TextField

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.form_template.form_template_dto import (
    FormTemplateDTO,
    FormTemplateFullDTO,
    FormTemplateVersionStatus,
)
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType


@final
class FormTemplate(ModelWithUser):
    """Family record for a versioned form schema. Tags and high-level metadata
    live here; schema content lives in FormTemplateVersion."""

    name = CharField(max_length=255, null=False)
    description = TextField(null=True)
    is_archived = BooleanField(default=False, index=True)

    def archive(self, archive: bool) -> "FormTemplate":
        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

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

    def to_full_dto(self) -> FormTemplateFullDTO:
        # DRAFT first, then PUBLISHED newest-first, then ARCHIVED newest-first.
        status_rank = {
            FormTemplateVersionStatus.DRAFT: 0,
            FormTemplateVersionStatus.PUBLISHED: 1,
            FormTemplateVersionStatus.ARCHIVED: 2,
        }
        versions = sorted(
            self.versions,
            key=lambda v: (status_rank[v.status], -v.version),
        )
        return FormTemplateFullDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            description=self.description,
            is_archived=self.is_archived,
            versions=[v.to_dto() for v in versions],
        )

    class Meta:
        table_name = "gws_form_template"
        is_table = True
