"""Home page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main import ReflexMainState

from ..components import example_tabs, page_layout


class HomePageState(rx.State):
    """State for the home page."""

    value: int = 0

    @rx.var
    async def get_resource_name(self) -> str:
        """Return the name of the resource."""
        # Secure the method to ensure it checks authentication
        # before accessing resources.
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            return "Unauthorized"
        resources = await main_state.get_resources()
        return resources[0].name if resources else "No resource"

    @rx.var
    async def get_param_name(self) -> str | None:
        """
        Get a parameter from the app configuration.
        This route is not secured, so it can be accessed without authentication.
        """
        main_state = await self.get_state(ReflexMainState)
        return await main_state.get_param("param_name", "default_value")

    @rx.var
    async def get_current_user_name(self) -> str | None:
        """Return the name of the current user, or None if no user is set."""
        main_state = await self.get_state(ReflexMainState)
        user = await main_state.get_current_user()
        return user.email if user else None


def home_page() -> rx.Component:
    """Render the home page with main content."""

    # Resource access example
    resource_access_example = rx.box(
        rx.text("Input resource name: " + HomePageState.get_resource_name),
        rx.text("Parameter value: " + HomePageState.get_param_name),
    )

    resource_access_code = """import reflex as rx
from gws_reflex_main import ReflexMainState

class HomePageState(rx.State):

    @rx.var
    async def get_resource_name(self) -> str:
        # Secure method - checks authentication before accessing resources
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            return 'Unauthorized'
        resources = await main_state.get_resources()
        return resources[0].name if resources else 'No resource'

    @rx.var
    async def get_param_name(self) -> str:
        # Get a parameter from the app configuration
        # This route is not secured by default
        main_state = await self.get_state(ReflexMainState)
        return await main_state.get_param('param_name', 'default_value')

# Use in component
rx.box(
    rx.text("Input resource name: " + HomePageState.get_resource_name),
    rx.text("Parameter value: " + HomePageState.get_param_name),
)"""

    # Authentication example
    authentication_example = rx.box(
        rx.text("Current user: " + HomePageState.get_current_user_name, margin_bottom="0.5em"),
    )

    authentication_code = """import reflex as rx
from gws_reflex_main import ReflexMainState

class HomePageState(rx.State):

    @rx.var
    async def get_current_user_name(self) -> str:
        main_state = await self.get_state(ReflexMainState)
        user = await main_state.get_current_user()
        return user.email if user else None

# Use in component
rx.box(
    rx.text("Current user: " + HomePageState.get_current_user_name),
)"""

    return page_layout(
        "Reflex Showcase App",
        "Welcome to the Reflex Showcase App! This application demonstrates "
        "various features and components available in Reflex applications.",
        # Resource access demo
        example_tabs(
            example_component=resource_access_example,
            code=resource_access_code,
            title="Resource Access",
            description="Shows how to access input resources and configuration parameters from the Constellab platform.",
        ),
        # Authentication demo
        example_tabs(
            example_component=authentication_example,
            code=authentication_code,
            title="Authentication",
            description="Demonstrates how to access the current authenticated user in your Reflex application.",
        ),
        rx.divider(margin_top="2em", margin_bottom="1em"),
        rx.text(
            "Use the sidebar to navigate to different pages and explore more components.",
            size="3",
            color="gray",
        ),
    )
