from typing import Optional

import reflex as rx
from gws_reflex_base import (add_unauthorized_page, get_theme,
                             render_main_container)
from gws_reflex_main import ReflexMainState


class State(ReflexMainState):
    value = 0

    @rx.var
    async def get_resource_name(self) -> str:
        """Return the name of the resource."""

        # Secure the method to ensure it checks authentication
        # before accessing resources.
        if not self.check_authentication():
            return 'Unauthorized'
        resources = self.get_resources()
        return resources[0].name if resources else 'No resource'

    @rx.var
    def get_param_name(self) -> Optional[str]:
        """
        Get a parameter from the app configuration.
        This route is not secured, so it can be accessed without authentication.
        """
        return self.get_param('param_name', 'default_value')

    @rx.event
    def increment(self):
        """Increment the value."""
        self.value += 1


app = rx.App(
    theme=get_theme()
)


# Declare the page and init the main state
@rx.page(on_load=ReflexMainState.on_load)
def index():
    # Render the main container with the app content.
    # The content will be displayed once the state is initialized.
    # If the state is not initialized, a loading spinner will be shown.
    return render_main_container(rx.box(
        rx.heading("Reflex app", font_size="2em"),
        rx.text("Input resource name: " + State.get_resource_name),
        rx.text("Param name: " + State.get_param_name),
        rx.text("Value: " + State.value.to_string()),
        rx.button(
            "Click me",
            on_click=State.increment,
            style={"margin-top": "20px"}
        )
    ))


# Add the unauthorized page to the app.
# This page will be displayed if the user is not authenticated
add_unauthorized_page(app)
