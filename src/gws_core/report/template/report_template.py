# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import CharField

from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.report.template.report_template_dto import (
    ReportTemplateDTO, ReportTemplateFullDTO)

from ...core.model.db_field import BaseDTOField, JSONField
from ...core.model.model_with_user import ModelWithUser


@final
class ReportTemplate(ModelWithUser):
    title = CharField()

    content: RichTextDTO = BaseDTOField(RichTextDTO, null=True)
    old_content = JSONField(null=True)

    _table_name = 'gws_report_template'

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.get_content()

    def to_dto(self) -> ReportTemplateDTO:
        return ReportTemplateDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
        )

    def to_full_dto(self) -> ReportTemplateFullDTO:
        return ReportTemplateFullDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            content=self.content,
        )

    class Meta:
        table_name = 'gws_report_template'
