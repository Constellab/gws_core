import reflex as rx
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo
from reflex.vars import Var

from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from ...reflex_main_state import ReflexMainState

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
    placeholder: Var[str | None]
    value: Var[RichTextDTO | None]
    disabled: Var[bool | None]
    change_event_debounce_time: Var[int | None]

    custom_style: Var[dict | None]  # Additional style properties

    # Whether to load custom tools from /public/custom_block.jsx
    use_custom_tools: Var[bool | None]

    authentication_info: Var[ReflexUserAuthInfo | None]

    # Event handler for output events from the component
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


def rich_text_component(
    placeholder: str | None = None,
    value: RichTextDTO | None = None,
    disabled: bool | None = None,
    change_event_debounce_time: int | None = None,
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
    custom_style: dict | None = None,
    use_custom_tools: bool | None = None,
):
    """Create a RichTextComponent instance.

    :param placeholder: Placeholder text for the editor, defaults to None
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
    :param use_custom_tools: Whether to load custom editor block tools from /public/custom_block.jsx.
        When set to True, the component will dynamically import a JavaScript file that must export
        a `customTools` object. This allows you to define custom block types for the editor.

        The custom_block.jsx file must be placed in your app's assets folder and should export:
        ``export const customTools = { toolName: ToolClass, ... };``

        Each tool class should implement:
        - ``static get toolbox()`` - Returns an array of toolbox entries with title and icon
        - ``render()`` - Returns the DOM element to display
        - ``save(block)`` - Returns the data to save for this block

        Example custom_block.jsx:

            export class MyCustomBlock {
                static get toolbox() {
                    return [{
                        title: 'My Block',
                        icon: '<span class="material-icons-outlined">star</span>',
                    }];
                }

                render() {
                    const wrapper = document.createElement('div');
                    wrapper.innerHTML = '<p>My custom content</p>';
                    return wrapper;
                }

                save(block) {
                    return { data: 'my data' };
                }
            }

            export const customTools = { myBlock: MyCustomBlock };

        Defaults to None (disabled).
    :type use_custom_tools: Optional[bool], optional
    :return: Instance of RichTextComponent
    :rtype: RichTextComponent
    """

    return RichTextComponent.create(
        placeholder=placeholder,
        value=value,
        disabled=disabled,
        change_event_debounce_time=change_event_debounce_time,
        output_event=output_event,
        custom_style=custom_style,
        use_custom_tools=use_custom_tools,
        authentication_info=ReflexMainState.get_reflex_user_auth_info,
    )
