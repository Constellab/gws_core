import reflex as rx
from attr import dataclass
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo
from reflex.event import EventCallback
from reflex.vars import Var

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from ...reflex_main_state import ReflexMainState

asset_path = rx.asset("reflex_rich_text_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path


@dataclass
class RichTextImageConfig:
    """Configuration of the images of a rich text editor.

    It identifies the object owning the rich text. The editor uploads and loads the images
    through the lab ``rich-text/{object_type}/{object_id}/image`` routes, in a directory
    dedicated to that object.

    The images are stored by :class:`RichTextFileService`, so the owner of the object must
    delete that directory when the object is deleted (``RichTextFileService.delete_object_dir``),
    otherwise the images are leaked.
    """

    object_type: str
    """Type of the object owning the rich text, e.g. ``'project_document'`` or a
    :class:`RichTextObjectType` value. It is used as a directory name, so it must only contain
    letters, digits, ``_`` and ``-``."""

    object_id: str
    """Id of the object owning the rich text."""

    def to_dict(self) -> dict:
        """Convert the config to a dictionary for serialization."""
        return {
            "objectType": self.object_type,
            "objectId": self.object_id,
        }


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

    # Object owning the images of the rich text. When it is set, the image tool is enabled
    # and the editor uploads/loads the images through the lab rich text API.
    image_config: Var[dict | None]

    custom_style: Var[dict | None]  # Additional style properties

    custom_tools_config: Var[dict | None]

    authentication_info: Var[ReflexUserAuthInfo | None]

    # Event handler for output events from the component
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]

    custom_tools_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


def rich_text_component(  # noqa: PLR0913 the params mirror the component's props
    placeholder: str | None = None,
    value: RichTextDTO | Var[RichTextDTO] | None = None,
    disabled: bool | None = None,
    change_event_debounce_time: int | None = None,
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | EventCallback | None = None,
    custom_style: dict | None = None,
    custom_tools_config: RichTextCustomBlocksConfig | None = None,
    custom_tools_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
    fallback_to_system_user: bool = False,
    image_config: RichTextImageConfig | None = None,
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
    :param fallback_to_system_user: when no user is authenticated (PUBLIC app), authenticate
        the component's API requests as the system user instead of leaving them
        unauthenticated. WARNING: this lets any visitor of the app read and write data lab
        objects through the API as the system user, including uploading the editor's images.
        Defaults to False.
    :type fallback_to_system_user: bool, optional
    :param image_config: object owning the images of this rich text. When provided, the image
        tool is enabled and the editor uploads/loads the images through the lab rich text API::

            rich_text_component(
                value=MyState.content,
                output_event=MyState.handle_change,
                image_config=RichTextImageConfig(
                    object_type="project_document",
                    object_id=MyState.document_id,
                ),
            )

        The images are stored in a directory dedicated to the object, so the owner of the
        object is responsible for deleting that directory when the object is deleted
        (``RichTextFileService.delete_object_dir``). Defaults to None (image tool disabled).
    :type image_config: Optional[RichTextImageConfig], optional
    :return: Instance of RichTextComponent
    :rtype: RichTextComponent
    """

    authentication_info = (
        ReflexMainState.get_reflex_user_auth_info_with_system_fallback
        if fallback_to_system_user
        else ReflexMainState.get_reflex_user_auth_info
    )
    return RichTextComponent.create(
        placeholder=placeholder,
        value=value,
        disabled=disabled,
        change_event_debounce_time=change_event_debounce_time,
        output_event=output_event,
        custom_style=custom_style,
        custom_tools_config=custom_tools_config.to_dict() if custom_tools_config else None,
        authentication_info=authentication_info,
        custom_tools_event=custom_tools_event,
        image_config=image_config.to_dict() if image_config else None,
    )
