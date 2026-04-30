from typing import final

from peewee import BooleanField, CharField, TextField

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.form_template.form_template_dto import FormTemplateDTO


@final
class FormTemplate(ModelWithUser):
    """Family record for a versioned form schema. Tags and high-level metadata
    live here; schema content lives in FormTemplateVersion."""

    name = CharField(max_length=255, null=False)
    description = TextField(null=True)
    is_archived = BooleanField(default=False, index=True)

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
