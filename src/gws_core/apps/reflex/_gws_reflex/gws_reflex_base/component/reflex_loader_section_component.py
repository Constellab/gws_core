import reflex as rx


def loader_section(content: rx.Component, is_loading: bool) -> rx.Component:
    """Loader section wrapper for loading state.

    Wraps the given content component with a loading spinner
    that displays when is_loading is True.

    Args:
        content (rx.Component): The main content to display
        is_loading (bool): Whether to show the loading spinner

    Returns:
        rx.Component: Component with loading spinner overlay
    """
    return rx.cond(
        is_loading,
        rx.center(
            rx.spinner(),
            width="100%",
            height="100%",
        ),
        content,
    )
