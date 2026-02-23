from collections.abc import Callable

from gws_core.brick.brick_log_service import BrickLogService
from gws_core.core.utils.utils import Utils
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase
from gws_core.model.typing_register_decorator import register_gws_typing_class


def rich_text_block_decorator(
    unique_name: str,
    human_name: str = "",
    short_description: str = "",
    hide: bool = True,
) -> Callable:
    """Decorator to register a RichTextBlockDataBase subclass as a typing.

    This decorator allows new RichTextBlock types to be created without modifying
    the RichTextBlock class. When a block with the decorated type is encountered,
    the RichTextBlock.get_data() method will automatically use the registered class
    via the TypingManager.

    :param unique_name: The block type identifier (e.g., 'paragraph', 'header').
                        This should match the value used in RichTextBlockType enum
                        or be a custom string for new block types.
                        //!\\ DO NOT MODIFY THIS NAME ONCE DEFINED //!\\
    :type unique_name: str
    :param human_name: Optional human-readable name for the block type.
                       If not provided, will be generated from unique_name.
    :type human_name: str, optional
    :param short_description: Optional description of the block type.
    :type short_description: str, optional
    :param hide: Whether to hide this type in the interface. Defaults to True
                 since block types are typically internal implementation details.
    :type hide: bool, optional

    Example usage:
        @rich_text_block_decorator("myCustomBlock")
        class RichTextBlockMyCustom(RichTextBlockDataBase):
            # ... implementation
    """

    def decorator(data_class: type[RichTextBlockDataBase]):
        # Verify that the decorated class extends RichTextBlockDataBase
        if not Utils.issubclass(data_class, RichTextBlockDataBase):
            BrickLogService.log_brick_error(
                data_class,
                f"The rich_text_block_decorator is used on class '{data_class.__name__}' "
                f"but this class is not a subclass of RichTextBlockDataBase",
            )
            return data_class

        register_gws_typing_class(
            object_class=data_class,
            object_type="RICH_TEXT_BLOCK",
            unique_name=unique_name,
            human_name=human_name,
            short_description=short_description,
            hide=hide,
            style=None,
            object_sub_type=unique_name,  # Use the block type as sub_type for lookup
        )
        return data_class

    return decorator
