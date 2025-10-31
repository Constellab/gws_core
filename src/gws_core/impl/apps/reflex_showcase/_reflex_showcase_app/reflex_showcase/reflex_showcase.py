from typing import Optional

import reflex as rx
from gws_core.core.utils.logger import Logger
from gws_core.user.current_user_service import CurrentUserService
from gws_reflex_main import ReflexMainState, add_unauthorized_page, get_theme


class State(ReflexMainState):
    value = 0

    @rx.var
    async def get_resource_name(self) -> str:
        """Return the name of the resource."""

        # Secure the method to ensure it checks authentication
        # before accessing resources.
        if not await self.check_authentication():
            return 'Unauthorized'
        resources = await self.get_resources()
        return resources[0].name if resources else 'No resource'

    @rx.var
    async def get_param_name(self) -> Optional[str]:
        """
        Get a parameter from the app configuration.
        This route is not secured, so it can be accessed without authentication.
        """
        return await self.get_param('param_name', 'default_value')

    @rx.event
    def increment(self):
        """Increment the value."""
        self.value += 1
        Logger.info(f"Value incremented to {self.value}")

    @rx.var
    async def get_current_user_name(self) -> Optional[str]:
        """Return the name of the current user, or None if no user is set."""
        user = await self.get_current_user()
        return user.email if user else None

    @rx.var(cache=False)
    async def get_current_user_name2(self) -> Optional[str]:
        """Return the name of the current user, or None if no user is set."""
        user = CurrentUserService.get_current_user()
        return user.email if user else None

    @rx.event
    async def load_current_user(self):
        """Load the current user."""
        user = CurrentUserService.get_current_user()
        if user:
            Logger.info(f"Current user in load_current_user: {user.email}")
        else:
            Logger.info("No current user in load_current_user")

        # # authenticate_user = await self.authenticate_user()
        with await self.authenticate_user() as user:
            user2 = CurrentUserService.get_current_user()
            if user2:
                Logger.info(f"Current user in load_current_user: {user2.email}")
            else:
                Logger.info("No current user in load_current_user")


app = rx.App(
    theme=get_theme()
)


# Declare the page and init the main state
@rx.page()
def index():
    # Render the main container with the app content.
    # The content will be displayed once the state is initialized.
    # If the state is not initialized, a loading spinner will be shown.
    return rx.box(
        rx.heading("Reflex app", font_size="2em"),
        rx.text("Input resource name: " + State.get_resource_name),
        rx.text("Param name: " + State.get_param_name),
        rx.text(f"Value: {State.value}"),
        rx.text("Current user: " + State.get_current_user_name),
        rx.text("Current user2: " + State.get_current_user_name2),
        rx.button(
            "Click me",
            on_click=State.increment,
            style={"margin-top": "20px"}
        ),
        rx.button(
            "Load current user",
            on_click=State.load_current_user,
            style={"margin-top": "20px", "margin-left": "10px"}
        ),
    )


# Add the unauthorized page to the app.
# This page will be displayed if the user is not authenticated
add_unauthorized_page(app)
