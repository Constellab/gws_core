
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader


def rich_text_editor(placeholder: str = None,
                     initial_value: RichText = None,
                     disabled: bool = False,
                     key: str = 'rich-text-editor') -> RichText:
    """ Add a rich text editor to the streamlit app

    :param placeholder: placeholder, defaults to None
    :type placeholder: str, optional
    :param initial_value: initial value of the rich text. This is only set on init., defaults to None
    :type initial_value: RichText, optional
    :param disabled: set to True to disable the field, defaults to False
    :type disabled: bool, optional
    :param key: streamlit key, defaults to None
    :type key: str, optional
    :return: _description_
    :rtype: RichText
    """

    streamlit_component_loader = StreamlitComponentLoader(
        "text-editor",
        version="dc_text_editor_1.2.0",
        is_released=True)

    default_value_json = initial_value.to_dto_json_dict() if initial_value is not None else None

    component_value = streamlit_component_loader.get_function()(
        placeholder=placeholder, initial_value=default_value_json, key=key, default=default_value_json,
        disabled=disabled)

    if component_value is None:
        return RichText()

    rich_text_dto = RichTextDTO.from_json(component_value)

    return RichText(rich_text_dto)
