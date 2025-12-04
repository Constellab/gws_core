from typing import final

from peewee import CharField

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_db_field import RichTextDbField
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.note_template.note_template_dto import NoteTemplateDTO


@final
class NoteTemplate(ModelWithUser):
    title = CharField()

    content: RichTextDTO = RichTextDbField(null=True)

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.to_dto()

    def to_dto(self) -> NoteTemplateDTO:
        return NoteTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
        )

    class Meta:
        table_name = "gws_note_template"
        is_table = True
