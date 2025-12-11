import reflex as rx
from gws_reflex_main import register_gws_reflex_app

from .pages import (
    dialog_page,
    doc_component_page,
    home_page,
    layout_page,
    rich_text_page,
    user_components_page,
)

# Option 1: Simplest - create app with all GWS defaults
app = register_gws_reflex_app()


def sidebar_link(text: str, url: str, emoji: str) -> rx.Component:
    """Create a sidebar navigation link."""
    return rx.link(
        rx.hstack(
            rx.text(emoji, size="5"),
            rx.text(text, size="3"),
            width="100%",
            padding_y="0.5em",
            padding_x="1em",
            border_radius="0.5em",
            _hover={
                "bg": rx.color("accent", 3),
            },
        ),
        href=url,
        underline="none",
        width="100%",
    )


def sidebar() -> rx.Component:
    """Create the sidebar with navigation links."""
    return rx.box(
        rx.vstack(
            # Navigation links
            sidebar_link("Home", "/", "🏠"),
            sidebar_link("Rich Text", "/rich-text", "✏️"),
            sidebar_link("User Components", "/user-components", "👤"),
            sidebar_link("Dialogs", "/dialogs", "💬"),
            sidebar_link("Layout Components", "/layout", "📐"),
            sidebar_link("Doc Component", "/doc-component", "📄"),
            width="100%",
            spacing="2",
        ),
        width="250px",
        padding="1.5em",
        bg="var(--accent-2)",
        height="100vh",
        position="fixed",
        left="0",
        top="0",
    )


def layout(content: rx.Component) -> rx.Component:
    """Create the main layout with sidebar and content."""
    return rx.box(
        sidebar(),
        rx.box(
            content,
            margin_left="250px",
            width="calc(100% - 250px)",
            min_height="100vh",
        ),
    )


@rx.page(route="/")
def index():
    """Home page."""
    return layout(home_page.home_page())


@rx.page(route="/rich-text")
def rich_text():
    """Rich text component demo page."""
    return layout(rich_text_page.rich_text_page())


@rx.page(route="/user-components")
def user_components():
    """User components demo page."""
    return layout(user_components_page.user_components_page())


@rx.page(route="/dialogs")
def dialogs():
    """Dialog components demo page."""
    return layout(dialog_page.dialog_page())


@rx.page(route="/layout")
def layout_components():
    """Layout components demo page."""
    return layout(layout_page.layout_page())


@rx.page(route="/doc-component")
def doc_component():
    """Doc component demo page."""
    return layout(doc_component_page.doc_component_page())
