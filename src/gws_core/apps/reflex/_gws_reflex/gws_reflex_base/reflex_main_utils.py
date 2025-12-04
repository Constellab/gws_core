import os

import reflex as rx

from .component.reflex_confirm_dialog_component import confirm_dialog
from .reflex_main_state_base import UNAUTHORIZED_ROUTE, ReflexMainStateBase


def main_component(*contents: rx.Component) -> rx.Component:
    """Wrapper to wait for the app to be initialized before showing the content.

    :param contents: The content components of the app.
    :type contents: rx.Component
    :return: The wrapped component.
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.cond(
            ReflexMainStateBase.main_component_initialized,
            rx.fragment(*contents),
            rx.center(
                rx.spinner(size="3"),
                height="100vh",
            ),
        ),
        confirm_dialog(),
        on_mount=ReflexMainStateBase.on_main_component_mount,
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
    """Get the theme of the app."""
    return rx.theme(
        accent_color="teal",
        appearance=os.environ.get("GWS_THEME", "light"),
    )
