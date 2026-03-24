import reflex as rx
from gws_reflex_main import (
    main_component,
    menu_item_component,
    page_sidebar_component,
    register_gws_reflex_app,
    sidebar_menu_component,
)

from .pages import (
    dialog_page,
    doc_component_page,
    home_page,
    input_search_page,
    layout_page,
    resource_components_page,
    rich_text_page,
    user_components_page,
)

# Option 1: Simplest - create app with all GWS defaults
app = register_gws_reflex_app()


def _sidebar_content() -> rx.Component:
    """Create the sidebar content with navigation menu."""
    return sidebar_menu_component(
        title="Showcase",
        subtitle="Reflex Components",
        logo_src="/constellab-logo.svg",
        menu_items=[
            menu_item_component("home", "Home", "/"),
            menu_item_component("pen-line", "Rich Text", "/rich-text"),
            menu_item_component("user", "User Components", "/user-components"),
            menu_item_component("folder", "Resource Components", "/resource-components"),
            menu_item_component("message-square", "Dialogs", "/dialogs"),
            menu_item_component("layout-grid", "Layout Components", "/layout"),
            menu_item_component("file-text", "Doc Component", "/doc-component"),
            menu_item_component("search", "Input search", "/input-search"),
        ],
    )


def layout(content: rx.Component) -> rx.Component:
    """Create the main layout with sidebar and content."""
    return main_component(
        page_sidebar_component(
            sidebar_content=_sidebar_content(),
            content=content,
        )
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


@rx.page(route="/resource-components")
def resource_components():
    """Resource components demo page."""
    return layout(resource_components_page.resource_components_page())


@rx.page(route="/input-search")
def input_search():
    """Input search component demo page."""
    return layout(input_search_page.input_search_page())
