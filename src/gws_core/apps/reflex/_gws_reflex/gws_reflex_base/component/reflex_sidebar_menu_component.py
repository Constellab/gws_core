"""Generic menu item and sidebar menu components for sidebar navigation."""

import reflex as rx


def sidebar_menu_component(
    title: str,
    menu_items: list[rx.Component],
    logo_src: str | None = None,
) -> rx.Component:
    """Create a sidebar menu with logo, title and navigation links.

    :param logo_src: The source path for the logo image
    :type logo_src: str
    :param title: The title to display next to the logo
    :type title: str
    :param menu_items: List of menu item components (use menu_item_component)
    :type menu_items: list[rx.Component]
    :return: The sidebar menu component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.hstack(
            rx.cond(
                logo_src,
                rx.image(
                    src=logo_src,
                    height="2rem",
                    width="auto",
                ),
            ),
            rx.heading(title, size="6", line_height="1em"),
            spacing="4",
            align="center",
            margin_bottom="1rem",
        ),
        rx.vstack(
            *menu_items,
            width="100%",
            spacing="1",
            align_items="start",
        ),
        width="100%",
        align_items="start",
    )


def menu_item_component(icon: str, label: str, href: str) -> rx.Component:
    """Create a menu item with icon and label for sidebar navigation.

    :param icon: The icon name (Lucide icon)
    :type icon: str
    :param label: The text label for the menu item
    :type label: str
    :param href: The URL to navigate to
    :type href: str
    :return: A menu item component
    :rtype: rx.Component
    """
    return rx.link(
        rx.hstack(rx.icon(icon, size=20), rx.text(label), spacing="2", align="center"),
        href=href,
        width="100%",
        padding="0.75rem 1rem",
        border_radius="6px",
        _hover={
            "background": "var(--gray-3)",
        },
        color="inherit",
        text_decoration="none",
    )
