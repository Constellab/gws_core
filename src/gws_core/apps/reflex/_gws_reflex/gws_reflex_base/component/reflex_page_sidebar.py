import reflex as rx


def _create_sidebar_drawer(
    sidebar_content: rx.Component,
    sidebar_width: str,
) -> rx.Component:
    """Create the drawer component for mobile/tablet sidebar."""
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.icon_button(
                rx.icon("menu", size=24),
                variant="soft",
            )
        ),
        rx.drawer.overlay(z_index="999"),
        rx.drawer.portal(
            rx.drawer.content(
                sidebar_content,
                top="auto",
                right="auto",
                height="100%",
                width=sidebar_width,
                padding="2rem 1rem",
                bg="var(--gray-2)",
            ),
        ),
        direction="left",
    )


def _create_desktop_sidebar(
    sidebar_content: rx.Component,
    sidebar_width: str,
) -> rx.Component:
    """Create the fixed sidebar for desktop."""
    return rx.desktop_only(
        rx.vstack(
            sidebar_content,
            width=sidebar_width,
            min_width=sidebar_width,
            padding="1.5rem",
            background="var(--gray-2)",
            border_radius="8px",
            align_items="start",
            height="100vh",
            position="fixed",
            left="0",
            top="0",
            z_index="5",
        ),
    )


def _create_mobile_header(
    header_content: rx.Component | None,
    sidebar_drawer: rx.Component,
) -> rx.Component:
    """Create the mobile/tablet header with hamburger menu."""
    if header_content is None:
        return rx.fragment()

    return rx.mobile_and_tablet(
        rx.hstack(
            sidebar_drawer,
            header_content,
            width="100%",
            align_items="center",
            spacing="3",
            padding="1rem",
            position="fixed",
            top="0",
            left="0",
            z_index="10",
            background="var(--color-background)",
        ),
    )


def _create_desktop_content(
    content: rx.Component,
    header_content: rx.Component | None,
    sidebar_width: str,
) -> rx.Component:
    """Create the desktop content area with optional header."""
    return rx.desktop_only(
        rx.vstack(
            rx.cond(
                header_content is not None,
                rx.box(
                    header_content,
                    width="100%",
                    padding_bottom="1rem",
                ),
                rx.fragment(),
            ),
            content,
            margin_left=sidebar_width,
            width=f"calc(100% - {sidebar_width})",
            height="100vh",
            overflow_y="auto",
            padding="2rem",
            spacing="0",
            align_items="stretch",
        ),
    )


def _create_mobile_content(
    content: rx.Component,
    header_content: rx.Component | None,
) -> rx.Component:
    """Create the mobile/tablet content area."""
    padding_top = "5rem" if header_content is not None else "1rem"

    return rx.mobile_and_tablet(
        rx.box(
            content,
            width="100%",
            height="100vh",
            overflow_y="auto",
            padding_top=padding_top,
            padding_left="1rem",
            padding_right="1rem",
            padding_bottom="2rem",
        ),
    )


def page_sidebar_component(
    sidebar_content: rx.Component,
    content: rx.Component,
    sidebar_width: str = "250px",
    height: str | None = None,
    header_content: rx.Component | None = None,
    **kwargs,
) -> rx.Component:
    """Create a generic page layout with responsive sidebar and main content area.

    This component provides a layout with:
    - Desktop: Fixed sidebar on left, content on right with optional header on top
    - Mobile/Tablet: Hamburger menu with drawer sidebar, optional header bar on top

    :param sidebar_content: The content to display in the sidebar
    :type sidebar_content: rx.Component
    :param content: The main content to display
    :type content: rx.Component
    :param sidebar_width: The width of the sidebar (default: "250px")
    :type sidebar_width: str
    :param height: The height of the layout (optional)
    :type height: str
    :param header_content: Optional header content to display at the top (optional)
    :type header_content: rx.Component | None
    :return: The page sidebar component
    :rtype: rx.Component
    """
    sidebar_drawer = _create_sidebar_drawer(sidebar_content, sidebar_width)

    return rx.box(
        # Desktop: Fixed sidebar
        _create_desktop_sidebar(sidebar_content, sidebar_width),
        # Mobile/Tablet: Header with hamburger (if header provided)
        _create_mobile_header(header_content, sidebar_drawer),
        # Content areas
        _create_desktop_content(content, header_content, sidebar_width),
        _create_mobile_content(content, header_content),
        width="100%",
        height=height,
        position="relative",
        class_name="page-layout-container",
        **kwargs,
    )
