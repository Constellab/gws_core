from typing import Optional

import reflex as rx
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from reflex.vars import Var

asset_path = rx.asset("reflex_rich_text_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path


class RichTextComponent(rx.Component):
    """Rich Text Editor component using dc-text-editor Angular component.

    This component wraps the dc-text-editor Angular component and matches the DcRichTextConfig interface.
    """

    # Use the custom TSX component
    library = public_js_path
    tag = "RichTextComponent"

    # Component props matching DcRichTextConfig interface
    placeholder: Var[Optional[str]]
    value: Var[Optional[RichTextDTO]]
    disabled: Var[Optional[bool]]
    change_event_debounce_time: Var[Optional[int]]

    custom_style: Var[Optional[dict]]  # Additional style properties

    # Event handler for output events from the component
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


def rich_text_component(placeholder: Optional[str] = None,
                        value: Optional[RichTextDTO] = None,
                        disabled: Optional[bool] = None,
                        change_event_debounce_time: Optional[int] = None,
                        output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]] = None,
                        custom_style: Optional[dict] = None):
    """Create a RichTextComponent instance.

    :param placeholder:² Placeholder text for the editor, defaults to None
    :type placeholder: Optional[str], optional
    :param value: Value for the editor, defaults to None
    :type value: Optional[RichTextDTO], optional
    :param disabled: Whether the editor is disabled, defaults to None
    :type disabled: Optional[bool], optional
    :param change_event_debounce_time: Debounce time for change events, defaults to None
    :type change_event_debounce_time: Optional[int], optional
    :param output_event: Event handler for output events; It emits a RichTextDTO object as a dictionary., defaults to None
    :type output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]], optional
    :param custom_style: Additional style properties for the component, defaults to None
    :type custom_style: Optional[dict], optional
    :return: Instance of RichTextComponent
    :rtype: RichTextComponent
    """

    return RichTextComponent.create(
        placeholder=placeholder,
        value=value,
        disabled=disabled,
        change_event_debounce_time=change_event_debounce_time,
        output_event=output_event,
        custom_style=custom_style
    )
