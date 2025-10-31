import reflex as rx
from gws_reflex_main import add_unauthorized_page, get_theme

from .pages import doc_component_page, home_page, rich_text_page

app = rx.App(
    theme=get_theme()
)


def sidebar_link(text: str, url: str, icon: str) -> rx.Component:
    """Create a sidebar navigation link."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20),
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
            rx.heading("Reflex Showcase", size="6", margin_bottom="1em"),
            rx.divider(margin_bottom="1em"),

            # Navigation links
            sidebar_link("Home", "/", "home"),
            sidebar_link("Rich Text", "/rich-text", "pencil"),
            sidebar_link("Doc Component", "/doc-component", "file-text"),

            width="100%",
            spacing="2",
        ),
        width="250px",
        padding="1.5em",
        bg=rx.color("gray", 2),
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


@rx.page(route="/doc-component")
def doc_component():
    """Doc component demo page."""
    return layout(doc_component_page.doc_component_page())


# Add the unauthorized page to the app.
# This page will be displayed if the user is not authenticated
add_unauthorized_page(app)
