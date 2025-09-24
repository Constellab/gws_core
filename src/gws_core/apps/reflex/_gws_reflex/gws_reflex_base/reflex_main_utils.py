

import os

import reflex as rx

from .reflex_main_state_base import UNAUTHORIZED_ROUTE


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
        accent_color='teal',
        appearance=os.environ.get("GWS_THEME", "light"),
    )
