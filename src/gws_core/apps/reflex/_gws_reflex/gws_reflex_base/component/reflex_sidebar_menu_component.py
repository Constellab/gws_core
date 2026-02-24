"""Generic menu item and sidebar menu components for sidebar navigation."""

import reflex as rx


def sidebar_menu_component(
    title: str,
    menu_items: list[rx.Component],
    logo_src: str | None = None,
    subtitle: str | None = None,
) -> rx.Component:
    """Create a sidebar menu with logo, title and navigation links.

    :param logo_src: The source path for the logo image
    :type logo_src: str
    :param title: The title to display next to the logo
    :type title: str
    :param menu_items: List of menu item components (use menu_item_component)
    :type menu_items: list[rx.Component]
    :param subtitle: An optional subtitle displayed below the title in smaller grey text
    :type subtitle: str | None
    :return: The sidebar menu component
    :rtype: rx.Component
    """
    title_section = [rx.heading(title, size="4", line_height="1em")]
    if subtitle:
        title_section.append(
            rx.text(subtitle, size="1", color="var(--gray-9)", line_height="1em"),
        )

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
            rx.vstack(*title_section, spacing="1"),
            spacing="2",
            align="center",
            margin_bottom="1rem",
            padding="1em",
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


def menu_item_component(
    icon: str,
    label: str,
    href: str,
    additional_active_route_prefixes: list[str] | None = None,
) -> rx.Component:
    """Create a menu item with icon and label for sidebar navigation.

    :param icon: The icon name (Lucide icon)
    :type icon: str
    :param label: The text label for the menu item
    :type label: str
    :param href: The URL to navigate to
    :type href: str
    :param additional_active_route_prefixes: Route prefixes that also highlight this item.
        Uses startswith matching so "/projects" will match "/projects/123".
    :type additional_active_route_prefixes: list[str] | None
    :return: A menu item component
    :rtype: rx.Component
    """
    current_path = rx.State.router.page.path

    # '/' route can appear as '/index' in Reflex, so handle both cases
    is_active = rx.cond(
        href == "/",
        (current_path == "/") | (current_path == "/index"),
        current_path == href,
    )

    for prefix in additional_active_route_prefixes or []:
        is_active = is_active | current_path.startswith(prefix)

    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(label, font_weight=rx.cond(is_active, "650", "inherit")),
            rx.cond(
                is_active,
                rx.box(
                    width="6px",
                    height="6px",
                    border_radius="50%",
                    background="var(--accent-9)",
                    margin_left="auto",
                ),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        href=href,
        width="100%",
        padding="0.75rem 1rem",
        border_radius="6px",
        background=rx.cond(is_active, "var(--accent-3)", "transparent"),
        color=rx.cond(is_active, "var(--accent-11)", "inherit"),
        _hover={
            "background": rx.cond(is_active, "var(--accent-3)", "var(--gray-3)"),
        },
        text_decoration="none",
    )
