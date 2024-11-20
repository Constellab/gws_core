from json import loads

from peewee import TextField

from gws_core.impl.rich_text.rich_text_types import RichTextDTO


class RichTextField(TextField):
    """
    Custom field that support serialization and deserialization RichTextDTO to JSON.
    """

    JSON_FIELD_TEXT_TYPE = "LONGTEXT"
    field_type = JSON_FIELD_TEXT_TYPE

    def db_value(self, value: RichTextDTO) -> str:
        if value is not None:
            if not isinstance(value, RichTextDTO):
                raise ValueError(f"Value must be a RichTextDTO instance, got {type(value)}")
            return value.to_json_str()
        return None

    def python_value(self, value: str) -> RichTextDTO:
        if value is not None and value != "":
            json_value = loads(value)

            # if this is the old version of rich text
            # convert it manually to the new version
            if 'time' in json_value:
                return RichTextDTO(
                    version=1,
                    blocks=json_value['blocks'],
                    editorVersion=json_value['version']
                )

            return RichTextDTO.from_json(json_value)
        return None
