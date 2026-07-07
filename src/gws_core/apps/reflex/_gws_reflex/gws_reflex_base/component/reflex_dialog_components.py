from collections.abc import Callable

import reflex as rx


def dialog_header(
    title: str | rx.Var[str] | rx.Component,
    subtitle: str | rx.Var[str] | rx.Component | None = None,
    close: Callable | None = None,
    additional_actions: rx.Component | None = None,
) -> rx.Component:
    """Create a styled header component for a Reflex dialog with a title and close button.

    This function generates a horizontal stack layout containing a heading and a close button,
    designed to be used as the header section of a dialog/modal component. The header
    features a flexible title area that expands to fill available space, and a fixed-width
    close button with an "x" icon positioned on the right side. An optional subtitle is
    rendered as a smaller, muted line right under the title.

    :param title: The text (str or reactive Var) or component to display as the dialog heading
    :type title: str | rx.Var[str] | rx.Component
    :param subtitle: Optional secondary line shown under the title; a string/Var is rendered as small gray text, a component is used as-is, defaults to None
    :type subtitle: str | rx.Var[str] | rx.Component | None, optional
    :param close: Optional callback function to execute when the close button is clicked, defaults to None
    :type close: Callable | None, optional
    :param additional_actions: Optional additional actions to include in the header (align on right side), defaults to None
    :type additional_actions: rx.Component | None, optional
    :return: A horizontal stack component with heading and close button. The component includes full width styling, vertically centered items, and 1em bottom margin
    :rtype: rx.Component
    """
    # Wrap a str/Var title in a text component; a passed-in component is used as-is.
    title_component = title if isinstance(title, rx.Component) else rx.text(title)

    if subtitle is None:
        title_area = rx.dialog.title(title_component, flex="1", margin_bottom="0")
    else:
        # Wrap anything that is not already a component (str or reactive Var) so the
        # muted subtitle styling is applied; a passed-in component is used as-is.
        subtitle_component = (
            subtitle if isinstance(subtitle, rx.Component) else rx.text(subtitle, size="2", color="gray")
        )
        title_area = rx.vstack(
            rx.dialog.title(title_component, margin_bottom="0"),
            subtitle_component,
            flex="1",
            spacing="1",
            align_items="start",
        )

    return rx.hstack(
        title_area,
        additional_actions if additional_actions else rx.box(),
        rx.dialog.close(
            rx.button(rx.icon("x"), variant="ghost", color_scheme="gray", on_click=close),
            flex_shrink="0",
        ),
        width="100%",
        align_items="center",
        margin_bottom="1em",
    )
