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
    return rx.vstack(
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
        display=rx.breakpoints(
            initial="none",  # Mobile: hidden
            sm="none",  # Tablet: hidden
            md="flex",  # Desktop: visible
        ),
    )


def _create_mobile_header_bar(
    sidebar_drawer: rx.Component,
) -> rx.Component:
    """Create the mobile/tablet header bar with just the hamburger menu.

    The actual header_content is rendered in the content wrapper to avoid
    duplicating components (which can cause issues with dialogs).
    """
    return rx.hstack(
        sidebar_drawer,
        width="100%",
        align_items="center",
        spacing="3",
        padding="1rem",
        position="fixed",
        top="0",
        left="0",
        z_index="10",
        background="var(--color-background)",
        display=rx.breakpoints(
            initial="flex",  # Mobile: visible
            sm="flex",  # Tablet: visible
            md="none",  # Desktop: hidden
        ),
    )


def _create_content_wrapper(
    content: rx.Component,
    header_content: rx.Component | None,
    sidebar_width: str,
    has_mobile_header_bar: bool,
) -> rx.Component:
    """Create a single content wrapper with responsive styling.

    The header_content is rendered only once here, avoiding duplicate
    components (which can cause issues with dialogs bound to state).
    """
    padding_top_mobile = "5rem" if has_mobile_header_bar else "1rem"

    return rx.box(
        # Header content rendered once with responsive styling
        rx.cond(
            header_content is not None,
            rx.box(
                header_content,
                width="100%",
                padding_bottom="1rem",
            ),
            rx.fragment(),
        ),
        # The actual content (rendered only once)
        content,
        # Responsive styling
        width=rx.breakpoints(
            initial="100%",  # Mobile: full width
            sm="100%",  # Tablet: full width
            md=f"calc(100% - {sidebar_width})",  # Desktop: account for sidebar
        ),
        margin_left=rx.breakpoints(
            initial="0",  # Mobile: no margin
            sm="0",  # Tablet: no margin
            md=sidebar_width,  # Desktop: offset by sidebar width
        ),
        padding=rx.breakpoints(
            initial=f"{padding_top_mobile} 1rem 2rem 1rem",  # Mobile: top, right, bottom, left
            sm=f"{padding_top_mobile} 1rem 2rem 1rem",  # Tablet: same as mobile
            md="2rem",  # Desktop: uniform padding
        ),
        height="100vh",
        overflow_y="auto",
        class_name="page-layout-content-wrapper",
        display="flex",
        flex_direction="column",
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

    Note: header_content is rendered only once in the content wrapper to avoid
    duplicating components (which can cause issues with dialogs bound to state).

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
    has_mobile_header_bar = header_content is not None

    return rx.box(
        # Desktop: Fixed sidebar
        _create_desktop_sidebar(sidebar_content, sidebar_width),
        # Mobile/Tablet: Header bar with hamburger menu only
        rx.cond(
            has_mobile_header_bar,
            _create_mobile_header_bar(sidebar_drawer),
            rx.fragment(),
        ),
        # Content wrapper (header_content rendered only once here)
        _create_content_wrapper(content, header_content, sidebar_width, has_mobile_header_bar),
        width="100%",
        height=height,
        position="relative",
        class_name="page-layout-container",
        **kwargs,
    )
