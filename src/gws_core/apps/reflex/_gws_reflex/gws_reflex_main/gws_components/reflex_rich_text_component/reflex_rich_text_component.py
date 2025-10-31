from typing import Optional

import reflex as rx
from reflex.vars import Var

from gws_core.impl.rich_text.rich_text_types import RichTextDTO

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
    min_height: Var[Optional[str]]
    max_height: Var[Optional[str]]

    # Event handler for output events from the component
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


def rich_text_component(placeholder: Optional[str] = None,
                        value: Optional[RichTextDTO] = None,
                        disabled: Optional[bool] = None,
                        min_height: Optional[str] = None,
                        max_height: Optional[str] = None,
                        output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]] = None,
                        **kwargs) -> RichTextComponent:
    """Create a RichTextComponent instance.

    :param placeholder: Placeholder text for the editor, defaults to None
    :type placeholder: Optional[str], optional
    :param value: Value for the editor, defaults to None
    :type value: Optional[RichTextDTO], optional
    :param disabled: Whether the editor is disabled, defaults to None
    :type disabled: Optional[bool], optional
    :param min_height: Minimum height of the editor, defaults to None
    :type min_height: Optional[str], optional
    :param max_height: Maximum height of the editor, defaults to None
    :type max_height: Optional[str], optional
    :param output_event: Event handler for output events; It emits a RichTextDTO object as a dictionary., defaults to None
    :type output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]], optional
    :return: Instance of RichTextComponent
    :rtype: RichTextComponent
    """

    return RichTextComponent.create(
        placeholder=placeholder,
        value=value,
        disabled=disabled,
        min_height=min_height,
        max_height=max_height,
        output_event=output_event,
        **kwargs
    )
