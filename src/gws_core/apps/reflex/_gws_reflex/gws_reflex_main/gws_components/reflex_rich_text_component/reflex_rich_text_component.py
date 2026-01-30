import reflex as rx
from attr import dataclass
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo
from reflex.vars import Var

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from ...reflex_main_state import ReflexMainState

asset_path = rx.asset("reflex_rich_text_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path


@dataclass
class RichTextCustomBlocksConfig:
    jsx_file_path: str
    custom_blocks: dict[str, type[RichTextBlockDataBase]] | None = None
    """Configuration for custom rich text editor tools."""
    config: dict | None = None

    def to_dict(self) -> dict:
        """Convert the config to a dictionary for serialization."""
        return {
            "jsxFilePath": self.jsx_file_path,
            "customBlocks": (
                {name: block.get_typing_name() for name, block in self.custom_blocks.items()}
                if self.custom_blocks
                else None
            ),
            "config": self.config,
        }


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

    custom_tools_config: Var[dict | None]

    authentication_info: Var[ReflexUserAuthInfo | None]

    # Event handler for output events from the component
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]

    custom_tools_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


def rich_text_component(
    placeholder: str | None = None,
    value: RichTextDTO | None = None,
    disabled: bool | None = None,
    change_event_debounce_time: int | None = None,
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
    custom_style: dict | None = None,
    custom_tools_config: RichTextCustomBlocksConfig | None = None,
    custom_tools_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
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
    :param custom_tools_config: Configuration for custom rich text editor blocks.
        When provided, the component will dynamically import the JSX file at ``jsx_file_path``
        which must export a ``getCustomTools(config, authenticationInfo)`` function returning
        an object of custom tool classes (editorjs tools).

        The ``custom_blocks`` dict maps editor tool names to their
        ``RichTextBlockDataBase`` subclass so that block type names are forwarded
        automatically.  An optional ``config`` dict is passed through to the JSX
        factory function as-is.

        **Step 1 — Define a custom block in Python**::

            from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataSpecial
            from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator

            @rich_text_block_decorator("CustomBlock", human_name="Custom Block")
            class CustomBlock(RichTextBlockDataSpecial):
                text: str

                def to_html(self) -> str:
                    return f"<p>Custom Block: {self.text}</p>"

                def to_markdown(self) -> str:
                    return ""

        **Step 2 — Create a JSX file** (e.g. ``rich_text_extension.jsx``) that exports
        ``getCustomTools``.  The returned object maps block type names to editorjs tool
        classes::

            // rich_text_extension.jsx
            export function getCustomTools(config, authenticationInfo) {
              class DcTextEditorToolExampleBlock {
                constructor({data}) { this.data = data; }

                static get toolbox() {
                  return {
                    title: 'Example Tool',
                    icon: '<span class="material-icons-outlined">build</span>',
                  };
                }

                render() {
                  const wrapper = document.createElement('div');
                  const p = document.createElement('p');
                  p.innerText = `Custom block content : '${this.data?.text || 'default text'}'`;
                  wrapper.appendChild(p);
                  return wrapper;
                }

                save(block) {
                  return { data: this.data?.text || 'default text' };
                }
              }

              return { [config.block_name]: DcTextEditorToolExampleBlock };
            }

        **Step 3 — Register the asset and wire up the component**::

            import reflex as rx
            from gws_core import RichText, RichTextDTO
            from gws_reflex_main.gws_components import RichTextCustomBlocksConfig, rich_text_component

            asset_path = rx.asset("rich_text_extension.jsx", shared=True)

            class MyState(rx.State):
                _rich_text: RichText = RichText()

                @rx.var
                def rich_text(self) -> RichTextDTO:
                    return self._rich_text.to_dto()

                @rx.event
                def handle_rich_text_change(self, event_data: dict):
                    self._rich_text = RichText.from_json(event_data)

            rich_text_component(
                placeholder="Type something here...",
                value=MyState.rich_text,
                output_event=MyState.handle_rich_text_change,
                custom_tools_config=RichTextCustomBlocksConfig(
                    jsx_file_path=asset_path,  # No /public prefix needed - handled automatically
                    custom_blocks={"CustomBlock": CustomBlock},
                ),
            )

        Defaults to None (disabled).
    :type custom_tools_config: Optional[RichTextCustomBlocksConfig], optional
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
        custom_tools_config=custom_tools_config.to_dict() if custom_tools_config else None,
        authentication_info=ReflexMainState.get_reflex_user_auth_info,
        custom_tools_event=custom_tools_event,
    )
