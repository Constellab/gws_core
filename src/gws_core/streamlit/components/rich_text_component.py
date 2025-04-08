
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader


def rich_text_editor(placeholder: str = None,
                     initial_value: RichText = None,
                     disabled: bool = False,
                     key: str = 'rich-text-editor',
                     min_height: str = '500px',
                     max_height: str = None) -> RichText:
    """ Add a rich text editor to the streamlit app

    :param placeholder: placeholder, defaults to None
    :type placeholder: str, optional
    :param initial_value: initial value of the rich text. This is only set on init., defaults to None
    :type initial_value: RichText, optional
    :param disabled: set to True to disable the field, defaults to False
    :type disabled: bool, optional
    :param key: streamlit key, defaults to None
    :type key: str, optional
    :param min_height: minimum height of the editor (css format), defaults to '500px'
    :type min_height: str, optional
    :param max_height: maximum height of the editor (css format), defaults to None
    :type max_height: str, optional
    :return: _description_
    :rtype: RichText
    """

    streamlit_component_loader = StreamlitComponentLoader("text-editor")

    default_value_json = initial_value.to_dto_json_dict() if initial_value is not None else None

    data = {
        "placeholder": placeholder,
        "initial_value": default_value_json,
        "disabled": disabled,
        "min_height": min_height,
        "max_height": max_height
    }
    component_value = streamlit_component_loader.call_component(data, key=key)

    if component_value is None:
        return RichText()

    rich_text_dto = RichTextDTO.from_json(component_value)

    return RichText(rich_text_dto)
