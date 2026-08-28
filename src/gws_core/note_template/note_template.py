from typing import final

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import TypedCharField
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_db_field import NullableRichTextDbField
from gws_core.note_template.note_template_dto import NoteTemplateDTO
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType


@final
class NoteTemplate(ModelWithUser):
    title: TypedCharField = TypedCharField()

    content: NullableRichTextDbField = NullableRichTextDbField()

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.to_dto()

    def delete_instance(self, *args, **kwargs):
        super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(TagEntityType.NOTE_TEMPLATE, self.id)

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
