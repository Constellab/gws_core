

from typing import final

from peewee import CharField

from gws_core.core.model.db_field import BaseDTOField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.document_template.document_template_dto import \
    DocumentTemplateDTO
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


@final
class DocumentTemplate(ModelWithUser):
    title = CharField()

    content: RichTextDTO = BaseDTOField(RichTextDTO, null=True)

    _table_name = 'gws_document_template'

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.get_content()

    def to_dto(self) -> DocumentTemplateDTO:
        return DocumentTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
        )

    class Meta:
        table_name = 'gws_document_template'
