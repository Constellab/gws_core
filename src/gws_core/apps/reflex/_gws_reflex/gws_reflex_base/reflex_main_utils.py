

import reflex as rx

from .reflex_main_state_base import UNAUTHORIZED_ROUTE, ReflexMainStateBase


def render_main_container(content: rx.Component) -> rx.Component:
    """
    Render the main container of the app. It wait for the state to be initialized
    and displays the content if initialized, otherwise shows a loading spinner.

    """
    return rx.box(
        rx.cond(
            ReflexMainStateBase.is_initialized,
            content,
            rx.center(
                rx.text("Loading app..."),
                rx.spinner(),
                align='center', justify='center',
                height='100vh', width='100vw',
            )
        )
    )


def _unauthorized_page():
    return rx.box(
        rx.heading("Unauthorized", font_size="2em"),
        rx.text("You are not authorized to view this page."),
    )


def add_unauthorized_page(app: rx.App):
    """Add the unauthorized page to the app."""
    app.add_page(_unauthorized_page, route=UNAUTHORIZED_ROUTE, title="Unauthorized")
