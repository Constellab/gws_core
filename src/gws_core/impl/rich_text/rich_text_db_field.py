from json import loads
from typing import Any

from peewee import TextField

from gws_core.core.model.typed_db_field import TypedDbField
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


class RichTextDbField(TextField):
    """
    Custom database table field for peewee that support serialization and deserialization RichTextDTO to JSON.
    """

    JSON_FIELD_TEXT_TYPE = "LONGTEXT"
    field_type = JSON_FIELD_TEXT_TYPE

    def db_value(self, value: RichTextDTO | None) -> str | None:
        if value is not None:
            if not isinstance(value, RichTextDTO):
                raise ValueError(f"Value must be a RichTextDTO instance, got {type(value)}")
            return value.to_json_str()
        return None

    def python_value(self, value: str | None) -> RichTextDTO | None:
        if value is not None and value != "":
            json_value = loads(value)

            # if this is the old version of rich text
            # convert it manually to the new version
            if "time" in json_value:
                return RichTextDTO(
                    version=1, blocks=json_value["blocks"], editorVersion=json_value["version"]
                )

            return RichTextDTO.from_json(json_value)
        return None


class TypedRichTextDbField(TypedDbField[RichTextDTO], RichTextDbField):
    """``RichTextDbField`` (``null=False``) whose instance value is typed ``RichTextDTO``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableRichTextDbField(TypedDbField[RichTextDTO | None], RichTextDbField):
    """``RichTextDbField`` (``null=True``) whose instance value is typed ``RichTextDTO | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)
