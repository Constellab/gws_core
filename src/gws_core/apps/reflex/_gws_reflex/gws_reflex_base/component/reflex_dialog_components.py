from collections.abc import Callable

import reflex as rx


def dialog_header(title: str, close: Callable | None = None) -> rx.Component:
    """Create a styled header component for a Reflex dialog with a title and close button.

    This function generates a horizontal stack layout containing a heading and a close button,
    designed to be used as the header section of a dialog/modal component. The header
    features a flexible title area that expands to fill available space, and a fixed-width
    close button with an "x" icon positioned on the right side.

    :param title: The text to display as the dialog heading
    :type title: str
    :param close: Optional callback function to execute when the close button is clicked, defaults to None
    :type close: Callable | None, optional
    :return: A horizontal stack component with heading and close button. The component includes full width styling, vertically centered items, and 1em bottom margin
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.dialog.title(title, flex="1", margin_bottom="0"),
        rx.dialog.close(
            rx.button(rx.icon("x"), variant="ghost", color_scheme="gray", on_click=close),
            flex_shrink="0",
        ),
        width="100%",
        align_items="center",
        margin_bottom="1em",
    )
