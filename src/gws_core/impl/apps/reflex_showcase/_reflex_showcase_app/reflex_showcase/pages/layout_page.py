"""Layout components demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_base import loader_section, page_sidebar_component

from ..components import example_tabs, page_layout


class LayoutPageState(rx.State):
    """State for the layout page."""

    # Loader section state
    is_loading: bool = False

    @rx.event(background=True)  # type: ignore
    async def simulate_loading(self):
        """Simulate a loading operation."""
        async with self:
            self.is_loading = True

        # Simulate async operation (e.g., API call, data processing)
        import asyncio

        await asyncio.sleep(3)

        async with self:
            self.is_loading = False

        yield rx.toast.success("Loading complete!")


def layout_page() -> rx.Component:
    """Render the layout components demo page."""

    # Example 1: page_sidebar_component - Code only
    code1 = """from gws_reflex_base import page_sidebar_component
import reflex as rx

# Create sidebar content
def sidebar_content():
    return rx.vstack(
        rx.heading("Menu", size="5"),
        rx.link("Home", href="/"),
        rx.link("About", href="/about"),
        rx.link("Contact", href="/contact"),
        width="100%",
        spacing="2",
    )

# Create header content (optional)
def header_content():
    return rx.heading("My App", size="5")

# Create main content
def main_content():
    return rx.vstack(
        rx.heading("Welcome", size="7"),
        rx.text("This is your main content area."),
        align="start",
    )

# Use the page_sidebar_component in your page route
@rx.page(route="/")
def index():
    return page_sidebar_component(
        sidebar_content=sidebar_content(),
        content=main_content(),
        sidebar_width="250px",  # Default: "250px"
        header_content=header_content(),  # Optional
    )

# Responsive behavior:
# - Desktop (≥ md breakpoint): Fixed sidebar on left
# - Mobile/Tablet (< md): Hamburger menu with drawer sidebar"""

    # Example 2: loader_section
    example_loader = rx.vstack(
        rx.button(
            "Simulate Loading (3 seconds)",
            on_click=LayoutPageState.simulate_loading,
            disabled=LayoutPageState.is_loading,
        ),
        rx.box(
            loader_section(
                content=rx.vstack(
                    rx.heading("Content Loaded!", size="6", color="green"),
                    rx.text("This content is displayed when not loading."),
                    rx.text(
                        "Click the button above to see the loading spinner.",
                        color="gray",
                        size="2",
                    ),
                    spacing="3",
                    padding="2em",
                ),
                is_loading=LayoutPageState.is_loading,
            ),
            width="100%",
            min_height="200px",
            border="1px solid var(--gray-6)",
            border_radius="8px",
            padding="1em",
        ),
        align="start",
        width="100%",
        spacing="4",
    )

    code2 = '''from gws_reflex_base import loader_section
from gws_reflex_main import ReflexMainState
import reflex as rx

class MyState(rx.State):
    is_loading: bool = False

    @rx.event(background=True)
    async def load_data(self):
        """Load data asynchronously."""
        async with self:
            self.is_loading = True

        # Perform async operation (e.g., API call)
        import asyncio
        await asyncio.sleep(2)
        # data = await fetch_data_from_api()

        async with self:
            self.is_loading = False

        yield rx.toast.success("Data loaded!")

# Use loader_section to wrap your content
def my_component():
    return rx.vstack(
        rx.button(
            "Load Data",
            on_click=MyState.load_data,
        ),
        loader_section(
            content=rx.vstack(
                rx.heading("My Data"),
                rx.text("Content goes here..."),
            ),
            is_loading=MyState.is_loading,
        ),
    )

# The loader_section will:
# - Show a centered spinner when is_loading=True
# - Show the content when is_loading=False'''

    return page_layout(
        "Layout Components",
        "This page demonstrates layout components for building responsive applications "
        "with sidebars and loading states.",
        # page_sidebar_component example (code only)
        example_tabs(
            example_component=rx.box(
                rx.vstack(
                    rx.heading("page_sidebar_component", size="6", margin_bottom="0.5em"),
                    rx.text(
                        "A responsive layout component with a sidebar that automatically adapts to screen size:",
                        margin_bottom="1em",
                    ),
                    rx.text("• Desktop (≥ md breakpoint): Fixed sidebar on the left", size="3"),
                    rx.text("• Mobile/Tablet (< md): Hamburger menu with drawer sidebar", size="3"),
                    rx.text(
                        "• Optional header content displayed at top",
                        size="3",
                        margin_bottom="1em",
                    ),
                    rx.text(
                        "See the code example for implementation details.",
                        color="gray",
                        size="2",
                    ),
                    align="start",
                    padding="2em",
                ),
                border="1px solid var(--gray-6)",
                border_radius="8px",
            ),
            code=code1,
            title="page_sidebar_component",
            description="A responsive layout with a sidebar that adapts to screen size. "
            "Desktop shows a fixed sidebar, mobile/tablet shows a hamburger menu with drawer.",
            func=page_sidebar_component,
        ),
        # loader_section example
        example_tabs(
            example_component=example_loader,
            code=code2,
            title="loader_section",
            description="A wrapper component that displays a loading spinner while content is being loaded.",
            func=loader_section,
        ),
    )
