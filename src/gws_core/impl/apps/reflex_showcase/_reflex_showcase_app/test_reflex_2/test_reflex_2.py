import reflex as rx

from gws_core.apps.reflex._reflex_app_utils.main_reflex import \
    add_unauthorized_page
from gws_core.apps.reflex._reflex_app_utils.main_reflex_not_env import \
    ReflexAuthenticationStateNotEnv


class State(ReflexAuthenticationStateNotEnv):
    variable: str = ''

    @rx.var
    def get_resource_name(self) -> str:
        """Return the name of the resource."""
        return self.resources[0].name if self.resources else 'No resource'

    @rx.var
    def get_resource_name_2(self) -> str:
        """Return the name of the resource."""
        resources = self.get_resources('Get')
        return resources[0].name if resources else 'No resource'


def _app_content():
    return rx.box(
        rx.heading("Bonjour les potes " + State.variable, font_size="2em"),
        rx.text("This is a test Reflex app without env."),
        rx.text("Resource name: " + State.get_resource_name),
        rx.text("Resource name 2: " + State.get_resource_name_2),
        rx.button(
            "Click me",
            on_click=State.on_load,
            style={"margin-top": "20px"}
        ),
    )


app = rx.App()


# Use the decorator only here, not elsewhere
@rx.page(on_load=State.on_load)
def index():
    return _app_content()


add_unauthorized_page(app)
