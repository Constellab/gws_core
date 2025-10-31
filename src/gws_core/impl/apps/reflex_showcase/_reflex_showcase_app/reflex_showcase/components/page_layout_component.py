"""Component to provide consistent page layout across showcase pages."""


import reflex as rx


def page_layout(
    title: str,
    description: str,
    *content: rx.Component,
) -> rx.Component:
    """
    Create a consistent page layout with title, description, divider, and content.

    This component provides a standardized layout for all showcase pages including:
    - Page title (large heading)
    - Page description (gray text)
    - Content area with proper padding

    :param title: The main page title (displayed as size 9 heading)
    :param description: Brief description of the page (displayed in gray)
    :param content: Variable number of Reflex components to display as page content
    :return: A Reflex component with consistent page layout
    """
    return rx.box(
        # Page header
        rx.heading(title, size="7", margin_bottom="0.5em"),

        rx.text(
            description,
            size="3",
            color="gray",
            margin_bottom="2em",
        ),

        # Page content
        *content,

        # Page padding
        padding="2em",
    )
