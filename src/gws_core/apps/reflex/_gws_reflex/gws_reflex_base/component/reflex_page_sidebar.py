import reflex as rx


class SidebarState(rx.State):
    """State for managing sidebar visibility."""

    show_left_sidebar: bool = False
    show_right_sidebar: bool = False

    def toggle_left_sidebar(self):
        """Toggle the visibility of the left sidebar."""
        self.show_left_sidebar = not self.show_left_sidebar

    def set_left_sidebar_open(self, is_open: bool):
        """Set the left sidebar visibility to a specific value."""
        self.show_left_sidebar = is_open

    def toggle_right_sidebar(self):
        """Toggle the visibility of the right sidebar."""
        self.show_right_sidebar = not self.show_right_sidebar


def left_sidebar_open_button() -> rx.Component:
    """Create a button to open the left sidebar on mobile/tablet.

    Always visible on small screens (the sidebar is a drawer overlay there).
    Hidden on desktop where the sidebar is always visible as a fixed panel.

    :return: The open button component
    :rtype: rx.Component
    """
    return rx.box(
        rx.tooltip(
            rx.icon_button(
                rx.icon("menu", size=20),
                on_click=SidebarState.toggle_left_sidebar,
                variant="soft",
                size="2",
                cursor="pointer",
            ),
            content="Show sidebar",
        ),
        display=rx.breakpoints(
            initial="block",  # Mobile: visible
            sm="block",  # Tablet: visible
            md="none",  # Desktop: hidden (sidebar always visible)
        ),
        class_name="left-sidebar-open-button",
    )


def right_sidebar_open_button() -> rx.Component:
    """Create a button to open the right sidebar when it is closed.

    Visible on small/medium screens when the right sidebar is hidden.
    Hidden on xl+ where the right sidebar is always visible.

    :return: The open button component (conditionally rendered)
    :rtype: rx.Component
    """
    return rx.box(
        rx.cond(
            ~SidebarState.show_right_sidebar,
            rx.tooltip(
                rx.icon_button(
                    rx.icon("panel-right-open", size=20),
                    on_click=SidebarState.toggle_right_sidebar,
                    variant="soft",
                    size="2",
                    cursor="pointer",
                ),
                content="Show detail panel",
            ),
        ),
        display=rx.breakpoints(
            initial="block",
            xl="none",
        ),
    )


def right_sidebar_close_button() -> rx.Component:
    """Create a button to close the right sidebar when it is open.

    Visible on small/medium screens where the right sidebar is an overlay.
    Hidden on xl+ where the right sidebar is always visible.

    :return: The close button component
    :rtype: rx.Component
    """
    return rx.box(
        rx.icon_button(
            rx.icon("panel-right-close", size=20),
            on_click=SidebarState.toggle_right_sidebar,
            variant="soft",
            size="2",
            cursor="pointer",
        ),
        display=rx.breakpoints(
            initial="block",
            xl="none",
        ),
    )


def _create_sidebar_drawer(
    sidebar_content: rx.Component,
    sidebar_width: str,
) -> rx.Component:
    """Create the drawer component for mobile/tablet sidebar.

    Controlled by SidebarState.show_left_sidebar so the left_sidebar_open_button
    can open it via state toggle.
    """
    return rx.drawer.root(
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
                display="flex",
                flex_direction="column",
            ),
        ),
        direction="left",
        open=SidebarState.show_left_sidebar,
        on_open_change=SidebarState.set_left_sidebar_open,
    )


def _create_desktop_sidebar(
    sidebar_content: rx.Component,
    sidebar_width: str,
) -> rx.Component:
    """Create the fixed sidebar for desktop.

    Always visible on desktop (md+), hidden on mobile/tablet.
    """
    return rx.vstack(
        sidebar_content,
        width=sidebar_width,
        min_width=sidebar_width,
        padding="1rem",
        background="white",
        border_right="1px solid var(--gray-4)",
        align_items="start",
        height="100vh",
        position="fixed",
        left="0",
        top="0",
        z_index="5",
        display=rx.breakpoints(
            initial="none",  # Mobile: hidden
            sm="none",  # Tablet: hidden
            md="flex",  # Desktop: always visible
        ),
    )


def _create_mobile_menu_button(
    sidebar_drawer: rx.Component,
) -> rx.Component:
    """Create the mobile hamburger menu button and drawer.

    Only visible on mobile/tablet. Hidden on desktop where the sidebar is
    always visible as a fixed panel.
    """
    return rx.box(
        rx.tooltip(
            rx.icon_button(
                rx.icon("menu", size=20),
                on_click=SidebarState.toggle_left_sidebar,
                variant="soft",
                size="2",
                cursor="pointer",
            ),
            content="Show sidebar",
        ),
        sidebar_drawer,
        display=rx.breakpoints(
            initial="block",  # Mobile: visible
            sm="block",  # Tablet: visible
            md="none",  # Desktop: hidden
        ),
    )


def _create_right_sidebar(
    right_sidebar_content: rx.Component,
    right_sidebar_width: str,
) -> rx.Component:
    """Create the desktop right sidebar.

    :param right_sidebar_content: The content to display in the right sidebar
    :type right_sidebar_content: rx.Component
    :param right_sidebar_width: The width of the right sidebar
    :type right_sidebar_width: str
    :return: The right sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.vstack(
            right_sidebar_content,
            padding="1.5rem",
            align_items="start",
            width="100%",
            height="100%",
            overflow_y="auto",
        ),
        width=right_sidebar_width,
        min_width=right_sidebar_width,
        height="100%",
        background="white",
        border_left="1px solid var(--gray-4)",
        display=rx.breakpoints(initial="none", xl="flex"),
    )


def _create_right_sidebar_mobile_overlay(
    right_sidebar_content: rx.Component,
    right_sidebar_width: str,
) -> rx.Component:
    """Create the mobile right sidebar overlay (slides in from the right).

    :param right_sidebar_content: The content to display in the right sidebar
    :type right_sidebar_content: rx.Component
    :param right_sidebar_width: The width of the right sidebar
    :type right_sidebar_width: str
    :return: The mobile right sidebar overlay component
    :rtype: rx.Component
    """
    return rx.box(
        # Backdrop overlay
        rx.box(
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            background="rgba(0, 0, 0, 0.4)",
            z_index="998",
            on_click=SidebarState.toggle_right_sidebar,
        ),
        # Sidebar panel
        rx.box(
            rx.vstack(
                right_sidebar_content,
                padding="1.5rem",
                align_items="start",
                width="100%",
                height="100%",
                overflow_y="auto",
            ),
            position="fixed",
            top="0",
            right="0",
            bottom="0",
            width=f"min({right_sidebar_width}, 90vw)",
            background="var(--color-background)",
            box_shadow="-4px 0 20px rgba(0, 0, 0, 0.15)",
            z_index="999",
            padding="1rem",
            display="flex",
            flex_direction="column",
            overflow_y="auto",
        ),
        display=rx.breakpoints(initial="block", xl="none"),
    )


def _create_content_wrapper(
    content: rx.Component,
    header_content: rx.Component | None,
    sidebar_width: str,
    mobile_menu_button: rx.Component | None = None,
    max_content_width: str | None = None,
) -> rx.Component:
    """Create a single content wrapper with responsive styling.

    On mobile, the hamburger menu button is placed on the left of the header row.
    On desktop, the sidebar is always visible so the button is hidden.

    :param max_content_width: Optional max width to constrain the header and content area
    :type max_content_width: str | None
    """
    inner_children = [
        # Header row: mobile menu button + header content + right sidebar toggle
        rx.cond(
            header_content is not None,
            rx.hstack(
                mobile_menu_button if mobile_menu_button is not None else rx.fragment(),
                rx.box(header_content, flex=1),
                right_sidebar_open_button(),
                width="100%",
                align_items="center",
                class_name="page-header-content",
            ),
            rx.fragment(),
        ),
        # The actual content (rendered only once)
        content,
    ]

    # If max_content_width is set, wrap header + content in a constraining box
    if max_content_width:
        inner = rx.vstack(
            *inner_children,
            max_width=max_content_width,
            width="100%",
            flex="1",
            min_height="0",
        )
    else:
        inner = rx.fragment(*inner_children)

    return rx.box(
        inner,
        # Responsive styling — desktop sidebar is always visible
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
        padding="2em",
        height="100vh",
        overflow_y="auto",
        class_name="page-layout-content-wrapper",
        display="flex",
        flex_direction="column",
        flex="1",
    )


def page_sidebar_component(
    sidebar_content: rx.Component,
    content: rx.Component,
    sidebar_width: str = "250px",
    height: str | None = None,
    header_content: rx.Component | None = None,
    right_sidebar_content: rx.Component | None = None,
    right_sidebar_width: str = "450px",
    max_content_width: str | None = None,
    **kwargs,
) -> rx.Component:
    """Create a generic page layout with responsive sidebar and main content area.

    This component provides a layout with:
    - Desktop: Fixed sidebar on left, content on right with optional header on top
    - Mobile/Tablet: Hamburger menu with drawer sidebar, optional header bar on top
    - Optional right sidebar: Full-height panel on the right with close/open toggle

    Note: header_content is rendered only once in the content wrapper to avoid
    duplicating components (which can cause issues with dialogs bound to state).

    :param sidebar_content: The content to display in the left sidebar
    :type sidebar_content: rx.Component
    :param content: The main content to display
    :type content: rx.Component
    :param sidebar_width: The width of the left sidebar (default: "250px")
    :type sidebar_width: str
    :param height: The height of the layout (optional)
    :type height: str
    :param header_content: Optional header content to display at the top (optional)
    :type header_content: rx.Component | None
    :param right_sidebar_content: Optional content for a right sidebar panel (optional)
    :type right_sidebar_content: rx.Component | None
    :param right_sidebar_width: The width of the right sidebar (default: "450px")
    :type right_sidebar_width: str
    :param max_content_width: Optional max width to constrain the header and content area (optional)
    :type max_content_width: str | None
    :return: The page sidebar component
    :rtype: rx.Component
    """
    sidebar_drawer = _create_sidebar_drawer(sidebar_content, sidebar_width)
    mobile_menu_button = _create_mobile_menu_button(sidebar_drawer)
    has_right_sidebar = right_sidebar_content is not None

    return rx.box(
        # Desktop: Fixed left sidebar (always visible on md+)
        _create_desktop_sidebar(sidebar_content, sidebar_width),
        # Content + optional right sidebar in a horizontal layout
        rx.hstack(
            # Content wrapper (mobile menu button inline with header)
            _create_content_wrapper(
                content, header_content, sidebar_width, mobile_menu_button, max_content_width
            ),
            # Desktop right sidebar (always visible on xl+ via CSS, hidden below)
            rx.cond(
                has_right_sidebar,
                _create_right_sidebar(right_sidebar_content, right_sidebar_width),
                rx.fragment(),
            ),
            width="100%",
            height="100vh",
            spacing="0",
            align_items="stretch",
        ),
        # Mobile right sidebar overlay
        rx.cond(
            has_right_sidebar,
            rx.cond(
                SidebarState.show_right_sidebar,
                _create_right_sidebar_mobile_overlay(right_sidebar_content, right_sidebar_width),
            ),
            rx.fragment(),
        ),
        width="100%",
        height=height,
        position="relative",
        class_name="page-layout-container",
        **kwargs,
    )
