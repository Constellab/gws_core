# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import CharField

from gws_core.core.classes.rich_text_content import RichText

from ...core.model.db_field import JSONField
from ...core.model.model_with_user import ModelWithUser


@final
class ReportTemplate(ModelWithUser):
    title = CharField()

    content = JSONField(null=True)

    _table_name = 'gws_report_template'

    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.get_content()

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)

        if not deep:
            del json_["content"]

        return json_
