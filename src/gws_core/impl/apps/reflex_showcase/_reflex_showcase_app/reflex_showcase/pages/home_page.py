"""Home page for the Reflex showcase app."""

from typing import Optional

import reflex as rx
from gws_reflex_main import ReflexMainState

from gws_core.core.utils.logger import Logger
from gws_core.user.current_user_service import CurrentUserService


class HomePageState(ReflexMainState):
    """State for the home page."""

    value: int = 0

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

        with await self.authenticate_user() as user:
            user2 = CurrentUserService.get_current_user()
            if user2:
                Logger.info(f"Current user in load_current_user: {user2.email}")
            else:
                Logger.info("No current user in load_current_user")


def home_page() -> rx.Component:
    """Render the home page with main content."""
    return rx.box(
        rx.heading("Reflex Showcase App", size="9", margin_bottom="1em"),

        rx.text(
            "Welcome to the Reflex Showcase App! This application demonstrates "
            "various features and components available in Reflex applications.",
            size="4",
            margin_bottom="2em",
        ),

        rx.divider(margin_bottom="2em"),

        rx.heading("Features Demo", size="7", margin_bottom="1em"),

        # State management demo
        rx.card(
            rx.heading("State Management", size="5", margin_bottom="0.5em"),
            rx.text("Current value: " + HomePageState.value.to_string(), margin_bottom="1em"),
            rx.hstack(
                rx.button(
                    "Increment",
                    on_click=HomePageState.increment,
                ),
                spacing="3",
            ),
            margin_bottom="1em",
        ),

        # Resource access demo
        rx.card(
            rx.heading("Resource Access", size="5", margin_bottom="0.5em"),
            rx.text("Input resource name: " + HomePageState.get_resource_name),
            rx.text("Parameter value: " + HomePageState.get_param_name),
            margin_bottom="1em",
        ),

        # Authentication demo
        rx.card(
            rx.heading("Authentication", size="5", margin_bottom="0.5em"),
            rx.text("Current user: " + HomePageState.get_current_user_name),
            rx.text("Current user (alt method): " + HomePageState.get_current_user_name2),
            rx.button(
                "Load current user",
                on_click=HomePageState.load_current_user,
            ),
            margin_bottom="1em",
        ),

        rx.divider(margin_top="2em", margin_bottom="1em"),

        rx.text(
            "Use the sidebar to navigate to different pages and explore more components.",
            size="3",
            color="gray",
        ),

        padding="2em",
    )
