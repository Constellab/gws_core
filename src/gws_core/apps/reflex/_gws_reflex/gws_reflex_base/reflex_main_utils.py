

import os

import reflex as rx

from .reflex_main_state_base_2 import UNAUTHORIZED_ROUTE, ReflexMainStateBase2


def render_main_container(content: rx.Component) -> rx.Component:
    """
    Render the main container of the app. It wait for the state to be initialized
    and displays the content if initialized, otherwise shows a loading spinner.

    """
    return rx.box(
        content,
        # This is not working with the new async load
        # This is not required anymore
        # rx.cond(
        #     ReflexMainStateBase2.is_initialized_computed,
        #     content,
        #     rx.center(
        #         rx.text("Loading app..."),
        #         rx.spinner(),
        #         align='center', justify='center',
        #         height='100vh', width='100vw',
        #     )
        # ),
        # on_mount=ReflexMainStateBase2.on_initialized
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
        accent_color='teal',
        appearance=os.environ.get("GWS_THEME", "light"),
    )
