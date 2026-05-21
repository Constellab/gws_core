import reflex as rx
from gws_reflex_base import main_component
from gws_reflex_env_main import ReflexMainStateEnv, register_gws_reflex_env_app


class State(rx.State):
    value = 0

    @rx.var
    async def get_source_paths(self) -> list[str]:
        """Return the file paths of the input resources.

        This app runs in a virtual environment and cannot load gws_core.
        The env state exposes the input resources as file paths.
        """
        main_state = await self.get_state(ReflexMainStateEnv)
        return await main_state.get_source_paths()

    @rx.var
    async def get_param_name(self) -> str | None:
        """Get a parameter from the app configuration."""
        main_state = await self.get_state(ReflexMainStateEnv)
        return await main_state.get_param("param_name", "default_value")

    @rx.event
    def increment(self):
        """Increment the value."""
        self.value += 1


app = register_gws_reflex_env_app()


# Declare the page and init the main state
@rx.page()
def index():
    # Render the main container with the app content.
    # The content will be displayed once the state is initialized.
    # If the state is not initialized, a loading spinner will be shown.
    return main_component(
        rx.heading("Reflex app", font_size="2em"),
        rx.text("Input file paths: " + State.get_source_paths.to_string()),
        rx.text("Param name: " + State.get_param_name),
        rx.text(f"Value: {State.value}"),
        rx.button("Click me", on_click=State.increment, style={"margin-top": "20px"}),
    )
