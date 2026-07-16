import traceback

import reflex as rx

from .component.reflex_confirm_dialog_component import confirm_dialog
from .reflex_exception import ReflexAppException
from .reflex_main_state_base import (
    UNAUTHORIZED_ROUTE,
    ReflexMainStateBase,
    ReflexMainStateBaseFactory,
)

gws_theme_css_asset_path = rx.asset("gws_theme.css", shared=True)


def main_component(*contents: rx.Component, include_theme_css: bool = True) -> rx.Component:
    """Wrapper to wait for the app to be initialized before showing the content.

    :param contents: The content components of the app.
    :type contents: rx.Component
    :param include_theme_css: Whether to include the GWS theme CSS stylesheet. Defaults to True.
    :type include_theme_css: bool
    :return: The wrapped component.
    :rtype: rx.Component
    """
    theme_link = (
        [rx.el.link(rel="stylesheet", href=gws_theme_css_asset_path)] if include_theme_css else []
    )

    return rx.fragment(
        *theme_link,
        rx.cond(
            ReflexMainStateBaseFactory.get_main_state_class().main_component_initialized,
            rx.fragment(*contents),
            rx.center(
                rx.spinner(size="3"),
                height="100vh",
            ),
        ),
        confirm_dialog(),
        on_mount=ReflexMainStateBaseFactory.get_main_state_class().on_main_component_mount,
    )


def _unauthorized_page():
    return rx.box(
        rx.heading("Unauthorized", font_size="2em"),
        rx.text("You are not authorized to view this page."),
    )


def add_unauthorized_page(app: rx.App):
    """Add the unauthorized page to the app."""
    app.add_page(_unauthorized_page, route=UNAUTHORIZED_ROUTE, title="Unauthorized")


def get_theme():
    """Get the theme of the app.

    Configured at compile time via ``rx.plugins.RadixThemesPlugin(theme=get_theme())``,
    appended to ``config.plugins`` inside each app's ``rxconfig._init_reflex`` (after
    ``ReflexInit.init()`` makes this module importable). This replaces the
    ``App(theme=...)`` argument, deprecated in reflex 0.9.0 and removed in 1.0.
    """
    return rx.theme(
        gray_color="sage",
        # force light mode, because switch based on user is not yet supported
        appearance="light",
        radius="large",
    )


def default_gws_env_frontend_handler(exception: Exception) -> None:
    """Default frontend exception handler for GWS virtual environment apps.

    A virtual environment app cannot load ``gws_core``, so this handler logs the
    exception with the standard library instead of the GWS Logger.

    :param exception: The exception that occurred
    :type exception: Exception
    """
    traceback.print_exception(type(exception), exception, exception.__traceback__)


def default_gws_env_backend_handler(exception: Exception) -> rx.event.EventSpec | None:
    """Default backend exception handler for GWS virtual environment apps.

    Expected ``ReflexAppException`` errors are shown as a toast with their message.
    Unexpected errors are logged and shown as a generic message (or the full message
    in dev mode).

    :param exception: The exception that occurred
    :type exception: Exception
    :return: Event spec to show an error toast
    :rtype: rx.event.EventSpec | None
    """
    if isinstance(exception, ReflexAppException):
        if exception.show_as == "info":
            return rx.toast.info(exception.detail, position="top-center")
        return rx.toast.error(exception.detail, position="top-center")

    default_gws_env_frontend_handler(exception)

    if ReflexMainStateBase.is_dev_mode():
        # In dev mode, show the full error message
        return rx.toast.error(
            f"An unexpected error occurred: {str(exception)}", position="top-center"
        )

    # In production mode, show a generic error message
    return rx.toast.error("An unexpected error occurred.", position="top-center")
